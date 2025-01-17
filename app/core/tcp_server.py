import socket
import threading
from typing import Callable


class TCPServer:
    def __init__(self, host: str = 'localhost', port: int = 6379, handle_func: Callable[[str], str] = None):
        self.__host = host
        self.__port = port
        self.__handle_func = handle_func or (lambda message: print(message))
        self.__server_socket = None
        self.__is_running = False

    def start(self):
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen(5)
        self.__is_running = True

        print(f"Server started on {self.__host}:{self.__port}")

        try:
            while self.__is_running:
                client_socket, addr = self.__server_socket.accept()
                print(f"Connection from {addr}")
                client_handler = threading.Thread(target=self.__handle_client, args=(client_socket,))
                client_handler.start()
        except OSError:
            print("Server socket closed.")
        finally:
            self.close()

    def __handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                response = self.__handle_func(message)
                if not response:
                    response = "None"
                client_socket.send(response.encode('utf-8'))
            except Exception as e:
                print(f"Error handling client: {e}")
                break
        client_socket.close()

    def close(self):
        if self.__server_socket:
            self.__is_running = False
            self.__server_socket.close()
            self.__server_socket = None
            print("Server closed.")

    @property
    def is_running(self):
        return self.__is_running

