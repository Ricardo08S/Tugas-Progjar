import socket

HOST = '172.16.16.101'
PORT = 45000

def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"Successfully connected to server at {HOST}:{PORT}")
            print("You can send commands now.")
            print("Type 'TIME' to get the current time, or 'QUIT' to exit.")
            print("-" * 20)

        except ConnectionRefusedError:
            print(f"Connection failed. Is the server running at {HOST}:{PORT}?")
            return

        while True:
            message = input("> ")
            
            if not message:
                continue

            formatted_message = message.strip().upper()
            command_to_send = f"{formatted_message}\r\n"
            
            s.sendall(command_to_send.encode('utf-8'))

            if formatted_message == "QUIT":
                print("Sent QUIT command. Closing connection.")
                break

            try:
                data = s.recv(1024)
                response = data.decode('utf-8').strip()
                print(f"Server: {response}")
            except ConnectionError:
                print("Connection to server lost.")
                break

if __name__ == "__main__":
    run_client()