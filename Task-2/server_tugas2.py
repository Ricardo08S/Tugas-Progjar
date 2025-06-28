import socket
import threading
import logging
from datetime import datetime
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        logging.info(f"[CONNECTED] Client {self.address} has connected.")
        
        try:
            while True:
                data = self.connection.recv(1024)
                if not data:
                    break

                request_string = data.decode('utf-8').strip()
                
                if request_string == "TIME":
                    tz_wib = pytz.timezone('Asia/Jakarta')
                    
                    now_wib = datetime.now(tz_wib)
                    
                    waktu_str = now_wib.strftime("%H:%M:%S")

                    response = f"JAM {waktu_str}\r\n"
                    self.connection.sendall(response.encode('utf-8'))
                
                elif request_string == "QUIT":
                    break
                
                else:
                    response = "Error: Invalid command\r\n"
                    self.connection.sendall(response.encode('utf-8'))

        finally:
            logging.info(f"[DISCONNECTED] Client {self.address} has disconnected.")
            self.connection.close()


class Server(threading.Thread):
    def __init__(self, port):
        self.the_clients = []
        self.port = port
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', self.port))
        self.my_socket.listen(5)
        logging.info(f"[STARTED] Time Server listening on port {self.port}")

        while True:
            connection, client_address = self.my_socket.accept()
            logging.info(f"[ACCEPTED] Connection from {client_address}")
            
            client_thread = ProcessTheClient(connection, client_address)
            client_thread.start()
            self.the_clients.append(client_thread)


def main():
    port = 45000
    server = Server(port)
    server.start()

if __name__ == "__main__":
    main()