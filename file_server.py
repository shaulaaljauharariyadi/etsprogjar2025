import socket
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from file_protocol import FileProtocol
import json

fp = FileProtocol()

class ProcessTheClient:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address

    def run(self):
        try:
            self.connection.settimeout(120)  # Long timeout for client communication
            data_received = ""
            while True:
                try:
                    data = self.connection.recv(4096)
                except socket.timeout:
                    logging.error(f"Timeout while receiving data from client {self.address}")
                    try:
                        self.connection.sendall(
                            json.dumps({'status': 'ERROR', 'data': 'Timeout while receiving data from client'}).encode() + b"\r\n\r\n"
                        )
                    except Exception as send_err:
                        logging.error(f"Failed to send timeout error response: {send_err}")
                    return  # Exit after sending error
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            logging.warning(f"string diproses: {data_received}")
            hasil = fp.proses_string(data_received.strip())
            hasil = hasil + "\r\n\r\n"
            try:
                self.connection.sendall(hasil.encode())
            except Exception as send_err:
                logging.error(f"Failed to send response to client: {send_err}")
        except Exception as e:
            logging.error(f"Exception in client thread: {str(e)}")
            try:
                self.connection.sendall(
                    json.dumps({'status': 'ERROR', 'data': str(e)}).encode() + b"\r\n\r\n"
                )
            except Exception as send_err:
                logging.error(f"Failed to send error response: {send_err}")
        finally:
            self.connection.close()

class Server(threading.Thread):
    def __init__(self, ipaddress='0.0.0.0', port=12345, pool_type='thread', max_workers=10):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)
        self.pool_type = pool_type
        self.max_workers = max_workers
        if self.pool_type == 'thread':
            self.pool = ThreadPoolExecutor(max_workers=self.max_workers)
        else:
            self.pool = ProcessPoolExecutor(max_workers=self.max_workers)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)
        while True:
            conn, addr = self.my_socket.accept()
            logging.warning(f"connection from {addr}")
            self.pool.submit(ProcessTheClient(conn, addr).run)

def main():
    # Ganti pool_type ke 'process' jika ingin process pool
    svr = Server(ipaddress='0.0.0.0', port=12345, pool_type='thread', max_workers=10)
    svr.start()
    svr.join()  # Prevent main thread from exiting

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    main()
