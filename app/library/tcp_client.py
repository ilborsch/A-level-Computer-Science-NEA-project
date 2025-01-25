import socket
import threading

# ./app/library/tcp_client.py


class TCPClient:
    """
    A simple TCP client for communicating with a server.

    This client handles connection, message sending, and receiving responses in a thread-safe manner.

    Attributes:
        __host (str): The host address of the server to connect to.
        __port (int): The port number of the server to connect to.
        __lock (threading.Lock): A lock to ensure thread-safe operations.
        __client_socket (socket.socket): The client socket used for communication.
    """

    def __init__(self, host: str = 'localhost', port: int = 6379):
        """
        Initialize a TCPClient instance.

        Args:
            host (str): The host address of the server. Defaults to 'localhost'.
            port (int): The port number of the server. Defaults to 6379.
        """
        self.__host = host
        self.__port = port
        self.__lock = threading.Lock()
        self.__client_socket = None

    def connect(self):
        """
        Establish a connection to the server.

        Raises:
            socket.error: If the connection to the server fails.
        """
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__client_socket.connect((self.__host, self.__port))

    def send(self, message: str) -> str:
        """
        Send a message to the server and receive the response.

        Args:
            message (str): The message to send to the server.

        Returns:
            str: The response from the server.

        Raises:
            ValueError: If the client is not connected to the server.
        """
        if self.__client_socket is None:
            raise ValueError("Client is not connected to the server.")

        with self.__lock:
            self.__client_socket.send(message.encode('utf-8'))
            response = self.__client_socket.recv(1024).decode('utf-8')
            return response

    def close_connection(self):
        """
        Close the connection to the server and clean up resources.
        """
        if self.__client_socket is not None:
            self.__client_socket.close()
            self.__client_socket = None
