from app.converter.style_mapper import StyleMapper, BlockContext


class TestStyleMapper:
    def setup_method(self):
        self.mapper = StyleMapper()

    def test_heading1(self):
        ctx = self.mapper.map("Heading 1")
        assert ctx.block_type == "heading"
        assert ctx.level == 1
        assert ctx.prefix == "# "

    def test_heading3(self):
        ctx = self.mapper.map("Heading 3")
        assert ctx.block_type == "heading"
        assert ctx.level == 3
        assert ctx.prefix == "### "

    def test_title(self):
        ctx = self.mapper.map("Title")
        assert ctx.block_type == "heading"
        assert ctx.level == 1

    def test_list_bullet(self):
        ctx = self.mapper.map("List Bullet")
        assert ctx.block_type == "list_item"
        assert ctx.prefix == "- "

    def test_list_number(self):
        ctx = self.mapper.map("List Number")
        assert ctx.block_type == "list_item"

    def test_blockquote(self):
        ctx = self.mapper.map("Block Text")
        assert ctx.block_type == "blockquote"
        assert ctx.prefix == "> "

    def test_code(self):
        ctx = self.mapper.map("Code")
        assert ctx.block_type == "code_block"

    def test_normal_paragraph(self):
        ctx = self.mapper.map("Normal")
        assert ctx.block_type == "paragraph"

    def test_empty_style_defaults_to_paragraph(self):
        ctx = self.mapper.map("")
        assert ctx.block_type == "paragraph"

    def test_unknown_style_defaults_to_paragraph(self):
        ctx = self.mapper.map("SomeUnknownStyle")
        assert ctx.block_type == "paragraph"

    def test_html_heading_fallback(self):
        ctx = self.mapper.map("UnknownStyle", html_style=["h2"])
        assert ctx.block_type == "heading"
        assert ctx.level == 2

    def test_toc_detection(self):
        assert self.mapper.is_toc_paragraph("TOC 1")
        assert self.mapper.is_toc_paragraph("TOC Heading")
        assert not self.mapper.is_toc_paragraph("Normal")

    def test_custom_style_map(self):
        custom = {"MyCustom": {"block_type": "heading", "level": 2, "prefix": "## "}}
        mapper = StyleMapper(custom)
        ctx = mapper.map("MyCustom")
        assert ctx.block_type == "heading"
        assert ctx.level == 2

    def test_heading_no_space(self):
        ctx = self.mapper.map("Heading1", html_style=["h1"])
        assert ctx.block_type == "heading"
        assert ctx.level == 1
