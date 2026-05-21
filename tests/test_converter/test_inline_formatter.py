from app.converter.inline_formatter import format_run, format_par_runs, replace_image_placeholders


class TestFormatRun:
    def test_bold(self):
        assert format_run("hello", ["b"]) == "**hello**"

    def test_italic(self):
        assert format_run("hello", ["i"]) == "*hello*"

    def test_bold_italic(self):
        assert format_run("hello", ["b", "i"]) == "***hello***"

    def test_underline(self):
        assert format_run("hello", ["u"]) == "<u>hello</u>"

    def test_strikethrough(self):
        assert format_run("hello", ["s"]) == "~~hello~~"

    def test_superscript(self):
        assert format_run("hello", ["sup"]) == "^hello^"

    def test_subscript(self):
        assert format_run("hello", ["sub"]) == "~hello~"

    def test_code(self):
        assert format_run("hello", ["code"]) == "`hello`"

    def test_empty_text(self):
        assert format_run("", ["b"]) == ""

    def test_heading_tags_skipped(self):
        assert format_run("Hello", ["h1"]) == "Hello"
        assert format_run("Hello", ["h2"]) == "Hello"

    def test_html_entities(self):
        assert format_run("a <b> b", ["i"]) == "*a <b> b*"


class TestReplaceImagePlaceholders:
    def test_single(self):
        assert replace_image_placeholders(
            "Text ----img1.png---- end",
            {"img1.png": "images/img1.png"}
        ) == "Text ![img1](images/img1.png) end"

    def test_multiple(self):
        result = replace_image_placeholders(
            "----a.jpg---- and ----b.jpg----",
            {"a.jpg": "images/a.jpg", "b.jpg": "images/b.jpg"}
        )
        assert "![a](images/a.jpg)" in result
        assert "![b](images/b.jpg)" in result

    def test_no_match(self):
        assert replace_image_placeholders("text", {}) == "text"
