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


class Database:
    def __init__(self, config_filename: str):
        self.__config_filepath = str(Path(__file__).resolve().parent / 'config' / config_filename)
        self.__config = config.load_config(self.__config_filepath)
        self.__file_handler = FileStorageHandler(filename="storage.red")
        self.__parser = Parser()
        self.__tcp_server = TCPServer(
            host='localhost',
            port=6379,
            handle_func=self.parse_user_input
        )
        self.__cache, n = self.__file_handler.read(
            self.__config.cache.type,
            self.__config.cache.ttl_seconds,
            self.__config.cache.capacity,
            self.__config.cache.hash_function
        )
        if n == 0:
            self.__cache = cache.CacheFactory.initialise_cache(
                self.__config.cache.type,
                self.__config.cache.ttl_seconds,
                self.__config.cache.capacity,
                self.__config.cache.hash_function
            )

        self.__authenticate_user(self.__config.user.username, self.__config.user.password)

    def __authenticate_user(self, username: str, password: str):
        if username == "":
            print("Please, register before using Rediska.")
            while True:
                new_username = input("Username: ")
                new_password = getpass.getpass("Password: ")
                password_repeat = getpass.getpass("Repeat password: ")
                if new_password == password_repeat:
                    break
                print("Passwords must match! Please, try again.\n")

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
        self.__tcp_server.start()

    def get(self, key: Hashable) -> str:
        return self.__cache.get(key)

    def set_config(self, key: str, value: Any) -> str:
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
        self.__cache.set(key, value)
        return "SUCCESS"

    def __change_cache(self):
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
        self.__cache.remove(key)
        return "SUCCESS"

    def parse_user_input(self, user_input: str) -> Any:
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
        config.save_config(self.__config, self.__config_filepath)
        self.__file_handler.write(self.__cache)
        if self.__tcp_server.is_running:
            self.__tcp_server.close()

    def get_config(self) -> str:
        return f"""
Logged in username: {base64.b64decode(self.__config.user.username).decode('utf-8')}
Cache Type: {self.__config.cache.type.value.upper()}
Hash Function: {self.__config.cache.hash_function.value.title()}
Capacity: {self.__config.cache.capacity} pairs
TTL Seconds: {self.__config.cache.ttl_seconds}s
        """

