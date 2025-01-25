import config
import cache
import base64
import getpass
from file_handler import FileStorageHandler
from parser import Parser, Operation, SetCommandKeys
from tcp_server import TCPServer
from typing import Hashable, Any
from pathlib import Path
from config import HashFunctionType, CacheType

# ./app/core/database.py


class Database:
    """
    Represents the main database functionality for managing a cache and user authentication.

    This class manages user registration, login, cache operations, configuration updates,
    and communication through a TCP server.
    """

    def __init__(self, config_filename: str):
        """
        Initialize the Database instance.

        Args:
            config_filename (str): The name of the configuration file.
        """
        self.__config_filepath = str(Path(__file__).resolve().parent / 'config' / config_filename)
        self.__config = config.load_config(self.__config_filepath)
        self.__file_handler = FileStorageHandler(filename="storage.red")
        self.__parser = Parser()
        self.__tcp_server = TCPServer(
            host='localhost',
            port=6379,
            handle_func=self.parse_user_input
        )

        # read data stored by previous session
        self.__cache, n = self.__file_handler.read(
            self.__config.cache.type,
            self.__config.cache.ttl_seconds,
            self.__config.cache.capacity,
            self.__config.cache.hash_function
        )

        # if 0 bytes were read – initialise a new cache
        if n == 0:
            self.__cache = cache.CacheFactory.initialise_cache(
                self.__config.cache.type,
                self.__config.cache.ttl_seconds,
                self.__config.cache.capacity,
                self.__config.cache.hash_function
            )

        self.__authenticate_user(self.__config.user.username, self.__config.user.password)

    def __authenticate_user(self, username: str, password: str):
        """
        Authenticate or register a user.
        Stores credentials in a base64 encoding.

        Args:
            username (str): The encoded username.
            password (str): The encoded password.
        """
        if username == "":
            print("Please, register before using Rediska.")
            while True:
                new_username = input("Username: ")
                new_password = getpass.getpass("Password: ")
                password_repeat = getpass.getpass("Repeat password: ")
                if new_password == password_repeat:
                    break
                print("Passwords must match! Please, try again.\n")

            # credentials are stored in base64 encoding
            encoded_username = base64.b64encode(new_username.encode('utf-8'))
            encoded_password = base64.b64encode(new_password.encode('utf-8'))
            self.__config.user.username = encoded_username.decode('utf-8')
            self.__config.user.password = encoded_password.decode('utf-8')
            print("Registration successful.")
        else:
            decoded_username = base64.b64decode(username).decode('utf-8')
            decoded_password = base64.b64decode(password).decode('utf-8')

            print("Please, login before using Rediska.")
            while True:
                login_username = input("Username: ")
                login_password = getpass.getpass("Password: ")
                if login_username == decoded_username and login_password == decoded_password:
                    print("Login successful.")
                    break
                print("Login unsuccessful. Please, try again.\n")
        config.save_config(self.__config, self.__config_filepath)

    def start_tcp(self):
        """
        Start the TCP server for communication.
        """
        self.__tcp_server.start()

    def get(self, key: Hashable) -> str:
        """
        Retrieve the value associated with a key in the cache.

        Args:
            key (Hashable): The key to retrieve.

        Returns:
            str: The value associated with the key or an empty string if not found.
        """
        return self.__cache.get(key)

    def set_config(self, key: str, value: Any) -> str:
        """
        Update the configuration settings.
        Reinitialize cache if it's config is changed.

        Args:
            key (str): The configuration key to update.
            value (Any): The new value for the configuration key.

        Returns:
            str: "SUCCESS" if the configuration was updated successfully.

        Raises:
            KeyError: If the configuration key is invalid.
        """
        if key not in [k.value for k in SetCommandKeys]:
            raise KeyError("Invalid key for SET_CONFIG. Check `rediska docs` for guidance.")

        config_key = SetCommandKeys(key)
        match config_key:
            case SetCommandKeys.Username:
                encoded_username = base64.b64encode(value.encode('utf-8'))
                self.__config.user.username = encoded_username.decode('utf-8')
            case SetCommandKeys.Password:
                encoded_password = base64.b64encode(value.encode('utf-8'))
                self.__config.user.password = encoded_password.decode('utf-8')
            case SetCommandKeys.HashFunctionType:
                self.__config.cache.hash_function = HashFunctionType(value)
                self.__change_cache()
            case SetCommandKeys.CacheType:
                self.__config.cache.type = CacheType(value)
                self.__change_cache()
            case SetCommandKeys.TTLSeconds:
                self.__config.cache.ttl_seconds = value
                if self.__config.cache.type == config.CacheType.TTL:
                    self.__change_cache()
            case SetCommandKeys.StorageCapacity:
                self.__config.cache.capacity = value
                self.__change_cache()
        config.save_config(self.__config, self.__config_filepath)
        return "SUCCESS"

    def set(self, key: Hashable, value: Any) -> str:
        """
        Set a value in the cache.

        Args:
            key (Hashable): The key to set.
            value (Any): The value to associate with the key.

        Returns:
            str: "SUCCESS" if the key-value pair was successfully set.
        """
        self.__cache.set(key, value)
        return "SUCCESS"

    def __change_cache(self):
        """
        Reinitialize the cache when configuration settings change, transferring existing data.
        """
        data = self.__cache.items()
        self.__cache = cache.CacheFactory.initialise_cache(
            self.__config.cache.type,
            int(self.__config.cache.ttl_seconds),
            int(self.__config.cache.capacity),
            self.__config.cache.hash_function
        )
        for key, value in data:
            self.__cache.set(key, value)

    def remove(self, key: Hashable) -> str:
        """
        Remove a key-value pair from the cache.

        Args:
            key (Hashable): The key to remove.

        Returns:
            str: "SUCCESS" if the key was successfully removed.
        """
        self.__cache.remove(key)
        return "SUCCESS"

    def parse_user_input(self, user_input: str) -> Any:
        """
        Parse and execute user input commands.

        Args:
            user_input (str): The command input by the user.

        Returns:
            Any: The result of the executed command.
        """
        command = self.__parser.parse(user_input)
        match command.operation:
            case Operation.GET:
                return self.get(command.operands.key)
            case Operation.SET:
                return self.set(command.operands.key, command.operands.value)
            case Operation.REMOVE:
                return self.remove(command.operands.key)
            case Operation.SET_CONFIG:
                return self.set_config(command.operands.key, command.operands.value)
            case Operation.GET_CONFIG:
                return self.get_config()
            case Operation.EXIT:
                self.shutdown()
                return Operation.EXIT.value

    def shutdown(self):
        """
        Save configuration and cache data to persistent storage and shut down the server.
        """
        config.save_config(self.__config, self.__config_filepath)
        self.__file_handler.write(self.__cache)
        if self.__tcp_server.is_running:
            self.__tcp_server.close()

    def get_config(self) -> str:
        """
        Retrieve the current configuration settings.

        Returns:
            str: A formatted string of the current configuration.
        """
        return f"""
Logged in username: {base64.b64decode(self.__config.user.username).decode('utf-8')}
Cache Type: {self.__config.cache.type.value.upper()}
Hash Function: {self.__config.cache.hash_function.value.title()}
Capacity: {self.__config.cache.capacity} pairs
TTL Seconds: {self.__config.cache.ttl_seconds}s
        """
