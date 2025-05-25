import subprocess
import time
import json
import logging
import os
import itertools
import pandas as pd
import sys
import socket

SERVER_SCRIPT = "file_server.py"
CLIENT_SCRIPT = "stress_client.py"
SERVER_LOG_FILE = "server_log.log"
CLIENT_LOG_FILE = "client_stress_test.log"
SERVER_IP = "172.16.16.101"
SERVER_PORT = 6667
UPLOADED_FILES_DIR = "files/"

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("orchestrator_log.log"), 
                        logging.StreamHandler(sys.stdout)             
                    ])

OPERATIONS = ['download', 'upload']
VOLUMES_MB = [10, 50, 100]
CLIENT_NUM_WORKERS = [1, 5, 50]
CLIENT_POOL_TYPES = ['thread', 'process']
SERVER_POOL_TYPES = ['thread', 'process']
SERVER_NUM_WORKERS = [1, 5, 50]

# Testing debugging
# OPERATIONS = ['download']
# VOLUMES_MB = [10]
# CLIENT_NUM_WORKERS = [1]
# CLIENT_POOL_TYPES = ['thread']
# SERVER_POOL_TYPES = ['thread']
# SERVER_NUM_WORKERS = [1]

server_process = None

def start_server(pool_type, max_workers, port):
    global server_process
    logging.info(f"Memulai server: {SERVER_SCRIPT} --pool_type {pool_type} --max_workers {max_workers} --port {port}")
    try:
        server_process = subprocess.Popen(
            ['python', SERVER_SCRIPT, 
             '--pool_type', pool_type, 
             '--max_workers', str(max_workers), 
             '--port', str(port)],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            preexec_fn=os.setsid 
        )
        
        if not wait_for_server_to_listen(port, ip=SERVER_IP, retries=10, delay=1): 
             logging.error(f"Server gagal mendengarkan pada port {port} setelah beberapa percobaan.")
             stop_server()
             return False
        
        logging.info(f"Server dimulai dengan PID: {server_process.pid} dan terdeteksi mendengarkan.")
        return True
    except Exception as e:
        logging.error(f"Gagal memulai server: {e}")
        return False

def is_server_listening_once(port, ip, timeout=0.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(timeout)
        s.connect((ip, port))
        return True
    except (socket.error, ConnectionRefusedError):
        return False
    finally:
        s.close()

def wait_for_server_to_listen(port, ip, retries=5, delay=1):
    for i in range(retries):
        if is_server_listening_once(port, ip):
            return True
        logging.info(f"Percobaan {i+1}/{retries}: Server belum mendengarkan pada {ip}:{port}. Menunggu {delay} detik...")
        time.sleep(delay)
    return False

def stop_server():
    global server_process
    if server_process:
        logging.info(f"Menghentikan server dengan PID: {server_process.pid}...")
        try:
            os.killpg(os.getpgid(server_process.pid), 15) 
            server_process.wait(timeout=10)
            logging.info("Server berhasil dihentikan.")
        except subprocess.TimeoutExpired:
            logging.warning("Server tidak berhenti dalam waktu yang ditentukan, mematikan paksa...")
            os.killpg(os.getpgid(server_process.pid), 9) 
            server_process.wait()
            logging.info("Server dimatikan paksa.")
        except Exception as e:
            logging.error(f"Error saat menghentikan server: {e}")
        server_process = None

def run_client_stress_test(operation, volume_mb, client_pool_type, num_client_workers):
    logging.info(f"Menjalankan client: {CLIENT_SCRIPT} --operation {operation} --volume {volume_mb} --client_pool_type {client_pool_type} --num_client_workers {num_client_workers}")
    try:
        result = subprocess.run(
            ['python', CLIENT_SCRIPT, 
             '--operation', operation, 
             '--volume', str(volume_mb), 
             '--client_pool_type', client_pool_type, 
             '--num_client_workers', str(num_client_workers)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logging.error(f"Client script exited with error code {result.returncode}. Stderr: {result.stderr}")
            return {"error": "Client script failed", "details": result.stderr}

        json_output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith('{') and line.strip().endswith('}')]
        
        if not json_output_lines:
            logging.error(f"No JSON output found from client. Full stdout: {result.stdout}")
            return {"error": "No JSON output", "details": result.stdout}

        client_metrics = json.loads(json_output_lines[-1])
        return client_metrics

    except json.JSONDecodeError as e:
        logging.error(f"Gagal mem-parse JSON dari client: {e}. Raw stdout: {result.stdout[:500]}...")
        return {"error": "JSON parse error", "details": str(e)}
    except Exception as e:
        logging.error(f"Error saat menjalankan client stress test: {e}")
        return {"error": "Subprocess error", "details": str(e)}

def cleanup_uploaded_files():
    logging.info("Melakukan pembersihan file yang diupload di server...")
    try:
        files_to_delete = []
        for size_mb in VOLUMES_MB: 
            uploaded_dir_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), UPLOADED_FILES_DIR)
            
            if not os.path.exists(uploaded_dir_full_path):
                logging.warning(f"Direktori upload {uploaded_dir_full_path} tidak ditemukan, tidak ada yang dihapus.")
                return

            files_to_delete.extend(
                [f for f in os.listdir(uploaded_dir_full_path) 
                 if f.startswith(f"uploaded_dummy_{size_mb}MB_") and f.endswith(".txt")]
            )
        
        for filename in files_to_delete:
            filepath = os.path.join(uploaded_dir_full_path, filename)
            os.remove(filepath)
        logging.info(f"Berhasil menghapus {len(files_to_delete)} file yang diupload.")
    except Exception as e:
        logging.error(f"Error saat membersihkan file yang diupload: {e}")

