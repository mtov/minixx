class TTLCache:
    def __init__(self, clock):
        self.clock = clock
        self._data = {}

    def set(self, key, value, ttl_seconds):
        self._data[key] = (value, self.clock() + ttl_seconds)

    def get(self, key, default=None):
        if key not in self._data:
            return default
        value, expires_at = self._data[key]
        if self.clock() <= expires_at:
            return value
        return default

    def __contains__(self, key):
        return key in self._data
