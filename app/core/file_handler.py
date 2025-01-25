from cache import Cache, LFUCache, LRUCache, TTLCache
from hashing import KeyValue
from config import CacheType, HashFunctionType
from pathlib import Path

# ./app/core/file_handler.py


class FileReader:
    """
    A class responsible for reading data from a file.
    """

    def __init__(self, filepath: str):
        """
        Initialize a FileReader instance.

        Args:
            filepath (str): The path of the file to read.
        """
        # dynamically resolve filepath of the file in /config folder.
        self.__filepath = filepath

    def read(self) -> str:
        """
        Read the entire content of the file as a string.

        Returns:
            str: The content of the file.
        """
        with open(self.__filepath, 'r') as file:
            return file.read()

    def read_lines(self) -> list[str]:
        """
        Read the content of the file as a list of lines.

        Returns:
            list[str]: A list of lines from the file.
        """
        with open(self.__filepath, 'r') as file:
            return file.readlines()


class FileWriter:
    """
    A class responsible for writing data to a file.
    """

    def __init__(self, filepath: str):
        """
        Initialize a FileWriter instance.

        Args:
            filepath (str): The path of the file to write to.
        """
        self.__filepath = filepath

    def write(self, data: str):
        """
        Write the given data to the file.

        Args:
            data (str): The data to write to the file.
        """
        with open(self.__filepath, 'w') as file:
            file.write(data)


class FileStorageHandler:
    """
    A class responsible for handling file-based storage operations, including writing and reading cache data.

    Attributes:
        __EXTENSION (str): The default file extension for cache storage files.
    """

    __EXTENSION = ".red"

    def __init__(self, filename: str):
        """
        Initialize a FileStorageHandler instance.

        Args:
            filename (str): The name of the storage file (with or without extension).
        """
        # dynamically resolve filepath of the file in the /config folder.
        filename = filename if filename.endswith(self.__EXTENSION) else filename + self.__EXTENSION
        filepath = str(Path(__file__).resolve().parent.parent.parent / filename)

        self.__file_writer = FileWriter(filepath)
        self.__file_reader = FileReader(filepath)

    def write(self, hashmap: Cache):
        """
        Write the contents of a cache (key-value pairs) to the storage file.

        Args:
            hashmap (Cache): The cache object containing key-value pairs to save.
        """
        file_data = ""
        for key, value in hashmap.items():
            row = f"{key}={str(value)}\n"
            file_data += row
        self.__file_writer.write(file_data)

    def read(self, cache_type: CacheType, ttl_seconds: int, capacity: int, hash_func_type: HashFunctionType) -> (Cache, int):
        """
        Read cache data from the storage file and initialize a cache instance.

        Args:
            cache_type (CacheType): The type of cache to initialize (TTL, LRU, LFU).
            ttl_seconds (int): The time-to-live value for TTL cache (ignored for other types).
            capacity (int): The maximum number of key-value pairs the cache can hold.
            hash_func_type (HashFunctionType): The type of hash function to use for the cache.

        Returns:
            tuple[Cache, int]: A tuple containing the initialized cache and the number of key-value pairs loaded.
        """
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

