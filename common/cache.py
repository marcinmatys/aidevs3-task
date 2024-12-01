import functools
import json
import os
import hashlib


def persistent_cache(filePath):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique cache key based on function name and arguments
            key = func.__name__

            script_dir = os.path.dirname(filePath)  # Directory of the script
            resource_dir = os.path.join(script_dir, 'resources')
            os.makedirs(resource_dir, exist_ok=True)

            cache_path = os.path.join(resource_dir, f"{key}.json")

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

    return decorator
