def merge_users(primary, secondary):
    users_by_id = {}
    for user in primary + secondary:
        users_by_id[user["id"]] = user
    return list(users_by_id.values())
