# Copyright (C) 2017 FireEye, Inc. All Rights Reserved.

import re
from typing import List, Iterable

from floss.results import StaticString, StringEncoding

ASCII_BYTE = br" !\"#\$%&\'\(\)\*\+,-\./0123456789:;<=>\?@ABCDEFGHIJKLMNOPQRSTUVWXYZ\[\]\^_`abcdefghijklmnopqrstuvwxyz\{\|\}\\\~\t"
ASCII_RE_4 = re.compile(br"([%s]{%d,})" % (ASCII_BYTE, 4))
UNICODE_RE_4 = re.compile(br"((?:[%s]\x00){%d,})" % (ASCII_BYTE, 4))
REPEATS = ["A", "\x00", "\xfe", "\xff"]
SLICE_SIZE = 4096


def buf_filled_with(buf, character):
    dupe_chunk = character * SLICE_SIZE
    for offset in range(0, len(buf), SLICE_SIZE):
        new_chunk = buf[offset : offset + SLICE_SIZE]
        if dupe_chunk[: len(new_chunk)] != new_chunk:
            return False
    return True


def extract_ascii_strings(buf, n=4) -> Iterable[StaticString]:
    """
    Extract ASCII strings from the given binary data.

    :param buf: A bytestring.
    :type buf: str
    :param n: The minimum length of strings to extract.
    :type n: int
    :rtype: Sequence[StaticString]
    """

    if not buf:
        return

    if (buf[0] in REPEATS) and buf_filled_with(buf, buf[0]):
        return

    r = None
    if n == 4:
        r = ASCII_RE_4
    else:
        reg = br"([%s]{%d,})" % (ASCII_BYTE, n)
        r = re.compile(reg)
    for match in r.finditer(buf):
        yield StaticString(match.group().decode("ascii"), offset=match.start(), encoding=StringEncoding.ASCII)


def extract_unicode_strings(buf, n=4) -> Iterable[StaticString]:
    """
    Extract naive UTF-16 strings from the given binary data.

    :param buf: A bytestring.
    :type buf: str
    :param n: The minimum length of strings to extract.
    :type n: int
    :rtype: Sequence[StaticString]
    """

    if not buf:
        return

    if (buf[0] in REPEATS) and buf_filled_with(buf, buf[0]):
        return

    if n == 4:
        r = UNICODE_RE_4
    else:
        reg = br"((?:[%s]\x00){%d,})" % (ASCII_BYTE, n)
        r = re.compile(reg)
    for match in r.finditer(buf):
        try:
            yield StaticString(match.group().decode("utf-16"), offset=match.start(), encoding=StringEncoding.UTF16LE)
        except UnicodeDecodeError:
            pass


def main():
    import sys

    with open(sys.argv[1], "rb") as f:
        b = f.read()

    for s in extract_ascii_strings(b):
        print("0x{:x}: {:s}".format(s.offset, s.string))

    for s in extract_unicode_strings(b):
        print("0x{:x}: {:s}".format(s.offset, s.string))


if __name__ == "__main__":
    main()
