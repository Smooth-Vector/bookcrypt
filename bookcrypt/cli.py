"""Command-line interface for bookcrypt."""

import argparse
import sys

from bookcrypt.encoder import build_position_index, decode, encode, format_encoded
from bookcrypt.indexer import paginate
from bookcrypt.parser import extract_words

DEFAULT_EPUB = "moby_dick.epub"


def _load_pages(epub: str, page_size: int) -> list[list[str]]:
    try:
        words = extract_words(epub)
    except FileNotFoundError:
        print(f"error: EPUB not found: {epub}", file=sys.stderr)
        sys.exit(1)
    return paginate(words, page_size=page_size)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bookcrypt",
        description="Book cipher encoder/decoder using Moby Dick.",
    )
    parser.add_argument(
        "--epub",
        default=DEFAULT_EPUB,
        metavar="PATH",
        help=f"Path to the EPUB file (default: {DEFAULT_EPUB})",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=250,
        metavar="N",
        help="Words per virtual page (default: 250)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    enc = subparsers.add_parser("encode", help="Encode a message to coordinates.")
    enc.add_argument("message", help="Plain-text sentence to encode.")

    dec = subparsers.add_parser("decode", help="Decode coordinates back to a message.")
    dec.add_argument("coordinates", help='Coordinate string, e.g. "15 76 6 215 18 44".')

    args = parser.parse_args()
    pages = _load_pages(args.epub, args.page_size)

    if args.command == "encode":
        index = build_position_index(pages)
        try:
            coords = encode(args.message, index)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        print(format_encoded(coords))

    elif args.command == "decode":
        try:
            sentence = decode(args.coordinates, pages)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        print(sentence)


if __name__ == "__main__":
    main()
