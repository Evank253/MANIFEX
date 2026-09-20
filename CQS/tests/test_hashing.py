from cqs.hashing import content_hash


def test_hash_is_deterministic():
    a = {"b": 2, "a": [1, 2]}
    assert content_hash(a) == content_hash({"a": [1, 2], "b": 2})
