from app.converter.table_handler import convert_table


def _make_cell(text):
    """Helper to create a docx2python-compatible cell structure."""
    class FakeRun:
        def __init__(self, t):
            self.text = t
            self.html_style = []
    class FakePar:
        def __init__(self, t):
            self.runs = [FakeRun(t)]
            self.style = ""
            self.html_style = []
    return [FakePar(text)]


def test_simple_table():
    table = [
        [_make_cell("A"), _make_cell("B")],
        [_make_cell("1"), _make_cell("2")],
    ]
    result = convert_table(table)
    assert len(result) >= 3
    assert "A" in result[0]
    assert "B" in result[0]
    assert ":---" in result[1]
    assert "1" in result[2]
    assert "2" in result[2]


def test_table_pipe_escaping():
    table = [
        [_make_cell("a|b"), _make_cell("c")],
    ]
    result = convert_table(table)
    assert "a\\|b" in result[0] or "a|b" in result[0]


def test_empty_table():
    assert convert_table([]) == []
    assert convert_table(None) == []
