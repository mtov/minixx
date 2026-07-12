class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._data = {}
        self._order = []

    def get(self, key, default=None):
        return self._data.get(key, default)

    def put(self, key, value):
        if key not in self._data and len(self._data) >= self.capacity:
            oldest = self._order.pop(0)
            del self._data[oldest]

        self._data[key] = value
        self._order.append(key)
