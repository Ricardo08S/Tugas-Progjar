import sys
import os
import os.path
import uuid
import json
import base64
from glob import glob
from datetime import datetime

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        
        self.upload_dir = 'public'
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append(f"HTTP/1.0 {kode} {message}\r\n")
        resp.append(f"Date: {tanggal}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        
        if isinstance(messagebody, str) and messagebody.startswith('{'):
            headers['Content-Type'] = 'application/json'
            
        resp.append(f"Content-Length: {len(messagebody)}\r\n")
        for kk in headers:
            resp.append(f"{kk}:{headers[kk]}\r\n")
        resp.append("\r\n")

        response_headers = "".join(resp)

        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        return response

    def proses(self, data):
        requests = data.split("\r\n")
        baris = requests[0]

        headers = {}
        body_start_index = -1
        for i, line in enumerate(requests[1:]):
            if line == "":
                body_start_index = i + 2
                break
            parts = line.split(":", 1)
            if len(parts) == 2:
                headers[parts[0].strip()] = parts[1].strip()

        body = ""
        if body_start_index != -1:
            body = "\r\n".join(requests[body_start_index:])


        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address, headers)
            elif method == 'POST':
                return self.http_post(object_address, headers, body)
            elif method == 'DELETE':
                return self.http_delete(object_address, headers)
            else:
                return self.response(400, 'Bad Request', 'Unsupported method', {})
        except IndexError:
            return self.response(400, 'Bad Request', 'Malformed request', {})

    def http_get(self, object_address, headers):
        if object_address == '/list':
            try:
                files = os.listdir(self.upload_dir)
                response_data = json.dumps({"status": "success", "files": files})
                return self.response(200, 'OK', response_data, {})
            except FileNotFoundError:
                return self.response(404, 'Not Found', 'Directory not found', {})

        file_path = os.path.join(self.upload_dir, object_address.strip('/'))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as fp:
                isi = fp.read()
            fext = os.path.splitext(file_path)[1]
            content_type = self.types.get(fext, 'application/octet-stream')
            headers_response = {'Content-type': content_type}
            return self.response(200, 'OK', isi, headers_response)
        
        return self.response(404, 'Not Found', 'File or endpoint not found', {})

    def http_post(self, object_address, headers, body):
        if object_address != '/upload':
            return self.response(404, 'Not Found', 'Endpoint not found for POST', {})

        try:
            filename = headers.get('X-Filename')
            if not filename:
                return self.response(400, 'Bad Request', 'X-Filename header is required', {})

            file_content = base64.b64decode(body)
            
            file_path = os.path.join(self.upload_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            response_data = json.dumps({"status": "success", "message": f"File '{filename}' berhasil diupload"})
            return self.response(201, 'Created', response_data, {})
        except Exception as e:
            response_data = json.dumps({"status": "error", "message": f"Upload failed: {str(e)}"})
            return self.response(500, 'Internal Server Error', response_data, {})

    def http_delete(self, object_address, headers):
        if not object_address.startswith('/delete/'):
            return self.response(400, 'Bad Request', 'Invalid DELETE endpoint', {})

        filename = object_address.split('/')[-1]
        if not filename:
            return self.response(400, 'Bad Request', 'Filename not specified', {})

        file_path = os.path.join(self.upload_dir, filename)

        try:
            os.remove(file_path)
            response_data = json.dumps({"status": "success", "message": f"File {filename} dihapus."})
            return self.response(200, 'OK', response_data, {})
        except FileNotFoundError:
            response_data = json.dumps({"status": "error", "message": f"File {filename} tidak ditemukan."})
            return self.response(404, 'Not Found', response_data, {})
        except Exception as e:
            response_data = json.dumps({"status": "error", "message": f"Error deleting file: {str(e)}"})
            return self.response(500, 'Internal Server Error', response_data, {})

if __name__ == "__main__":
    httpserver = HttpServer()
