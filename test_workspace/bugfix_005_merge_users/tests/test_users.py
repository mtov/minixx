from src.users import merge_users

def test_preserves_primary_order():
    primary = [{"id": 2, "name": "B"}, {"id": 1, "name": "A"}]
    assert merge_users(primary, []) == primary

def test_secondary_new_users_are_appended():
    primary = [{"id": 1, "name": "A"}]
    secondary = [{"id": 2, "name": "B"}]
    assert merge_users(primary, secondary) == primary + secondary

def test_primary_wins_duplicates():
    primary = [{"id": 1, "name": "A"}]
    secondary = [{"id": 1, "name": "A2"}, {"id": 2, "name": "B"}]
    assert merge_users(primary, secondary) == [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
    ]
