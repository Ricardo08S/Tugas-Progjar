import socket
import json
import base64
import logging
import os
import time
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("client_stress_test.log"),
                        logging.StreamHandler(sys.stdout)
                    ])

SERVER_ADDRESS=('172.16.16.101',6667) 

DOWNLOAD_DIR = "client_downloads/" 
UPLOAD_SOURCE_DIR = "."             

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def send_command(command_str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(SERVER_ADDRESS)
        command_to_send = (command_str + "\r\n\r\n").encode() 
        sock.sendall(command_to_send)
        
        data_received_chunks = [] 
        while True:
            data = sock.recv(4096) 
            if data:
                data_received_chunks.append(data)
                if b"\r\n\r\n" in b"".join(data_received_chunks):
                    break
            else:
                break
        
        full_data_received = b"".join(data_received_chunks).decode('utf-8', errors='ignore')
        
        if not full_data_received.strip():
            logging.error(f"Received empty response from server. Command: {command_str}")
            return {"status": "ERROR", "data": "Empty response from server."}

        json_data = full_data_received.split("\r\n\r\n")[0]
        
        if not json_data.strip():
            logging.error(f"Received empty JSON data. Raw: {full_data_received[:200]}...")
            return {"status": "ERROR", "data": "Empty JSON response part."}

        hasil = json.loads(json_data)
        return hasil
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error (Raw data: {full_data_received[:200]}...): {e}")
        return {"status": "ERROR", "data": "Invalid JSON response from server."}
    except Exception as e:
        logging.error(f"Error during data receiving/sending: {e}") 
        return {"status": "ERROR", "data": f"Client communication error: {e}"}
    finally:
        sock.close()

def download_file_task(filename):
    start_time = time.time()
    total_bytes = 0
    success = False
    try:
        command_str = f"GET {filename}"
        hasil = send_command(command_str)
        
        if hasil.get('status') == 'OK':
            remote_filename = hasil.get('data_namafile')
            encoded_content = hasil.get('data_file')
            if remote_filename and encoded_content:
                try:
                    decoded_content = base64.b64decode(encoded_content)
                    total_bytes = len(decoded_content)
                    
                    filepath = os.path.join(DOWNLOAD_DIR, remote_filename)
                    with open(filepath, 'wb+') as fp:
                        fp.write(decoded_content)
                    success = True
                    os.remove(filepath) 
                except Exception as decode_write_error:
                    logging.error(f"Error decoding or writing file {filename}: {decode_write_error}")
                    success = False 
            else:
                logging.error(f"Download task failed for {filename}: Missing remote_filename or encoded_content. Data: {hasil}")
                success = False
        else:
            logging.error(f"Server reported non-OK status for {filename}: {hasil.get('data', 'Unknown error')}")
            success = False 
    except Exception as e:
        logging.error(f"Exception in download task for {filename}: {e}")
    finally:
        end_time = time.time()
        duration = end_time - start_time
        return {"success": success, "duration": duration, "bytes_transferred": total_bytes}

def upload_file_task(local_filepath, remote_filename):
    start_time = time.time()
    total_bytes = 0
    success = False
    try:
        if not os.path.exists(local_filepath):
            logging.error(f"Local file {local_filepath} not found for upload.")
            return {"success": False, "duration": 0, "bytes_transferred": 0}

        with open(local_filepath, 'rb') as fp:
            file_content_bytes = fp.read()
        total_bytes = len(file_content_bytes)
        encoded_content = base64.b64encode(file_content_bytes).decode('utf-8')
        
        command_str = f"UPLOAD {remote_filename} {encoded_content}"
        hasil = send_command(command_str)

        if hasil.get('status') == 'OK':
            success = True
        else:
            logging.error(f"Upload task failed for {local_filepath} to {remote_filename}: {hasil.get('data', 'Unknown error')}")
    except Exception as e:
        logging.error(f"Exception in upload task for {local_filepath}: {e}")
    finally:
        end_time = time.time()
        duration = end_time - start_time
        return {"success": success, "duration": duration, "bytes_transferred": total_bytes}

def run_client_test(operation_type, file_size_mb, client_pool_type, num_client_workers):
    logging.warning(f"Client stress test dimulai: Operasi={operation_type}, Volume={file_size_mb}MB, ClientPool={client_pool_type}, Workers={num_client_workers}")
    
    successful_workers = 0
    failed_workers = 0
    total_duration_sum = 0 
    total_bytes_sum = 0    

    Executor = ThreadPoolExecutor if client_pool_type == 'thread' else ProcessPoolExecutor

    if operation_type == 'download':
        source_filename = f"dummy_download_{file_size_mb}MB.txt"
        remote_filename_on_server = source_filename 
        task_func = download_file_task
        task_args_list = [(remote_filename_on_server,) for _ in range(num_client_workers)]
    elif operation_type == 'upload':
        local_upload_source_path = os.path.join(UPLOAD_SOURCE_DIR, f"dummy_upload_{file_size_mb}MB.txt")
        task_func = upload_file_task
        task_args_list = [(local_upload_source_path, f"uploaded_dummy_{file_size_mb}MB_{int(time.time() * 1000)}_{i}.txt")
                          for i in range(num_client_workers)]
    else:
        logging.error(f"Operasi '{operation_type}' tidak didukung.")
        results = {
            "time_per_client_s": 0,
            "throughput_per_client_bps": 0,
            "successful_client_workers": 0,
            "failed_client_workers": num_client_workers,
            "error": "Unsupported operation type"
        }
        print(json.dumps(results)) 
        return

    futures = []
    with Executor(max_workers=num_client_workers) as executor:
        for args in task_args_list:
            futures.append(executor.submit(task_func, *args)) 

        for future in futures:
            try:
                result = future.result() 
                if result["success"]:
                    successful_workers += 1
                    total_duration_sum += result["duration"]
                    total_bytes_sum += result["bytes_transferred"]
                else:
                    failed_workers += 1
            except Exception as e:
                logging.error(f"Exception from worker task: {e}")
                failed_workers += 1

    avg_duration_per_successful_worker = (total_duration_sum / successful_workers) if successful_workers > 0 else 0
    avg_throughput_per_successful_worker = (total_bytes_sum / total_duration_sum) if total_duration_sum > 0 else 0
    
    results = {
        "time_per_client_s": avg_duration_per_successful_worker,
        "throughput_per_client_bps": avg_throughput_per_successful_worker,
        "successful_client_workers": successful_workers,
        "failed_client_workers": failed_workers
    }
    
    print(json.dumps(results))
    logging.warning(f"Client stress test selesai. Hasil: {json.dumps(results)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Client Stress Test untuk File Server.")
    parser.add_argument('--operation', type=str, required=True,
                        choices=['download', 'upload'],
                        help="Jenis operasi yang akan diuji: 'download' atau 'upload'")
    parser.add_argument('--volume', type=int, required=True,
                        choices=[10, 50, 100],
                        help="Volume file dalam MB yang akan diproses: 10, 50, atau 100")
    parser.add_argument('--client_pool_type', type=str, default='thread',
                        choices=['thread', 'process'],
                        help="Tipe pool untuk worker client: 'thread' atau 'process'. Default: 'thread'")
    parser.add_argument('--num_client_workers', type=int, default=1,
                        help="Jumlah worker client dalam pool yang akan melakukan operasi. Default: 1")
    
    args = parser.parse_args()

    run_client_test(
        operation_type=args.operation,
        file_size_mb=args.volume,
        client_pool_type=args.client_pool_type,
        num_client_workers=args.num_client_workers
    )