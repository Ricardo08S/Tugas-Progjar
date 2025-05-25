import socket
import logging
import time
import sys
import argparse
import os 
import threading

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from file_protocol import FileProtocol

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_LOG_FULL_PATH = os.path.join(SCRIPT_DIR, "server_log.log")

fp = FileProtocol() 

logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(SERVER_LOG_FULL_PATH), 
                        logging.StreamHandler(sys.stdout)     
                    ])

def handle_client(connection, address):
    worker_id = threading.current_thread().name if isinstance(threading.current_thread(), threading.Thread) else os.getpid()
    logging.warning(f"Worker {worker_id} mulai menangani koneksi dari {address}")
    
    data_received = ""
    start_time = time.time()
    total_bytes_processed = 0
    response_bytes_sent = 0

    try:
        while True:
            data = connection.recv(4096)
            if data:
                data_received += data.decode()
                total_bytes_processed += len(data) 
                
                if "\r\n\r\n" in data_received:
                    command_str, _, remainder = data_received.partition("\r\n\r\n")
                    data_received = remainder 
                    
                    hasil = fp.proses_string(command_str)
                    hasil = hasil + "\r\n\r\n" 
                    
                    encoded_response = hasil.encode()
                    connection.sendall(encoded_response)
                    response_bytes_sent += len(encoded_response) 
            else:
                break
    except Exception as e:
        logging.error(f"Error saat menangani client {address} pada worker {worker_id}: {e}")
    finally:
        connection.close()
        end_time = time.time()
        duration = end_time - start_time
        throughput_received = (total_bytes_processed / duration) if duration > 0 else 0
        
        logging.warning(f"Worker {worker_id} selesai menangani koneksi dari {address}. Durasi: {duration:.4f}s, Byte Received (from client): {total_bytes_processed}B, Byte Sent (to client): {response_bytes_sent}B, Throughput Received: {throughput_received:.2f} B/s")
        for handler in logging.getLogger().handlers:
            handler.flush()

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=6667, pool_type='thread', max_workers=5):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.pool_type = pool_type
        self.max_workers = max_workers
        self.executor = None 
        
        logging.warning(f"Server diinisialisasi pada {self.ipinfo} dengan {pool_type} pool ({max_workers} workers)")

    def start(self):
        logging.warning(f"Server mencoba berjalan di ip address {self.ipinfo}")
        try:
            self.my_socket.bind(self.ipinfo)
            self.my_socket.listen(100)
            logging.warning(f"Server berhasil mendengarkan koneksi pada {self.ipinfo}")

            if self.pool_type == 'thread':
                self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
                logging.warning(f"Menggunakan ThreadPoolExecutor dengan {self.max_workers} workers.")
            elif self.pool_type == 'process':
                self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
                logging.warning(f"Menggunakan ProcessPoolExecutor dengan {self.max_workers} workers.")
            else:
                raise ValueError("Tipe pool tidak valid. Gunakan 'thread' atau 'process'.")

            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"Koneksi masuk dari {client_address}. Menyerahkan ke pool...")
                self.executor.submit(handle_client, connection, client_address)
        except KeyboardInterrupt:
            logging.warning("Server dimatikan oleh pengguna (Ctrl+C).")
        except Exception as e:
            logging.error(f"Fatal error server: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        if self.executor:
            logging.warning("Mematikan executor pool. Menunggu tugas selesai...")
            self.executor.shutdown(wait=True)
            logging.warning("Executor pool dimatikan.")
        if self.my_socket:
            self.my_socket.close()
            logging.warning("Socket server ditutup.")
        for handler in logging.getLogger().handlers:
            handler.flush()

def main():
    parser = argparse.ArgumentParser(description="File Server dengan Konkurensi Pool untuk Stress Test ETS.")
    parser.add_argument('--pool_type', type=str, default='thread',
                        choices=['thread', 'process'],
                        help="Tipe pool untuk konkurensi (thread atau process). Default: thread")
    parser.add_argument('--max_workers', type=int, default=5,
                        help="Jumlah maksimum worker dalam pool. Default: 5")
    parser.add_argument('--port', type=int, default=6667,
                        help="Port yang akan digunakan server. Default: 6667")
    
    args = parser.parse_args()
    
    svr = Server(ipaddress='0.0.0.0', port=args.port, 
                 pool_type=args.pool_type, max_workers=args.max_workers)
    svr.start()

if __name__ == "__main__":
    main()