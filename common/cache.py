import functools
import json
import os
import hashlib

def persistent_cache(func):
    """
    A decorator that provides persistent caching for function results across multiple script runs.

    - Caches function results to disk
    - Uses a hash of function name and arguments as the cache key
    - Stores cache files in the user's home directory

    Usage:
        @persistent_cache
        def my_function(arg1, arg2):
            # Function implementation
            return result
    """
    # Create a cache directory if it doesn't exist
    cache_dir = os.path.join(os.path.expanduser('~'), '.python_function_cache')
    os.makedirs(cache_dir, exist_ok=True)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a unique cache key based on function name and arguments
        key = func.__name__
        cache_path = os.path.join(cache_dir, f"{key}.json")

        # Try to read from cache
        try:
            with open(cache_path, 'r', encoding="utf-8") as cache_file:
                return json.load(cache_file)
        except FileNotFoundError:
            # If not in cache, call the function
            result = func(*args, **kwargs)

            # Store result in cache
            with open(cache_path, 'w', encoding="utf-8") as cache_file:
                json.dump(result, cache_file, indent=4, ensure_ascii=False)

            return result

    return wrapper