def clear_server_log():
    logging.info(f"Membersihkan log server: {SERVER_LOG_FILE}")
    try:
        full_server_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SERVER_LOG_FILE)
        if os.path.exists(full_server_log_path):
            with open(full_server_log_path, 'w') as f:
                f.truncate(0)
    except Exception as e:
        logging.error(f"Gagal membersihkan log server: {e}")

def get_server_worker_metrics_from_log():
    successful_server_workers = 0
    failed_server_workers = 0
    
    try:
        full_server_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SERVER_LOG_FILE)
        with open(full_server_log_path, 'r') as f:
            log_content = f.read()
        
        successful_server_workers = log_content.count("selesai menangani koneksi")
        failed_server_workers = log_content.count("Error saat menangani client")

    except FileNotFoundError:
        logging.warning(f"Server log file {SERVER_LOG_FILE} tidak ditemukan saat dibaca. Server mungkin gagal menulis log.")
    except Exception as e:
        logging.error(f"Error saat membaca log server: {e}")
        
    return successful_server_workers, failed_server_workers


def main():
    all_test_results = []
    test_number = 1

    logging.info("Memulai seluruh rangkaian stress test...")
    
    cleanup_uploaded_files() 

    total_combinations = len(OPERATIONS) * len(VOLUMES_MB) * \
                         len(CLIENT_NUM_WORKERS) * len(CLIENT_POOL_TYPES) * \
                         len(SERVER_POOL_TYPES) * len(SERVER_NUM_WORKERS)

    for op, vol, client_num_workers, client_pool_type, server_pool_type, server_num_workers in itertools.product(
        OPERATIONS, 
        VOLUMES_MB, 
        CLIENT_NUM_WORKERS, 
        CLIENT_POOL_TYPES,
        SERVER_POOL_TYPES, 
        SERVER_NUM_WORKERS
    ):
        logging.info(f"\n--- Uji Kombinasi {test_number}/{total_combinations} ---")
        logging.info(f"Operasi: {op}, Volume: {vol}MB, Client Workers: {client_num_workers}, Client Pool Type: {client_pool_type}, Server Pool Type: {server_pool_type}, Server Workers: {server_num_workers}")

        clear_server_log()

        if not start_server(server_pool_type, server_num_workers, SERVER_PORT): 
            logging.error(f"Melewati kombinasi {test_number} karena server gagal dimulai.")
            all_test_results.append({
                "No": test_number,
                "Operasi": op,
                "Volume (MB)": vol,
                "Client Worker Pool": client_num_workers,
                "Client Pool Type": client_pool_type,
                "Server Pool Type": server_pool_type,
                "Server Worker Pool": server_num_workers,
                "Waktu Total per Client (s)": "N/A",
                "Throughput per Client (B/s)": "N/A",
                "Client Sukses": "N/A",
                "Client Gagal": "N/A",
                "Server Sukses": "N/A",
                "Server Gagal": "N/A",
                "Keterangan": "Server gagal dimulai"
            })
            test_number += 1
            time.sleep(2)
            continue 

        client_results = run_client_stress_test(op, vol, client_pool_type, client_num_workers)
        
        stop_server()
        
        time.sleep(1) 

        successful_server_workers, failed_server_workers = get_server_worker_metrics_from_log()

        if op == 'upload':
            cleanup_uploaded_files()

        current_result = {
            "No": test_number,
            "Operasi": op,
            "Volume (MB)": vol,
            "Client Worker Pool": client_num_workers,
            "Client Pool Type": client_pool_type,
            "Server Pool Type": server_pool_type,
            "Server Worker Pool": server_num_workers,
            "Waktu Total per Client (s)": round(client_results.get("time_per_client_s", 0), 4) if isinstance(client_results.get("time_per_client_s"), (int, float)) else client_results.get("time_per_client_s", "N/A"),
            "Throughput per Client (B/s)": round(client_results.get("throughput_per_client_bps", 0), 2) if isinstance(client_results.get("throughput_per_client_bps"), (int, float)) else client_results.get("throughput_per_client_bps", "N/A"),
            "Client Sukses": client_results.get("successful_client_workers", "N/A"),
            "Client Gagal": client_results.get("failed_client_workers", "N/A"),
            "Server Sukses": successful_server_workers,
            "Server Gagal": failed_server_workers,
            "Keterangan": client_results.get("error", "OK")
        }
        all_test_results.append(current_result)
        
        test_number += 1
        time.sleep(2) 
    
    logging.info("\n--- Rangkaian stress test selesai ---")

    df_results = pd.DataFrame(all_test_results)
    
    print("\n" + "="*80)
    print("                 HASIL STRESS TEST KOMPREHENSIF")
    print("="*80)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(df_results.to_string()) 
    print("="*80)

    output_csv_file = "stress_test_results.csv"
    df_results.to_csv(output_csv_file, index=False)
    logging.info(f"Hasil stress test disimpan ke '{output_csv_file}'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Stress test dihentikan oleh pengguna.")
        stop_server()
    finally:
        cleanup_uploaded_files()
        logging.info("Proses orchestrator selesai.")