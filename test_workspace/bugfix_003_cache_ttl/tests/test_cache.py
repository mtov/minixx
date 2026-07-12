from src.cache import TTLCache

class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now

def test_value_before_expiration():
    clock = Clock()
    cache = TTLCache(clock)
    cache.set("a", 10, ttl_seconds=5)
    clock.now = 4
    assert cache.get("a") == 10

def test_value_at_expiration_is_expired():
    clock = Clock()
    cache = TTLCache(clock)
    cache.set("a", 10, ttl_seconds=5)
    clock.now = 5
    assert cache.get("a") is None

def test_expired_value_is_removed():
    clock = Clock()
    cache = TTLCache(clock)
    cache.set("a", 10, ttl_seconds=5)
    clock.now = 6
    assert cache.get("a") is None
    assert "a" not in cache
