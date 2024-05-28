from typing import Callable, Optional, Any

from ibmdata import LOG
#from app import LOG, cache


def get_cache_key_for(func: Callable, *args, **kwargs) -> Optional[str]:
    """
    Returns the cache key generated when calling func(*args, **kwargs) assuming func is a cached function.
    This does not actually run func, it only generates the key that would be generated *if* func was called
    elsewhere, so can be called before or after an actualy invocation of func.  If called before and the cache
    key does not exist a warning will be logged for awareness that the key is currently not valid (doesn't
    point to anything yet).  Returns None if func is not a cached function.
    """
    make_cache_key = getattr(func, "make_cache_key", None)
    if make_cache_key is None:
        LOG.warning(f"function {func.__name__} has no cache key method, are you sure it's cached?")
        return None

    key = make_cache_key(func, *args, **kwargs)
    if not cache.has(key):
        LOG.warning(f"cache key {key} for {func.__name__} does not currently exist")

    return key


def get_cached_value(key: str) -> Optional[Any]:
    """
    Given a cache key, retrieves the associated value.
    None is returned if the key or value are invalid or None.
    """
    if key and (data := cache.get(key)) is not None:
        return data
    LOG.warning(f"nothing found for cache key {key}, returning None")
    return None
