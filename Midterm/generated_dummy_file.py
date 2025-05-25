import os
import random

FILE_SIZES_MB = [10, 50, 100]

SERVER_FILES_DIR = "files" 
CLIENT_UPLOAD_SOURCE_DIR = "." 

BASE_TEXT_CONTENT = "This is a dummy text file generated for stress testing purposes. Line number: "
BYTES_PER_LINE_ESTIMATE = len(BASE_TEXT_CONTENT.encode('utf-8')) + len(str(len(BASE_TEXT_CONTENT) * 1000000).encode('utf-8')) + 1

def create_text_dummy_file(target_dir, filename, size_mb):
    target_bytes = size_mb * 1024 * 1024
    
    filepath = os.path.join(target_dir, filename)
    
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"Membuat file teks dummy: {filepath} ({size_mb} MB)...")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            current_bytes = 0
            line_num = 0
            while current_bytes < target_bytes:
                line_to_write = f"{BASE_TEXT_CONTENT}{line_num}\n"
                encoded_line = line_to_write.encode('utf-8')
                
                if current_bytes + len(encoded_line) > target_bytes:
                    remaining_bytes = target_bytes - current_bytes
                    f.write(encoded_line[:remaining_bytes].decode('utf-8', errors='ignore')) 
                    current_bytes += remaining_bytes
                    break
                else:
                    f.write(line_to_write)
                    current_bytes += len(encoded_line)
                line_num += 1
        
        actual_size = os.path.getsize(filepath)
        print(f"File {filename} berhasil dibuat di {target_dir}. Ukuran aktual: {actual_size / (1024*1024):.2f} MB")
    except IOError as e:
        print(f"Error saat membuat file {filename} di {target_dir}: {e}")

if __name__ == "__main__":
    print("Memulai pembuatan file teks dummy untuk stress test...")
    
    os.makedirs(SERVER_FILES_DIR, exist_ok=True)

    for size in FILE_SIZES_MB:
        download_filename = f"dummy_download_{size}MB.txt"
        create_text_dummy_file(SERVER_FILES_DIR, download_filename, size)
        
        upload_filename = f"dummy_upload_{size}MB.txt"
        create_text_dummy_file(CLIENT_UPLOAD_SOURCE_DIR, upload_filename, size) 
        
    print("\nPembuatan file dummy selesai.")
    print(f"Pastikan file-file berikut ada di direktori '{SERVER_FILES_DIR}/' (untuk download oleh client):")
    for size in FILE_SIZES_MB:
        print(f"- {os.path.join(SERVER_FILES_DIR, f'dummy_download_{size}MB.txt')}")
    print(f"\nDan file-file berikut ada di direktori '{CLIENT_UPLOAD_SOURCE_DIR}/' (untuk upload dari client):")
    for size in FILE_SIZES_MB:
        print(f"- {os.path.join(CLIENT_UPLOAD_SOURCE_DIR, f'dummy_upload_{size}MB.txt')}")