from src.lru_cache import LRUCache


def test_missing_key_returns_default():
    cache = LRUCache(2)
    assert cache.get("missing") is None
    assert cache.get("missing", "fallback") == "fallback"


def test_get_marks_key_as_recently_used():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)

    assert cache.get("a") == 1

    cache.put("c", 3)

    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_updating_existing_key_in_full_cache_does_not_evict_immediately():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)

    cache.put("a", 10)

    assert cache.get("a") == 10
    assert cache.get("b") == 2


def test_put_updates_existing_key_without_duplicate_order_entries():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("a", 10)
    cache.put("b", 2)
    cache.put("c", 3)

    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_eviction_uses_lru_order_after_updates():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    cache.put("c", 3)

    assert cache.get("a") == 10
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_capacity_one_keeps_only_the_most_recent_key():
    cache = LRUCache(1)
    cache.put("a", 1)
    cache.put("b", 2)

    assert cache.get("a") is None
    assert cache.get("b") == 2
