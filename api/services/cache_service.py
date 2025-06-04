from cachetools import TTLCache
from typing import Callable

class CacheService:
    def __init__(self):
        self.caches = {
            "approvals": TTLCache(maxsize=400, ttl=300),
            "comments": TTLCache(maxsize=400, ttl=300),
            "ldap_users": TTLCache(maxsize=200, ttl=300),
        }
        
    def get(self, namespace: str, key: str):
        cache = self.caches.get(namespace)
        if cache is None:
            return None
        return cache.get(key)
    
    def set(self, namespace: str, key: str, value):
        cache = self.caches.get(namespace)
        if cache is None:
            return
        cache[key] = value
        
    def get_or_set(self, namespace: str, key:str, compute_func: Callable):
        cache = self.caches.get(namespace)
        if cache is None:
            return compute_func()
        
        if key in cache:
            return cache[key]
        
        else:
            value = compute_func()
            cache[key] = value
            return value
        
cache_service = CacheService()
            
        
        
