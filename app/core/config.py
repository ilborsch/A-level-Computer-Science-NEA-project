from dataclasses import dataclass, asdict
from enum import Enum
import yaml

# ./app/core/config.py


class CacheType(Enum):
    """
    Enum for different cache types.

    Attributes:
        TTL (str): Time-To-Live cache type.
        LRU (str): Least Recently Used cache type.
        LFU (str): Least Frequently Used cache type.
    """
    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"


class HashFunctionType(Enum):
    """
    Enum for different hash function types.

    Attributes:
        PythonHash (str): Default Python hash function.
        Division (str): Division hash function.
        Multiplication (str): Multiplication hash function.
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


@dataclass
class UserConfig:
    """
    Data class representing user configuration.

    Attributes:
        username (str): The username for the user.
        password (str): The password for the user.
    """
    username: str
    password: str


@dataclass
class CacheConfig:
    """
    Data class representing cache configuration.

    Attributes:
        type (CacheType): The type of cache (TTL, LRU, LFU).
        hash_function (HashFunctionType): The type of hash function to use.
        capacity (int): The maximum capacity of the cache.
        ttl_seconds (int): Time-to-live in seconds for TTL cache.
    """
    type: CacheType
    hash_function: HashFunctionType
    capacity: int
    ttl_seconds: int


@dataclass
class Config:
    """
    Data class representing the overall configuration.

    Attributes:
        user (UserConfig): User-specific configuration.
        cache (CacheConfig): Cache-specific configuration.
    """
    user: UserConfig
    cache: CacheConfig


def load_config(file_path: str) -> Config:
    """
    Load configuration from a YAML file.

    Args:
        file_path (str): The path to the YAML configuration file.

    Returns:
        Config: The configuration instance loaded from the file.
    """
    with open(file_path, 'r') as file:
        config_dict = yaml.safe_load(file)

    user_config = UserConfig(
        username=config_dict['user']['username'],
        password=config_dict['user']['password']
    )
    cache_config = CacheConfig(
        type=CacheType(config_dict['cache']['type']),
        hash_function=HashFunctionType(config_dict['cache']['hash_function']),
        capacity=int(config_dict['cache']['capacity']),
        ttl_seconds=int(config_dict['cache']['ttl_seconds'])
    )

    return Config(
        user=user_config,
        cache=cache_config,
    )


def save_config(config: Config, file_path: str):
    """
    Save a Config instance to a YAML file.

    Args:
        config (Config): The configuration instance to save.
        file_path (str): The path to the YAML file where the configuration will be saved.

    """
    config_dict = asdict(config)
    config_dict['cache']['type'] = config.cache.type.value
    config_dict['cache']['hash_function'] = config.cache.hash_function.value
    with open(file_path, 'w') as file:
        yaml.dump(config_dict, file, indent=2)
