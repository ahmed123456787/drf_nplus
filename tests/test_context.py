from drf_nplus import context


def test_starts_empty():
    assert context.is_empty()
    assert context.current_path() is None


def test_push_and_reset_restore_state():
    token = context.push("PostSerializer")
    assert context.current_path() == "PostSerializer"

    inner = context.push("author")
    assert context.current_path() == "PostSerializer.author"

    context.reset(inner)
    assert context.current_path() == "PostSerializer"

    context.reset(token)
    assert context.is_empty()


def test_nested_pushes_join_with_dots():
    tokens = [context.push(seg) for seg in ("A", "b", "c")]
    try:
        assert context.current_path() == "A.b.c"
    finally:
        for t in reversed(tokens):
            context.reset(t)
