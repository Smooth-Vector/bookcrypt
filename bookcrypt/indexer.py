"""Indexer: virtual pagination and word-to-page index construction."""

DEFAULT_PAGE_SIZE = 250  # words per virtual page (approx. standard paperback page)


def paginate(words: list[str], page_size: int = DEFAULT_PAGE_SIZE) -> list[list[str]]:
    """Split a word list into fixed-size virtual pages.

    Args:
        words: Ordered list of words (as returned by ``extract_words``).
        page_size: Number of words per page. Defaults to 250.

    Returns:
        List of pages, where each page is a list of words. Page numbers are
        1-based (index 0 in the returned list is page 1).
    """
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")
    return [words[i : i + page_size] for i in range(0, len(words), page_size)]


def build_index(pages: list[list[str]]) -> dict[str, list[int]]:
    """Build a word-to-page-numbers index from paginated content.

    Args:
        pages: List of pages as returned by ``paginate``. Page numbers are
            1-based (the first element corresponds to page 1).

    Returns:
        Dictionary mapping each unique word to a sorted list of 1-based page
        numbers on which it appears.

    Example::

        words = extract_words("moby_dick.epub")
        pages = paginate(words, page_size=250)
        index = build_index(pages)
        print(index["whale"])   # [3, 7, 12, ...]
    """
    index: dict[str, list[int]] = {}
    for page_num, page_words in enumerate(pages, start=1):
        seen_on_page: set[str] = set()
        for word in page_words:
            if word not in seen_on_page:
                index.setdefault(word, []).append(page_num)
                seen_on_page.add(word)
    return index
