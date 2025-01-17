import argparse
from database import Database
from parser import Operation
from pathlib import Path
import os


ASCII_LOGO = r"""
 ______     ______     _____     __     ______     __  __     ______    
/\  == \   /\  ___\   /\  __ \  /\ \   /\  ___\   /\ \/ /    /\  __ \   
\ \  __<   \ \  __\   \ \ \/\ \ \ \ \  \ \___  \  \ \  _"-.  \ \  __ \  
 \ \_\ \_\  \ \_____\  \ \____-  \ \_\  \/\_____\  \ \_\ \_\  \ \_\ \_\ 
  \/_/ /_/   \/_____/   \/____/   \/_/   \/_____/   \/_/\/_/   \/_/\/_/ 
"""


class CLI:
    def __init__(self):
        self.__database = Database('settings.yaml')
        self.__parser = argparse.ArgumentParser(description="Rediska CLI Tool")
        subparsers = self.__parser.add_subparsers(dest='command')
        subparsers.add_parser('docs', help='Show the documentation')
        subparsers.add_parser('start', help='Start in passive mode')
        subparsers.add_parser('interactive', help='Enter interactive mode')
        subparsers.add_parser('config', help='Show current settings')
        subparsers.add_parser('version', help='Show the current version')

    @staticmethod
    def show_docs():
        docs = """
===============================
        Rediska CLI           
===============================

  A simple and efficient CLI for cache management.

-------------------------------
|          Commands           |
-------------------------------
  rediska docs          : Display this documentation.
  rediska start         : Start in passive mode (connect via TCP or Python library).
  rediska interactive   : Enter interactive mode.
  rediska config        : Show current configuration settings.
  rediska version       : Display Rediska version.

-------------------------------
|   Interactive Mode Commands |
-------------------------------
  GET key               : Retrieve the value for a given key.
  SET key value         : Store a value for a given key.
  REMOVE key            : Remove a value associated with a given key.
  SET_CONFIG key value  : Update a configuration setting.
  CONFIG                : Display current configuration.
  EXIT                  : Exit interactive mode.

-------------------------------
|   SET_CONFIG Command Keys   |
-------------------------------

– "cache_type"
  Changes the cache type. Possible values:
    - "ttl": TTL Cache. Automatically removes pairs older than `ttl_seconds` (default: 900 seconds). (default)
    - "lru": LRU Cache. Removes least recently accessed items when capacity (default: 1000) is exceeded.
    - "lfu": LFU Cache. Removes least frequently accessed items when capacity (default: 1000) is exceeded.

– "username"  
  Change the username for authentication.

- "password"  
  Change the password for authentication.

- "hash_function"  
  Sets the hash function for key hashing. Options include:
    - "division" (default)  : Uses Python's `hash()` (also called the division method).
    - "py_hash"             : Python's `hash()` method.
    - "multiplication"      : Multiplication hash method.
    - "midsquare"           : Mid-Square hash method.
    - "folding"             : Folding hash method.
    - "djb2"                : DJB2 hashing algorithm.

- "storage_capacity"  
  Defines the cache's maximum capacity in pairs (default: 1000).

- "ttl_seconds"  
  Specifies the Time-To-Live for pairs in TTL Cache (default: 900 seconds).

===============================
"""
        print(docs)

    @staticmethod
    def show_version():
        path = str(Path(__file__).resolve().parent / 'config' / 'VERSION')
        with open(path, 'r') as file:
            print(f"\n\"Rediska\" software VERSION: {file.read()}")

    def show_config(self):
        config = self.__database.get_config()
        print(config)

    def interactive_mode(self):
        while True:
            try:
                user_input = input("rediska> ").strip()
                response = self.__database.parse_user_input(user_input)
                if response == Operation.EXIT.value:
                    exit(0)
                if response:
                    print(response)
            except KeyboardInterrupt:
                self.exit()
                break
            except Exception as e:
                print("ERROR -> ", e)

    def passive_start(self):
        print("Starting passive...")
        print("Now you can connect via the Python library or TCP connection (port 6379)")
        self.__database.start_tcp()

    def parse_arguments(self):
        return self.__parser.parse_args()

    def exit(self):
        print("Exiting...")
        self.__database.shutdown()


if __name__ == "__main__":
    print(ASCII_LOGO)
    print()

    cli = CLI()
    args = cli.parse_arguments()

    if args.command == 'docs':
        cli.show_docs()
    elif args.command == 'config':
        cli.show_config()
    elif args.command == 'version':
        cli.show_version()
    elif args.command == 'interactive':
        cli.interactive_mode()
    elif args.command == 'start' or args.command is None:
        cli.passive_start()
    else:
        cli.show_docs()

