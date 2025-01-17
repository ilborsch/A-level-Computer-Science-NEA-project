from typing import Callable, Hashable, Any, Optional, Generic, TypeVar
from collections import namedtuple
from collections.abc import Hashable as HashableKey
from config import HashFunctionType


KeyValue = namedtuple('KeyValue', ['key', 'value'])
K = TypeVar('K', bound=Hashable)
V = TypeVar('V', bound=Any)


class HashMap(Generic[K, V]):
    def __init__(self, size: int = 100, hash_function_type: HashFunctionType = None) -> None:
        self.__size = size
        self.__pairs_amount = 0
        self.__table: list[list[KeyValue[Hashable, Any]]] = [[] for _ in range(size)]
        if hash_function_type is None:
            self.__hash_function = HashFunctionFactory.division_method
        else:
            self.__hash_function = HashFunctionFactory.get_hash_function(hash_function_type)

    @staticmethod
    def __check_key_hashable(key: Any) -> None:
        """
        Check if the key is hashable.

        Args:
            key (Any): The key to check.

        Raises:
            TypeError: If the key is not hashable.
        """
        if not isinstance(key, HashableKey):
            raise TypeError(f"Key {key} of type {key.__class__} is not Hashable")

    def get(self, key: Hashable) -> Optional[Any]:
        """
        Get the value associated with the key.

        Args:
            key (Hashable): The key to look up.

        Returns:
            Optional[Any]: The value associated with the key, or None if the key is not found.

        Raises:
            TypeError: If the key is not hashable.
        """
        self.__check_key_hashable(key)

        index = self.__hash_function(key, self.__size)
        for pair in self.__table[index]:
            if pair.key == key:
                return pair.value

    def insert(self, key: Hashable, value: Any) -> None:
        """
        Insert or update a key-value pair.

        Args:
            key (Hashable): The key to insert.
            value (Any): The value to insert.
        """
        self.__check_key_hashable(key)

        index = self.__hash_function(key, self.__size)
        if len(self.__table[index]) == 0:
            self.__table[index].append(KeyValue(key=key, value=value))
            self.__pairs_amount += 1
            return

        for i, pair in enumerate(self.__table[index]):
            if pair.key == key:
                self.__table[index][i] = KeyValue(key=key, value=value)
                self.__pairs_amount += 1
                return

        self.__table[index].append(KeyValue(key=key, value=value))
        self.__pairs_amount += 1

    def delete(self, key: Hashable) -> Optional[Any]:
        """
        Delete a key-value pair.

        Args:
            key (Hashable): The key to delete.

        Returns:
            Optional[Any]: The value associated with the key, or None if the key is not found.

        Raises:
            TypeError: If the key is not hashable.
        """
        self.__check_key_hashable(key)

        index = self.__hash_function(key, self.__size)
        for i, pair in enumerate(self.__table[index]):
            if pair.key == key:
                self.__table[index].pop(i)
                self.__pairs_amount -= 1
                return pair.value

    def __getitem__(self, key: Hashable) -> Any:
        """
        Get the value associated with the key using the indexing syntax.

        Args:
            key (Hashable): The key to look up.

        Returns:
            Any: The value associated with the key.

        Raises:
            KeyError: If the key is not found.
        """
        value = self.get(key)
        if value is None:
            raise KeyError(f"Invalid key {key}")
        return value

    def __setitem__(self, key: Hashable, value: Any) -> None:
        """
        Insert or update a key-value pair using the indexing syntax.

        Args:
            key (Hashable): The key to insert.
            value (Any): The value to insert.
        """
        self.insert(key, value)

    def __delitem__(self, key: Hashable) -> None:
        """
        Delete a key-value pair using the indexing syntax.

        Args:
            key (Hashable): The key to delete.
        """
        self.delete(key)

    def __contains__(self, key: Hashable) -> bool:
        """
        Check if the key exists in the hash map.

        Args:
            key (Hashable): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        try:
            value = self.get(key)
            return bool(value)
        except KeyError:
            return False

    def __iter__(self):
        for bucket in self.__table:
            for key_value in bucket:
                yield key_value

    def items(self):
        return iter(self)

    def __len__(self):
        return self.__pairs_amount


class HashFunctionFactory:
    @classmethod
    def get_hash_function(cls, hash_function_type: HashFunctionType) -> Callable[[K, int], int]:
        match hash_function_type:
            case HashFunctionType.Division:
                return cls.division_method
            case HashFunctionType.PythonHash:
                return cls.division_method
            case HashFunctionType.Multiplication:
                return cls.multiplication_method
            case HashFunctionType.MidSquareMethod:
                return cls.mid_square_method
            case HashFunctionType.FoldingMethod:
                return cls.folding_method
            case HashFunctionType.DJB2:
                return cls.djb2
        return cls.division_method

    @staticmethod
    def __string_to_numeric(key):
        return sum(ord(char) for char in key)

    @classmethod
    def division_method(cls, key: K, size: int) -> int:
        return hash(key) % size

    @classmethod
    def multiplication_method(cls, key: K, size: int) -> int:
        if isinstance(key, str):
            key = cls.__string_to_numeric(key)

        A = 0.61803398875
        fractional_part = (key * A) % 1
        return int(size * fractional_part)

    @classmethod
    def mid_square_method(cls, key: K, size: int) -> int:
        if isinstance(key, str):
            key = cls.__string_to_numeric(key)

        key_hash = hash(key)
        square = key_hash ** 2
        square_str = str(square)
        mid = len(square_str) // 2

        num_digits = len(str(size))
        start = max(0, mid - num_digits // 2)
        middle_digits = square_str[start:start + num_digits]

        return int(middle_digits) % size

    @classmethod
    def folding_method(cls, key: K, size: int) -> int:
        if isinstance(key, str):
            key = cls.__string_to_numeric(key)

        key_str = str(key)
        part_size = len(key_str) // 2
        parts = [int(key_str[i:i + part_size]) for i in range(0, len(key_str), part_size)]

        combined = sum(parts)
        return combined % size

    @classmethod
    def djb2(cls, key: K, size: int) -> int:
        if not isinstance(key, str):
            return cls.division_method(key, size)

        hash_value = 5381
        for char in key:
            hash_value = ((hash_value * 33) + ord(char)) % size
        return hash_value

