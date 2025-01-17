from enum import Enum
from config import HashFunctionType, CacheType


class InvalidCommandError(Exception):
    pass


class InvalidInputError(Exception):
    pass


class InvalidSetKey(Exception):
    pass


class InvalidSetValue(Exception):
    pass


class SetCommandKeys(Enum):
    CacheType = "cache_type"
    Username = "username"
    Password = "password"
    HashFunctionType = "hash_function"
    StorageCapacity = "storage_capacity"
    TTLSeconds = "ttl_seconds"


class Operation(Enum):
    GET = "GET"
    SET = "SET"
    REMOVE = "REMOVE"
    SET_CONFIG = "SET_CONFIG"
    GET_CONFIG = "CONFIG"
    EXIT = "EXIT"


class Operands:
    def __init__(self, key_operand: str, value_operand: str):
        self.__key_operand = key_operand
        self.__value_operand = value_operand

    @property
    def key(self):
        return self.__key_operand

    @property
    def value(self):
        return self.__value_operand


class Command:
    def __init__(self, operation: Operation = None, operands: Operands = None):
        self.__operation = operation
        self.__operands = operands

    @property
    def operation(self):
        return self.__operation

    @property
    def operands(self):
        return self.__operands


class Parser:
    __MAX_KEY_LENGTH = 150
    __MAX_VALUE_LENGTH = 200

    def parse(self, user_input: str) -> Command:
        input_split = user_input.split(" ")

        if len(input_split) < 1:
            raise InvalidInputError("Invalid input.")

        command_str = input_split[0].upper()
        if command_str not in [operation.value for operation in Operation]:
            raise InvalidCommandError("Invalid command. Please, check documentation")

        operation = Operation(command_str)
        operands = Operands("", "")
        match operation:
            case Operation.SET_CONFIG:
                if len(input_split) != 3:
                    raise InvalidInputError("Invalid input. Should consist of 3 elements (command, key, value).")

                operands = Operands(input_split[1], input_split[2])
                set_command_keys = [key.value for key in SetCommandKeys]
                if operands.key not in set_command_keys:
                    raise InvalidSetKey("Invalid key for SET_CONFIG. Please, check documentation.")

                hash_function_types = [func_type.value for func_type in HashFunctionType]
                if operands.key == SetCommandKeys.HashFunctionType and operands.value not in hash_function_types:
                    raise InvalidSetValue("Invalid value for SET_CONFIG hash_function command.")

                cache_types = [cache_type.value for cache_type in CacheType]
                if operands.key == SetCommandKeys.CacheType and operands.value not in cache_types:
                    raise InvalidSetValue("Invalid value for SET_CONFIG cache_type command.")

            case Operation.SET:
                if len(input_split) != 3:
                    raise InvalidInputError("Invalid input. SET should consist of 3 elements (SET key value).")
                operands = Operands(input_split[1], input_split[2])

            case Operation.GET:
                if len(input_split) != 2:
                    raise InvalidInputError("Invalid input. GET should consist of 2 elements (GET key)")
                operands = Operands(input_split[1], "")

            case Operation.REMOVE:
                if len(input_split) != 2:
                    raise InvalidInputError("Invalid input. REMOVE should consist of 2 elements (REMOVE key)")
                operands = Operands(input_split[1], "")

        if len(operands.key) > self.__MAX_KEY_LENGTH:
            raise KeyError(f"Key is too long {len(operands.key)}/{self.__MAX_KEY_LENGTH}")

        if len(operands.value) > self.__MAX_VALUE_LENGTH:
            raise ValueError(f"Value if too long {len(operands.value)}/{self.__MAX_VALUE_LENGTH}")

        command = Command(operation, operands)
        return command









