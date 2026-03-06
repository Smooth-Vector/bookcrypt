"""EPUB parser: extracts words in reading order from a Gutenberg EPUB file."""

import re
import zipfile
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

# Namespaces used in OPF/NCX files
_OPF_NS = "http://www.idpf.org/2007/opf"
_CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"

# Strip Gutenberg boilerplate between these sentinels
_PG_START = re.compile(r"\*{3}\s*START OF THE PROJECT GUTENBERG EBOOK[^*]+\*{3}", re.IGNORECASE)
_PG_END = re.compile(r"\*{3}\s*END OF THE PROJECT GUTENBERG EBOOK[^*]+\*{3}", re.IGNORECASE)

_WORD_RE = re.compile(r"[A-Za-z''\-]+")


def tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens, keeping apostrophes and hyphens.

    Args:
        text: Raw text string.

    Returns:
        Ordered list of lowercase word strings.
    """
    return [m.group().lower() for m in _WORD_RE.finditer(text)]


def _opf_path(epub: zipfile.ZipFile) -> str:
    """Return the path of the OPF package document from container.xml."""
    container = epub.read("META-INF/container.xml")
    root = ET.fromstring(container)
    rootfile = root.find(f".//{{{_CONTAINER_NS}}}rootfile")
    if rootfile is None:
        raise ValueError("container.xml has no rootfile element")
    path = rootfile.get("full-path")
    if not path:
        raise ValueError("rootfile element missing full-path attribute")
    return path


def _spine_hrefs(epub: zipfile.ZipFile, opf_path: str) -> list[str]:
    """Return content file paths in spine reading order."""
    opf_dir = opf_path.rsplit("/", 1)[0] + "/" if "/" in opf_path else ""
    root = ET.fromstring(epub.read(opf_path))

    # Build id -> href map from manifest
    manifest: dict[str, str] = {}
    for item in root.findall(f".//{{{_OPF_NS}}}item"):
        item_id = item.get("id")
        href = item.get("href")
        if item_id and href:
            manifest[item_id] = opf_dir + href

    # Follow spine order
    hrefs: list[str] = []
    for itemref in root.findall(f".//{{{_OPF_NS}}}itemref"):
        idref = itemref.get("idref")
        if idref and idref in manifest:
            hrefs.append(manifest[idref])
    return hrefs


def _html_to_text(html_bytes: bytes) -> str:
    """Extract plain text from an XHTML chapter, stripping all tags."""
    soup = BeautifulSoup(html_bytes, features="xml")
    # Remove script/style nodes
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ")


def _strip_boilerplate(text: str) -> str:
    """Remove Project Gutenberg header/footer boilerplate."""
    start = _PG_START.search(text)
    end = _PG_END.search(text)
    if start:
        text = text[start.end():]
    if end:
        end_match = _PG_END.search(text)
        if end_match:
            text = text[: end_match.start()]
    return text


def extract_words(epub_path: str) -> list[str]:
    """Extract all words from an EPUB file in spine reading order.

    Words are lowercased and limited to alphabetic tokens (including
    apostrophes and hyphens within words). Gutenberg boilerplate is removed.

    Args:
        epub_path: Path to the .epub file.

    Returns:
        Ordered list of lowercase word strings.
    """
    with zipfile.ZipFile(epub_path) as epub:
        opf = _opf_path(epub)
        hrefs = _spine_hrefs(epub, opf)

        chunks: list[str] = []
        for href in hrefs:
            try:
                raw = epub.read(href)
            except KeyError:
                continue
            chunks.append(_html_to_text(raw))

    full_text = " ".join(chunks)
    full_text = _strip_boilerplate(full_text)
    return tokenize(full_text)
