"""Tests for bookcrypt.parser."""

import io
import zipfile

import pytest

from bookcrypt.parser import _html_to_text, _strip_boilerplate, extract_words


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_epub(chapters: dict[str, str]) -> bytes:
    """Build a minimal in-memory EPUB zip with the given chapter HTML content.

    Args:
        chapters: Mapping of filename -> HTML string, in reading order.
    """
    buf = io.BytesIO()
    hrefs = list(chapters.keys())

    manifest_items = "\n".join(
        f'<item href="{href}" id="item{i}" media-type="application/xhtml+xml"/>'
        for i, href in enumerate(hrefs)
    )
    spine_items = "\n".join(
        f'<itemref idref="item{i}"/>' for i in range(len(hrefs))
    )
    opf = f"""<?xml version='1.0' encoding='UTF-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id">
  <metadata/>
  <manifest>
    {manifest_items}
  </manifest>
  <spine>
    {spine_items}
  </spine>
</package>"""

    container = """<?xml version='1.0' encoding='UTF-8'?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        for href, html in chapters.items():
            z.writestr(f"OEBPS/{href}", html)

    return buf.getvalue()


def _simple_html(body: str) -> str:
    return f"<html><body>{body}</body></html>"


# ---------------------------------------------------------------------------
# _html_to_text
# ---------------------------------------------------------------------------

class TestHtmlToText:
    def test_extracts_paragraph_text(self):
        html = b"<html><body><p>Hello world</p></body></html>"
        assert "Hello" in _html_to_text(html)
        assert "world" in _html_to_text(html)

    def test_strips_tags(self):
        html = b"<html><body><b>bold</b> <i>italic</i></body></html>"
        text = _html_to_text(html)
        assert "<b>" not in text
        assert "bold" in text
        assert "italic" in text

    def test_ignores_script_and_style(self):
        html = b"<html><body><script>var x=1;</script><p>real</p></body></html>"
        text = _html_to_text(html)
        assert "var" not in text
        assert "real" in text


# ---------------------------------------------------------------------------
# _strip_boilerplate
# ---------------------------------------------------------------------------

class TestStripBoilerplate:
    def test_removes_gutenberg_header(self):
        text = "junk *** START OF THE PROJECT GUTENBERG EBOOK MOBY DICK *** actual content"
        result = _strip_boilerplate(text)
        assert "junk" not in result
        assert "actual content" in result

    def test_removes_gutenberg_footer(self):
        text = "actual content *** END OF THE PROJECT GUTENBERG EBOOK MOBY DICK *** junk"
        result = _strip_boilerplate(text)
        assert "junk" not in result
        assert "actual content" in result

    def test_no_boilerplate_unchanged(self):
        text = "just some plain text with no markers"
        assert _strip_boilerplate(text) == text


# ---------------------------------------------------------------------------
# extract_words
# ---------------------------------------------------------------------------

class TestExtractWords:
    def test_returns_list_of_strings(self, tmp_path):
        epub_bytes = _make_epub({"ch1.html": _simple_html("<p>Hello world</p>")})
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(epub_bytes)
        words = extract_words(str(epub_path))
        assert isinstance(words, list)
        assert all(isinstance(w, str) for w in words)

    def test_words_are_lowercase(self, tmp_path):
        epub_bytes = _make_epub({"ch1.html": _simple_html("<p>Hello WORLD</p>")})
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(epub_bytes)
        words = extract_words(str(epub_path))
        assert all(w == w.lower() for w in words)

    def test_multiple_chapters_in_order(self, tmp_path):
        epub_bytes = _make_epub({
            "ch1.html": _simple_html("<p>alpha</p>"),
            "ch2.html": _simple_html("<p>beta</p>"),
        })
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(epub_bytes)
        words = extract_words(str(epub_path))
        assert words.index("alpha") < words.index("beta")

    def test_punctuation_stripped(self, tmp_path):
        epub_bytes = _make_epub({"ch1.html": _simple_html("<p>Hello, world!</p>")})
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(epub_bytes)
        words = extract_words(str(epub_path))
        assert "hello" in words
        assert "world" in words
        assert "," not in words
        assert "!" not in words

    def test_real_epub_returns_words(self):
        """Smoke test against the actual Moby Dick EPUB."""
        words = extract_words("moby_dick.epub")
        assert len(words) > 10_000
        assert "whale" in words
        assert "ishmael" in words
