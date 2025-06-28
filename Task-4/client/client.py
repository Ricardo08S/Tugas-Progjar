import socket
import os
import base64
import json
import time

def parse_response(response_str):
    try:
        header_part, body_part = response_str.split('\r\n\r\n', 1)
        return header_part, body_part
    except ValueError:
        return response_str, ""

def print_response_body(body_str):
    try:
        data = json.loads(body_str)
        print(json.dumps(data, indent=4))
    except json.JSONDecodeError:
        print(body_str)

def send_request(host, port, request_str):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((host, port))
            sock.sendall(request_str.encode('utf-8'))
            
            response_bytes = b''
            while True:
                try:
                    data = sock.recv(2048)
                    if not data:
                        break
                    response_bytes += data
                except socket.timeout:
                    break
            
            return response_bytes.decode('utf-8')
    except ConnectionRefusedError:
        return "KONEKSI GAGAL: Pastikan server sudah berjalan."
    except Exception as e:
        return f"Terjadi Error: {str(e)}"

def list_files(host, port):
    print("\n[INFO] Meminta daftar file dari endpoint /list...")
    request = "GET /list HTTP/1.0\r\n\r\n"
    response = send_request(host, port, request)
    header, body = parse_response(response)
    print("Respons dari Server")
    print_response_body(body)

def upload_file(host, port, filepath):
    filename = os.path.basename(filepath)
    print(f"[INFO] Mengirim file '{filename}' ke endpoint /upload...")
    
    try:
        with open(filepath, 'rb') as f:
            file_content_binary = f.read()
        
        file_content_base64 = base64.b64encode(file_content_binary).decode('utf-8')
        
        body = file_content_base64
        headers = [
            "POST /upload HTTP/1.0",
            f"X-Filename: {filename}",
            f"Content-Length: {len(body)}",
        ]
        request = "\r\n".join(headers) + "\r\n\r\n" + body
        
        response = send_request(host, port, request)
        header, body = parse_response(response)
        print("Respons dari Server")
        print_response_body(body)

    except FileNotFoundError:
        print(f"ERROR: File '{filepath}' tidak ditemukan di client.")

def delete_file(host, port, filename):
    print(f"[INFO] Mengirim permintaan hapus untuk '{filename}'...")
    request = f"DELETE /delete/{filename} HTTP/1.0\r\n\r\n"
    response = send_request(host, port, request)
    header, body = parse_response(response)
    print("Respons dari Server")
    print_response_body(body)

if __name__ == '__main__':
    TARGET_HOST = '172.16.16.101'
    # TARGET_PORT = 8885
    TARGET_PORT = 8889
    
    FILES_TO_TEST = [
        "testing.txt",
        "donalbebek.jpg",
        "pokijan.jpg",
        "research_center.jpg",
        "resources.txt",
        "rfc2616.pdf"
    ]
    
    for f in FILES_TO_TEST:
        if not os.path.exists(f):
            print(f"!!! PERINGATAN: File uji '{f}' tidak ditemukan. Pengujian dibatalkan.")
            exit()
            
    print(f"\nMEMULAI PENGUJIAN ke {TARGET_HOST}:{TARGET_PORT}")
    
    print("\nKONDISI AWAL SERVER")
    list_files(TARGET_HOST, TARGET_PORT)
    time.sleep(1)

    print("\n\nMENGUNGGAH SEMUA FILE KE SERVER")
    for filename in FILES_TO_TEST:
        upload_file(TARGET_HOST, TARGET_PORT, filename)
        time.sleep(0.5)

    print("\n\nVERIFIKASI SEMUA FILE SUDAH ADA DI SERVER")
    list_files(TARGET_HOST, TARGET_PORT)
    time.sleep(2)

    print("\n\nMENGHAPUS SEMUA FILE DARI SERVER")
    for filename in FILES_TO_TEST:
        delete_file(TARGET_HOST, TARGET_PORT, filename)
        time.sleep(0.5)

    print("\n\nVERIFIKASI SERVER KEMBALI KOSONG")
    list_files(TARGET_HOST, TARGET_PORT)

    print("\nPENGUJIAN LENGKAP SELESAI")