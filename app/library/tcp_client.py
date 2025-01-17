import socket
import threading


class TCPClient:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.__host = host
        self.__port = port
        self.__lock = threading.Lock()
        self.__client_socket = None

    def connect(self):
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__client_socket.connect((self.__host, self.__port))

    def send(self, message: str):
        if self.__client_socket is None:
            return ''

        with self.__lock:
            self.__client_socket.send(message.encode('utf-8'))
            response = self.__client_socket.recv(1024).decode('utf-8')
            return response

    def close_connection(self):
        if self.__client_socket is not None:
            self.__client_socket.close()
            self.__client_socket = None

