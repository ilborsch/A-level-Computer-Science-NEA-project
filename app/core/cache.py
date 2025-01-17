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
    Interface for a cache behaviour
    """
    @abstractmethod
    def get(self, key: Hashable) -> str:
        pass

    @abstractmethod
    def set(self, key: Hashable, value: Any):
        pass

    @abstractmethod
    def remove(self, key: Hashable):
        pass

    @abstractmethod
    def items(self):
        pass


class CacheFactory:
    @classmethod
    def initialise_cache(
            cls,
            cache_type: config.CacheType,
            ttl_seconds: int,
            capacity: int,
            hash_func_type: HashFunctionType
    ) -> Cache:
        match cache_type:
            case config.CacheType.TTL:
                return TTLCache(ttl_seconds, capacity, hash_func_type=hash_func_type)
            case config.CacheType.LRU:
                return LRUCache(capacity, hash_func_type=hash_func_type)
            case config.CacheType.LFU:
                return LFUCache(capacity, hash_func_type=hash_func_type)


class TTLValue:
    def __init__(self, ttl: float, value: str):
        self.__ttl = ttl
        self.__value = value

    @property
    def value(self):
        return self.__value

    @property
    def ttl(self):
        return self.__ttl

    def __str__(self):
        return self.__value


class TTLCache(Cache):
    def __init__(self, ttl_seconds: int, capacity: int, hash_func_type: HashFunctionType = None):
        self.__data: HashMap[str, TTLValue] = HashMap(size=capacity, hash_function_type=hash_func_type)
        self.__ttl_seconds = ttl_seconds
        self.__lock = threading.Lock()
        self.__cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        self.__cleanup_thread.start()

    def get(self, key) -> str:
        """Retrieve the value associated with the given key."""
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
        """Set the value for the given key with an optional time-to-live (TTL)."""
        with self.__lock:
            expire_time = time.time() + self.__ttl_seconds
            self.__data[key] = TTLValue(ttl=expire_time, value=value)

    def remove(self, key):
        """Remove the key-value pair associated with the given key."""
        with self.__lock:
            try:
                del self.__data[key]
            except (KeyError, TypeError):
                return

    def items(self):
        return iter(self.__data)

    def _cleanup(self):
        """Clean up the data by removing all key-value pairs."""
        while True:
            time.sleep(1)
            with self.__lock:
                keys_to_remove = [key for key, item in self.__data.items() if item.ttl and item.ttl <= time.time()]
                for key in keys_to_remove:
                    del self.__data[key]


class LRUCache(Cache):
    def __init__(self, capacity: int, hash_func_type: HashFunctionType = None):
        self.__capacity = capacity
        self.__data: HashMap[Hashable, Any] = HashMap(hash_function_type=hash_func_type)
        self.__order: deque[Hashable] = deque()
        self.__lock = threading.Lock()

    def get(self, key: Hashable) -> str:
        """Retrieve the value associated with the given key."""
        with self.__lock:
            try:
                value = self.__data[key]
                # Move the accessed key to the end to mark it as recently used
                self.__order.remove(key)
                self.__order.appendleft(key)
                return str(value)
            except (KeyError, TypeError):
                return ""

    def set(self, key: Hashable, value: Any) -> None:
        """Set the value for the given key."""
        with self.__lock:
            if key in self.__data:
                self.__order.remove(key)
            elif len(self.__data) >= self.__capacity:
                # Remove the least recently used key
                lru_key = self.__order.pop()
                del self.__data[lru_key]
            self.__data[key] = value
            self.__order.appendleft(key)

    def remove(self, key: Hashable) -> None:
        """Remove the key-value pair associated with the given key."""
        with self.__lock:
            try:
                del self.__data[key]
                self.__order.remove(key)
            except (KeyError, TypeError):
                return

    def items(self):
        return iter(self.__data)


class LFUCache(Cache):
    def __init__(self, capacity: int, hash_func_type: HashFunctionType = None):
        self.__capacity = capacity
        self.__data: HashMap[Hashable, Any] = HashMap(size=capacity, hash_function_type=hash_func_type)
        self.__freq: HashMap[Hashable, int] = HashMap(size=capacity, hash_function_type=hash_func_type)
        self.__freq_lists = defaultdict(list)
        self.__min_freq = 0
        self.__lock = threading.Lock()

    def get(self, key) -> str:
        """Retrieve the value associated with the given key."""
        with self.__lock:
            if key not in self.__data:
                return ""
            value = self.__data[key]
            self._update_frequency(key)
            return str(value)

    def set(self, key, value):
        """Set the value for the given key."""
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
        """Remove the key-value pair associated with the given key."""
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
        return iter(self.__data)

    def _update_frequency(self, key):
        """Update the frequency of the given key."""
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
        """Evict the least frequently used item."""
        lfu_keys = self.__freq_lists[self.__min_freq]
        key_to_evict = lfu_keys.pop(0)
        if not lfu_keys:
            del self.__freq_lists[self.__min_freq]

        del self.__data[key_to_evict]
        del self.__freq[key_to_evict]

