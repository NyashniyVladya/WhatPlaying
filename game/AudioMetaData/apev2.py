# -*- coding: utf-8 -*-
"""
APEv2 parser.

@author: Vladya
"""

import re
import io
import struct
import codecs
from os import path
from . import (
    AudioTag,
    IMAGE_MIME_EXT,
    NotFindHeader,
    IncorrectTag
)


class APEv2(AudioTag):

    """

    APEv2 tags parser.

    Documentation:
        http://wiki.hydrogenaud.io/index.php?title=APEv2_specification


    APE header struct:

        1. Preamble:
            0x41, 0x50, 0x45, 0x54, 0x41, 0x47, 0x45, 0x58
        2. Version Number (32 bits)
        3. Tag Size (32 bits)
        4. Item Count (32 bits)
        5. Tags Flags (32 bits)
        6. Reserved (64 bits)



    """

    ITEM_TYPES = (
        "txt",
        "bin",
        "locator",
        "reserved"
    )

    LOGGER = AudioTag.LOGGER.getChild("APEv2")

    def __init__(self, audio, datatype="filePath", filename=None):

        super(APEv2, self).__init__(audio, datatype, filename)

        _start = None
        for APE_tag_header in re.finditer(
            r"\x41\x50\x45\x54\x41\x47\x45\x58.{16}\x00{8}",
            self._bytedata,
            re.DOTALL
        ):
            version_number, tag_size, item_count, tags_flags = struct.unpack(
                "<8x4I8x",
                APE_tag_header.group()
            )
            _contains_header = bool((tags_flags & (1 << 31)))
            _contains_footer = bool((tags_flags & (1 << 30)))
            _is_header = bool((tags_flags & (1 << 29)))
            _item_type = self.ITEM_TYPES[((tags_flags & 0b110) >> 1)]
            _read_only = bool((tags_flags & (1 << 0)))

            if (version_number == 2000) and _is_header:
                _start = APE_tag_header.end()
                break

        if _start is None:
            raise NotFindHeader("Not found APEv2 header.")

        if _item_type not in ("txt", "bin"):
            raise IncorrectTag("Not text or binary data.")

        self._tag_raw_data = self._bytedata[_start:(_start + tag_size)]
        self._item_count = item_count
        self._items = dict(self._get_items())

    def __getitem__(self, key):
        return self._items[key.upper()]

    def _get_items(self):

        with io.BytesIO(self._tag_raw_data) as tagFile:
            for _i in xrange(self._item_count):
                size, flags = struct.unpack("<2I", tagFile.read(8))
                item_key = ""
                while True:
                    _next_byte = tagFile.read(1)
                    if _next_byte == "\x00":
                        break
                    item_key += _next_byte
                value = tagFile.read(size)

                _item_type = self.ITEM_TYPES[((flags & 0b110) >> 1)]
                if _item_type not in ("txt", "bin"):
                    continue
                if _item_type == "txt":
                    try:
                        value = codecs.decode(value, "utf_8")
                    except UnicodeDecodeError:
                        continue
                yield (item_key.upper(), value)

    @property
    def title_tag(self):
        return self._items.get("TITLE", None)

    @property
    def artist_tag(self):
        return self._items.get("ARTIST", None)

    @property
    def album_tag(self):
        return self._items.get("ALBUM", None)

    @property
    def coveralbum_tag(self):
        key = "Cover Art (Front)".upper()
        if key in self._items:
            value = self._items[key]
            _filename, value = re.split("\x00", value, 1)
            _ext = path.splitext(_filename)[-1].lower()
            if _ext in IMAGE_MIME_EXT.itervalues():
                return (codecs.decode(_filename, "utf_8"), value)
        return None

    @property
    def date_tag(self):
        return self._items.get("YEAR", None)

    @property
    def genre_tag(self):
        return self._items.get("GENRE", None)
