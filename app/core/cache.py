from abc import ABC, abstractmethod
from collections import defaultdict, deque
from hashing import HashMap
from typing import Hashable, Any
from config import HashFunctionType
import threading
import time
import config


class Cache(ABC):
    """
    An interface that defines the basic behavior of a Cache data structure.
    Acts as a parent abstract class for TTLCache, LRUCache, and LFUCache.
    """

    @abstractmethod
    def get(self, key: Hashable) -> str:
        """
        Retrieve the value associated with the given key.

        Args:
            key (Hashable): The key to retrieve the value for.

        Returns:
            str: The value associated with the key, or an empty string if the key does not exist.
        """
        pass

    @abstractmethod
    def set(self, key: Hashable, value: Any):
        """
        Add or update a key-value pair in the cache.

        Args:
            key (Hashable): The key to add or update.
            value (Any): The value to associate with the key.
        """
        pass

    @abstractmethod
    def remove(self, key: Hashable):
        """
        Remove a key-value pair from the cache.

        Args:
            key (Hashable): The key to remove.
        """
        pass

    @abstractmethod
    def items(self) -> list[tuple[Hashable, str]]:
        """
        Get all key-value pairs in the cache.

        Returns:
            list[tuple[Hashable, str]]: A list of tuples representing all key-value pairs in the cache.
        """
        pass


class CacheFactory:
    """
    A factory class for initializing different types of cache instances.
    """

    @classmethod
    def initialise_cache(
        cls,
        cache_type: config.CacheType,
        ttl_seconds: int,
        capacity: int,
        hash_func_type: HashFunctionType,
    ) -> Cache:
        """
        Factory method for creating a specific type of cache.

        Args:
            cache_type (config.CacheType): The type of cache to create (TTL, LRU, or LFU).
            ttl_seconds (int): The time-to-live in seconds for TTLCache.
            capacity (int): The maximum number of key-value pairs the cache can hold.
            hash_func_type (HashFunctionType): The type of hash function to use.

        Returns:
            Cache: An instance of the specified cache type.
        """
        match cache_type:
            case config.CacheType.TTL:
                return TTLCache(ttl_seconds, capacity, hash_func_type=hash_func_type)
            case config.CacheType.LRU:
                return LRUCache(capacity, hash_func_type=hash_func_type)
            case config.CacheType.LFU:
                return LFUCache(capacity, hash_func_type=hash_func_type)


class TTLValue:
    """
    Represents a value in TTLCache, with a value and a time-to-live (TTL) timestamp.
    """

    def __init__(self, ttl: float, value: str):
        """
        Initialize a TTLValue instance.

        Args:
            ttl (float): The expiration timestamp for the value.
            value (str): The value to store.
        """
        self.__ttl = ttl
        self.__value = value

    @property
    def value(self):
        """
        Get the stored value.

        Returns:
            str: The stored value.
        """
        return self.__value

    @property
    def ttl(self):
        """
        Get the time-to-live timestamp.

        Returns:
            float: The TTL timestamp.
        """
        return self.__ttl

    def __str__(self):
        """
        Get the string representation of the stored value.

        Returns:
            str: The stored value as a string.
        """
        return self.__value


class TTLCache(Cache):
    """
    A cache implementation with Time-To-Live (TTL) functionality.
    """

    def __init__(self, ttl_seconds: int, capacity: int, hash_func_type: HashFunctionType = None):
        """
        Initialize a TTLCache instance.

        Args:
            ttl_seconds (int): Time-to-live in seconds for each key-value pair.
            capacity (int): Maximum number of key-value pairs the cache can hold.
            hash_func_type (HashFunctionType, optional): Hash function type to use.
        """
        self.__data: HashMap[str, TTLValue] = HashMap(size=capacity, hash_function_type=hash_func_type)
        self.__ttl_seconds = ttl_seconds
        self.__lock = threading.Lock()
        self.__cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        self.__cleanup_thread.start()

    def get(self, key) -> str:
        """
        Retrieve the value associated with the given key.

        Args:
            key (Hashable): The key to retrieve the value for.

        Returns:
            str: The value if it exists and is valid; otherwise, an empty string.
        """
        with self.__lock:
            try:
                item = self.__data[key]
                if item.ttl is None or item.ttl > time.time():
                    return item.value
                else:
                    self.remove(key)
            except (KeyError, TypeError):
                return ""

    def set(self, key, value):
        """
        Set a value for the given key with an expiration time.

        Args:
            key (Hashable): The key to set.
            value (Any): The value to associate with the key.
        """
        with self.__lock:
            expire_time = time.time() + self.__ttl_seconds
            self.__data[key] = TTLValue(ttl=expire_time, value=value)

    def remove(self, key):
        """
        Remove a key-value pair from the cache.

        Args:
            key (Hashable): The key to remove.
        """
        with self.__lock:
            try:
                del self.__data[key]
            except (KeyError, TypeError):
                return

    def items(self):
        """
        Get all key-value pairs in the cache.

        Returns:
            Iterator: An iterator over all key-value pairs.
        """
        return iter(self.__data)

    def _cleanup(self):
        """
        Periodically remove expired key-value pairs from the cache.
        """
        while True:
            time.sleep(1)
            with self.__lock:
                keys_to_remove = [key for key, item in self.__data.items() if item.ttl and item.ttl <= time.time()]
                for key in keys_to_remove:
                    del self.__data[key]


