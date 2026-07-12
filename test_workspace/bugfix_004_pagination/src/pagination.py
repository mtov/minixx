def paginate(items, page: int, per_page: int):
    start = page * per_page
    end = start + per_page
    return list(items[start:end])
