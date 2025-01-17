import yaml
import os
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


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


@dataclass
class UserConfig:
    username: str
    password: str


@dataclass
class CacheConfig:
    type: CacheType
    hash_function: HashFunctionType
    capacity: int
    ttl_seconds: int


@dataclass
class Config:
    user: UserConfig
    cache: CacheConfig


def load_config(file_path: str) -> Config:
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
    """Save Config instance to a YAML file."""
    config_dict = asdict(config)
    config_dict['cache']['type'] = config.cache.type.value
    config_dict['cache']['hash_function'] = config.cache.hash_function.value
    with open(file_path, 'w') as file:
        yaml.dump(config_dict, file, indent=2)