class LRUCache(Cache):
    """
    A cache implementation with Least Recently Used (LRU) functionality.
    """

    def __init__(self, capacity: int, hash_func_type: HashFunctionType = None):
        """
        Initialize an LRUCache instance.

        Args:
            capacity (int): Maximum number of key-value pairs the cache can hold.
            hash_func_type (HashFunctionType, optional): Hash function type to use.
        """
        self.__capacity = capacity
        self.__data: HashMap[Hashable, Any] = HashMap(hash_function_type=hash_func_type)
        self.__order: deque[Hashable] = deque()
        self.__lock = threading.Lock()

    def get(self, key: Hashable) -> str:
        """
        Retrieve the value associated with the given key and mark it as recently used.

        Args:
            key (Hashable): The key to retrieve.

        Returns:
            str: The value if it exists; otherwise, an empty string.
        """
        with self.__lock:
            try:
                value = self.__data[key]
                self.__order.remove(key)
                self.__order.appendleft(key)
                return str(value)
            except (KeyError, TypeError):
                return ""

    def set(self, key: Hashable, value: Any) -> None:
        """
        Set a key-value pair in the cache.

        Args:
            key (Hashable): The key to set.
            value (Any): The value to associate with the key.
        """
        with self.__lock:
            if key in self.__data:
                self.__order.remove(key)
            elif len(self.__data) >= self.__capacity:
                lru_key = self.__order.pop()
                del self.__data[lru_key]
            self.__data[key] = value
            self.__order.appendleft(key)

    def remove(self, key: Hashable) -> None:
        """
        Remove a key-value pair from the cache.

        Args:
            key (Hashable): The key to remove.
        """
        with self.__lock:
            try:
                del self.__data[key]
                self.__order.remove(key)
            except (KeyError, TypeError):
                return

    def items(self):
        """
        Get all key-value pairs in the cache.

        Returns:
            Iterator: An iterator over all key-value pairs.
        """
        return iter(self.__data)


class LFUCache(Cache):
    """
    A cache implementation with Least Frequently Used (LFU) functionality.
    """

    def __init__(self, capacity: int, hash_func_type: HashFunctionType = None):
        """
        Initialize an LFUCache instance.

        Args:
            capacity (int): Maximum number of key-value pairs the cache can hold.
            hash_func_type (HashFunctionType, optional): Hash function type to use.
        """
        self.__capacity = capacity
        self.__data: HashMap[Hashable, Any] = HashMap(size=capacity, hash_function_type=hash_func_type)
        self.__freq: HashMap[Hashable, int] = HashMap(size=capacity, hash_function_type=hash_func_type)
        self.__freq_lists = defaultdict(list)
        self.__min_freq = 0
        self.__lock = threading.Lock()

    def get(self, key) -> str:
        """
        Retrieve the value associated with the given key and update its frequency.

        Args:
            key (Hashable): The key to retrieve.

        Returns:
            str: The value if it exists; otherwise, an empty string.
        """
        with self.__lock:
            if key not in self.__data:
                return ""
            value = self.__data[key]
            self._update_frequency(key)
            return str(value)

    def set(self, key, value):
        """
        Set a key-value pair in the cache and update its frequency.

        Args:
            key (Hashable): The key to set.
            value (Any): The value to associate with the key.
        """
        with self.__lock:
            if self.__capacity <= 0:
                return

            if key in self.__data:
                self.__data[key] = value
                self._update_frequency(key)
            else:
                if len(self.__data) >= self.__capacity:
                    self._evict()

                self.__data[key] = value
                self.__freq[key] = 1
                self.__freq_lists[1].append(key)
                self.__min_freq = 1

    def remove(self, key):
        """
        Remove a key-value pair from the cache.

        Args:
            key (Hashable): The key to remove.
        """
        with self.__lock:
            if key in self.__data:
                freq = self.__freq[key]
                self.__freq_lists[freq].remove(key)
                if not self.__freq_lists[freq]:
                    del self.__freq_lists[freq]
                    if self.__min_freq == freq:
                        self.__min_freq += 1

                del self.__data[key]
                del self.__freq[key]

    def items(self):
        """
        Get all key-value pairs in the cache.

        Returns:
            Iterator: An iterator over all key-value pairs.
        """
        return iter(self.__data)

    def _update_frequency(self, key):
        """
        Update the frequency of a key.

        Args:
            key (Hashable): The key to update the frequency for.
        """
        freq = self.__freq[key]
        self.__freq_lists[freq].remove(key)
        if not self.__freq_lists[freq]:
            del self.__freq_lists[freq]
            if self.__min_freq == freq:
                self.__min_freq += 1

        self.__freq[key] += 1
        new_freq = self.__freq[key]
        self.__freq_lists[new_freq].append(key)

    def _evict(self):
        """
        Evict the least frequently used key-value pair from the cache.
        """
        lfu_keys = self.__freq_lists[self.__min_freq]
        key_to_evict = lfu_keys.pop(0)
        if not lfu_keys:
            del self.__freq_lists[self.__min_freq]

        del self.__data[key_to_evict]
        del self.__freq[key_to_evict]
