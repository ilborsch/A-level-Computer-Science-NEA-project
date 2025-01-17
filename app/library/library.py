from tcp_client import TCPClient
from typing import Hashable, Any
from dataclasses import dataclass
from enum import Enum


@dataclass
class Config:
    username: str
    cache_type: str
    hash_function: str
    capacity: int
    ttl: int


class RediskaQueryError(Exception):
    pass


class SetConfigKey(Enum):
    CacheType = "cache_type"
    Username = "username"
    Password = "password"
    HashFunctionType = "hash_function"
    StorageCapacity = "storage_capacity"
    TTLSeconds = "ttl_seconds"


class CacheType(Enum):
    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"


class HashFunctionType(Enum):
    PythonHash = "py_hash"
    Division = "division"
    Multiplication = "multiplication"
    MidSquareMethod = "midsquare"
    FoldingMethod = "folding"
    DJB2 = "djb2"


class Rediska:
    def __init__(self):
        self.__tcp_client = TCPClient('localhost')

    def __del__(self):
        self.close_connection()

    def connect(self):
        self.__tcp_client.connect()

    def close_connection(self):
        self.__tcp_client.close_connection()

    def get(self, key: Hashable) -> str:
        query = f"GET {key}"
        response = self.__tcp_client.send(query)
        return response

    def set(self, key: Hashable, value: Any):
        query = f"SET {key} {value}"
        response = self.__tcp_client.send(query)
        if response != "SUCCESS":
            raise RediskaQueryError(f"Invalid query: {response}")

    def set_config(self, key: SetConfigKey, value: str):
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
        query = f"REMOVE {key}"
        response = self.__tcp_client.send(query)
        if response != "SUCCESS":
            raise RediskaQueryError(f"Invalid query: {response}")

    def get_config_raw(self) -> str:
        query = f"CONFIG"
        response = self.__tcp_client.send(query)
        return response

    def get_config(self) -> Config:
        raw_config = self.get_config_raw()
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

