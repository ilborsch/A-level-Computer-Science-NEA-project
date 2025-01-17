from cache import Cache, LFUCache, LRUCache, TTLCache
from hashing import KeyValue
from config import CacheType, HashFunctionType
from pathlib import Path
import os


class FileReader:
    def __init__(self, filename: str):
        self.__filepath = Path(__file__).resolve().parent.parent.parent / filename

    def read(self) -> str:
        with open(self.__filepath, 'r') as file:
            return file.read()

    def read_lines(self) -> list[str]:
        with open(self.__filepath, 'r') as file:
            return file.readlines()


class FileWriter:
    def __init__(self, filename: str):
        self.__filepath = Path(__file__).resolve().parent.parent.parent / filename

    def write(self, data: str):
        with open(self.__filepath, 'w') as file:
            file.write(data)


class FileStorageHandler:
    __EXTENSION = ".red"

    def __init__(self, filename: str):
        filepath = filename if filename.endswith(self.__EXTENSION) else filename + self.__EXTENSION
        self.__file_writer = FileWriter(filepath)
        self.__file_reader = FileReader(filepath)

    def write(self, hashmap: Cache):
        file_data = ""
        for key, value in hashmap.items():
            row = f"{key}={str(value)}\n"
            file_data += row
        self.__file_writer.write(file_data)

    def read(self, cache_type: CacheType, ttl_seconds: int, capacity: int, hash_func_type: HashFunctionType) -> (Cache, int):
        new_cache = None
        match cache_type:
            case CacheType.TTL:
                new_cache = TTLCache(ttl_seconds, capacity, hash_func_type=hash_func_type)
            case CacheType.LFU:
                new_cache = LFUCache(capacity, hash_func_type=hash_func_type)
            case CacheType.LRU:
                new_cache = LRUCache(capacity, hash_func_type=hash_func_type)

        file_content = self.__file_reader.read_lines()
        for line in file_content:
            key, value = line.strip().split('=')
            pair = KeyValue(key, value)
            new_cache.set(pair.key, pair.value)
        return new_cache, len(file_content)







