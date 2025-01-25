from tcp_client import TCPClient
from typing import Hashable, Any
from dataclasses import dataclass
from enum import Enum

# ./app/library/library.py


@dataclass
class Config:
    """
    Represents the configuration details for Rediska.

    Attributes:
        username (str): The username of the logged-in user.
        cache_type (str): The type of cache being used (e.g., TTL, LRU, LFU).
        hash_function (str): The hash function used for the cache.
        capacity (int): The capacity of the cache.
        ttl (int): The time-to-live (TTL) value for cache items in seconds.
    """
    username: str
    cache_type: str
    hash_function: str
    capacity: int
    ttl: int


class RediskaQueryError(Exception):
    """
    Exception raised when a query to the Rediska server fails.
    """
    pass


class SetConfigKey(Enum):
    """
    Enum representing valid keys for SET_CONFIG commands.

    Attributes:
        CacheType (str): Key for setting the cache type.
        Username (str): Key for setting the username.
        Password (str): Key for setting the password.
        HashFunctionType (str): Key for setting the hash function type.
        StorageCapacity (str): Key for setting the cache storage capacity.
        TTLSeconds (str): Key for setting the time-to-live (TTL) value.
    """
    CacheType = "cache_type"
    Username = "username"
    Password = "password"
    HashFunctionType = "hash_function"
    StorageCapacity = "storage_capacity"
    TTLSeconds = "ttl_seconds"


class CacheType(Enum):
    """
    Enum representing the supported cache types.

    Attributes:
        TTL (str): Time-to-Live cache.
        LRU (str): Least Recently Used cache.
        LFU (str): Least Frequently Used cache.
    """
    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"


class HashFunctionType(Enum):
    """
    Enum representing the supported hash function types.

    Attributes:
        PythonHash (str): Default Python hash function.
        Division (str): Division method for hashing.
        Multiplication (str): Multiplication method for hashing.
        MidSquareMethod (str): Mid-square method for hashing.
        FoldingMethod (str): Folding method for hashing.
        DJB2 (str): DJB2 hash function.
    """
    PythonHash = "py_hash"
    Division = "division"
    Multiplication = "multiplication"
    MidSquareMethod = "midsquare"
    FoldingMethod = "folding"
    DJB2 = "djb2"


class Rediska:
    """
    A client interface for interacting with the Rediska server.

    Provides methods to perform cache operations, manage configurations, and communicate with the server.

    Attributes:
        __tcp_client (TCPClient): The TCP client for communication with the server.
    """

    def __init__(self):
        """
        Initialize a Rediska instance and set up the TCP client.
        """
        self.__tcp_client = TCPClient('localhost')

    def __del__(self):
        """
        Ensure the connection to the server is closed when the object is deinitialized (deleted).
        """
        self.close_connection()

    def connect(self):
        """
        Establish a connection to the Rediska server.
        """
        self.__tcp_client.connect()

    def close_connection(self):
        """
        Close the connection to the Rediska server.
        """
        self.__tcp_client.close_connection()

    def get(self, key: Hashable) -> str:
        """
        Retrieve a value from the cache.

        Args:
            key (Hashable): The key to retrieve.

        Returns:
            str: The value associated with the key.
        """
        query = f"GET {key}"
        response = self.__tcp_client.send(query)
        return response

    def set(self, key: Hashable, value: Any):
        """
        Set a key-value pair in the cache.

        Args:
            key (Hashable): The key to set.
            value (Any): The value to associate with the key.

        Raises:
            RediskaQueryError: If the server response indicates an error.
        """
        query = f"SET {key} {value}"
        response = self.__tcp_client.send(query)
        if response != "SUCCESS":
            raise RediskaQueryError(f"Invalid query: {response}")

    def set_config(self, key: SetConfigKey, value: str):
        """
        Update a configuration setting on the server.

        Args:
            key (SetConfigKey): The configuration key to update.
            value (str): The new value for the configuration key.

        Raises:
            RediskaQueryError: If the key or value is invalid or the server response indicates an error.
        """
        if key not in SetConfigKey:
            raise RediskaQueryError("Invalid key for SET_CONFIG. Please, check documentation.")

        config_key = SetConfigKey(key)
        hash_function_types = [func_type.value for func_type in HashFunctionType]
        if config_key == SetConfigKey.HashFunctionType and value not in hash_function_types:
            raise RediskaQueryError("Invalid value for SET_CONFIG hash_function command.")

        cache_types = [cache_type.value for cache_type in CacheType]
        if config_key == SetConfigKey.CacheType and value not in cache_types:
            raise RediskaQueryError("Invalid value for SET_CONFIG cache_type command.")

        query = f"SET_CONFIG {key.value} {value}"
        response = self.__tcp_client.send(query)
        if response != "SUCCESS":
            raise RediskaQueryError(f"Invalid query: {response}")

    def remove(self, key: Hashable):
        """
        Remove a key-value pair from the cache.

        Args:
            key (Hashable): The key to remove.

        Raises:
            RediskaQueryError: If the server response indicates an error.
        """
        query = f"REMOVE {key}"
        response = self.__tcp_client.send(query)
        if response != "SUCCESS":
            raise RediskaQueryError(f"Invalid query: {response}")

    def get_config_raw(self) -> str:
        """
        Retrieve the raw configuration details from the server.

        Returns:
            str: The raw configuration details as a string.
        """
        query = f"CONFIG"
        response = self.__tcp_client.send(query)
        return response

    def get_config(self) -> Config:
        """
        Retrieve and parse the configuration details from the server.

        Returns:
            Config: The parsed configuration details.
        """
        raw_config = self.get_config_raw()

        # parse config data by lines
        lines = list(filter(lambda x: len(x) > 1, map(lambda line: line.strip().split(': '), raw_config.split('\n'))))
        return Config(
            username=lines[0][1],
            cache_type=lines[1][1],
            hash_function=lines[2][1],
            capacity=int(lines[3][1].split(' ')[0]),
            ttl=int(lines[4][1][:-1])
        )


if __name__ == '__main__':
    db = Rediska()
    db.connect()
    print(db.set_config(SetConfigKey.CacheType, CacheType.TTL.value))
    print(db.set_config(SetConfigKey.TTLSeconds, "20"))
    print(db.get_config())

