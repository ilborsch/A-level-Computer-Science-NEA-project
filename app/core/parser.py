from enum import Enum
from config import HashFunctionType, CacheType

# ./app/core/parser.py


class InvalidCommandError(Exception):
    """
    Exception raised when an invalid command is encountered.
    """
    pass


class InvalidInputError(Exception):
    """
    Exception raised when the user input is invalid.
    """
    pass


class InvalidSetKey(Exception):
    """
    Exception raised when the key for SET_CONFIG is invalid.
    """
    pass


class InvalidSetValue(Exception):
    """
    Exception raised when the value for SET_CONFIG is invalid.
    """
    pass


class SetCommandKeys(Enum):
    """
    Enum representing valid keys for the SET_CONFIG operation.

    Attributes:
        CacheType (str): Key for cache type configuration.
        Username (str): Key for username configuration.
        Password (str): Key for password configuration.
        HashFunctionType (str): Key for hash function type configuration.
        StorageCapacity (str): Key for storage capacity configuration.
        TTLSeconds (str): Key for TTL (time-to-live) configuration.
    """
    CacheType = "cache_type"
    Username = "username"
    Password = "password"
    HashFunctionType = "hash_function"
    StorageCapacity = "storage_capacity"
    TTLSeconds = "ttl_seconds"


class Operation(Enum):
    """
    Enum representing supported operations for the parser.

    Attributes:
        GET (str): Retrieve a value.
        SET (str): Store a value.
        REMOVE (str): Remove a value.
        SET_CONFIG (str): Set configuration parameters.
        GET_CONFIG (str): Retrieve configuration details.
        EXIT (str): Exit the program.
    """
    GET = "GET"
    SET = "SET"
    REMOVE = "REMOVE"
    SET_CONFIG = "SET_CONFIG"
    GET_CONFIG = "CONFIG"
    EXIT = "EXIT"


class Operands:
    """
    Represents the operands (key and value) for a command.

    Attributes:
        key (str): The key operand.
        value (str): The value operand.
    """

    def __init__(self, key_operand: str, value_operand: str):
        """
        Initialize the operands with a key and a value.

        Args:
            key_operand (str): The key operand.
            value_operand (str): The value operand.
        """
        self.__key_operand = key_operand
        self.__value_operand = value_operand

    @property
    def key(self):
        """
        Get the key operand.

        Returns:
            str: The key operand.
        """
        return self.__key_operand

    @property
    def value(self):
        """
        Get the value operand.

        Returns:
            str: The value operand.
        """
        return self.__value_operand


class Command:
    """
    Represents a parsed command with an operation and operands.

    Attributes:
        operation (Operation): The operation type.
        operands (Operands): The operands for the command.
    """

    def __init__(self, operation: Operation = None, operands: Operands = None):
        """
        Initialize a Command instance.

        Args:
            operation (Operation, optional): The operation type.
            operands (Operands, optional): The operands for the command.
        """
        self.__operation = operation
        self.__operands = operands

    @property
    def operation(self):
        """
        Get the operation type.

        Returns:
            Operation: The operation type.
        """
        return self.__operation

    @property
    def operands(self):
        """
        Get the operands for the command.

        Returns:
            Operands: The operands.
        """
        return self.__operands


class Parser:
    """
    Parses user input into a Command object.

    Attributes:
        __MAX_KEY_LENGTH (int): Maximum allowed length for keys.
        __MAX_VALUE_LENGTH (int): Maximum allowed length for values.
    """

    __MAX_KEY_LENGTH = 150
    __MAX_VALUE_LENGTH = 200

    def parse(self, user_input: str) -> Command:
        """
        Parse user input into a Command object.

        Args:
            user_input (str): The user input string to parse.

        Returns:
            Command: The parsed command object.

        Raises:
            InvalidInputError: If the input is malformed.
            InvalidCommandError: If the command is not recognized.
            InvalidSetKey: If the key for SET_CONFIG is invalid.
            InvalidSetValue: If the value for SET_CONFIG is invalid.
            KeyError: If the key length exceeds the maximum allowed length.
            ValueError: If the value length exceeds the maximum allowed length.
        """
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
            raise ValueError(f"Value is too long {len(operands.value)}/{self.__MAX_VALUE_LENGTH}")

        command = Command(operation, operands)
        return command



