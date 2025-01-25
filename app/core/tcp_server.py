import socket
import threading
from typing import Callable

# ./app/core/tcp_server.py


class TCPServer:
    """
    A simple multi-threaded TCP server.

    This server listens for incoming connections, handles client messages, and responds using a specified handler function.

    Attributes:
        __host (str): The host address to bind the server.
        __port (int): The port number to bind the server.
        __handle_func (Callable[[str], str]): The function to handle incoming messages from clients.
        __server_socket (socket.socket): The server's socket object.
        __is_running (bool): Indicates whether the server is currently running.
    """

    def __init__(self, host: str = 'localhost', port: int = 6379, handle_func: Callable[[str], str] = None):
        """
        Initialize the TCPServer instance.

        Args:
            host (str): The host address to bind the server. Defaults to 'localhost'.
            port (int): The port number to bind the server. Defaults to 6379.
            handle_func (Callable[[str], str], optional): A function to process client messages. Defaults to a simple print function.
        """
        self.__host = host
        self.__port = port
        self.__handle_func = handle_func or (lambda message: print(message))
        self.__server_socket = None
        self.__is_running = False

    def start(self):
        """
        Start the TCP server and listen for incoming connections.

        The server accepts incoming client connections and spawns a new thread to handle each client.
        """
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # init TCP socket
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
        """
        Handle communication with a connected client.

        Args:
            client_socket (socket.socket): The socket object representing the client connection.
        """
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
        """
        Stop the server and close the server socket.
        """
        if self.__server_socket:
            self.__is_running = False
            self.__server_socket.close()
            self.__server_socket = None
            print("Server closed.")

    @property
    def is_running(self):
        """
        Returns True if the server is currently running.

        Returns:
            bool: True if the server is running, False otherwise.
        """
        return self.__is_running
