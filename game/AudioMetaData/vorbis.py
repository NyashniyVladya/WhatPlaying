# -*- coding: utf-8 -*-
"""
Vorbis/OpusTags parser.

@author: Vladya
"""

import re
import io
import struct
import codecs
import base64
from . import (
    id3,
    AudioTag,
    IMAGE_MIME_EXT,
    IncorrectTag,
    NotFindHeader
)


class SkipComment(Exception):
    pass


class VorbisComment(AudioTag):

    """
    Vorbis/OpusTags comment parser.

    Documentation:
        https://www.xiph.org/vorbis/doc/Vorbis_I_spec.html#x1-620004.2.1
        https://www.xiph.org/vorbis/doc/Vorbis_I_spec.html#x1-850005.2.1
        https://tools.ietf.org/html/rfc7845#section-5.2


    VORBIS comment header ID:
        1) [packet_type] :
               8 bit value
        2) 0x76, 0x6f, 0x72, 0x62, 0x69, 0x73:
               the characters "vorbis" as six octets

   OpusTags comment header ID:
        1) 0x4f, 0x70, 0x75, 0x73, 0x54, 0x61, 0x67, 0x73:
               the characters "OpusTags" as eight octets


    How read comment header (copypast from docs):
        1) [vendor length]:
               read an unsigned integer of 32 bits
        2) [vendor string]:
               read a UTF-8 vector as [vendor length] octets
        3) [user comment list length]:
               read an unsigned integer of 32 bits
        4) iterate [user comment list length] times {
        5)     [length]:
                   read an unsigned integer of 32 bits
        6)     this iteration’s user comment:
                   read a UTF-8 vector as [length] octets
           }
        7) [framing bit]:
               read a single bit as boolean
        VORBIS only:
            8) if ( [framing bit] unset or end-of-packet ) then ERROR
        9) done.

    """

    LOGGER = AudioTag.LOGGER.getChild("VorbisComment")

    def __init__(self, audio, datatype="filePath", filename=None):

        super(VorbisComment, self).__init__(audio, datatype, filename)

        _start_comments = _end_comments = None
        for _data in re.finditer(r".\x76\x6f\x72\x62\x69\x73", self._bytedata):
            data = _data.group()
            packet_type = ord(data[0])
            if packet_type == 0x03:  # Vorbis comment type.
                _start_comments = _data.end()
            elif packet_type == 0x05:  # Setup type. End of the comment block.
                _end_comments = _data.start()

        if _start_comments and _end_comments:
            if _end_comments <= _start_comments:
                raise IncorrectTag("Wrong headers order.")
            self.VORBISTYPE = "vorbis"
            self._comments_raw_data = self._cut_pages(
                self._bytedata[_start_comments:_end_comments]
            )
        else:
            opus_tags = re.search(
                r"\x4f\x70\x75\x73\x54\x61\x67\x73",
                self._bytedata
            )
            if not opus_tags:
                raise NotFindHeader("Not found vorbis headers.")
            self.VORBISTYPE = "OpusTags"
            self._comments_raw_data = self._cut_pages(
                self._bytedata[opus_tags.end():]
            )

        self._comments = self._get_comments_dict()
        if not self._comments:
            raise IncorrectTag("Not found vorbis comments.")

    def __getattr__(self, key):
        if ("_comments" in self.__dict__) and (key.upper() in self._comments):
            return self._comments[key.upper()]
        raise AttributeError(key)

    def _get_basic_tag(self, name):
        result = getattr(self, name, None)
        if result:
            if name == "METADATA_BLOCK_PICTURE":
                return result[0]
            return u" / ".join(result)
        return None

    @property
    def title_tag(self):
        return self._get_basic_tag("TITLE")

    @property
    def artist_tag(self):
        return self._get_basic_tag("ARTIST")

    @property
    def album_tag(self):
        return self._get_basic_tag("ALBUM")

    @property
    def coveralbum_tag(self):
        return self._get_basic_tag("METADATA_BLOCK_PICTURE")

    @property
    def date_tag(self):
        return self._get_basic_tag("DATE")

    @property
    def genre_tag(self):
        return self._get_basic_tag("GENRE")

    def _get_comments_dict(self):

        comments = {}
        for name, value in self._get_comments():
            comments.setdefault(name, set()).add(value)
        return dict(map(lambda x: (x[0], tuple(x[1])), comments.iteritems()))

    @staticmethod
    def _unsigned_int(bytedata, little_endian=True):
        """
        Unpack unsigned integer value to "python int" from byte data.
        """
        read_format = "{0}I".format(('<' if little_endian else '>'))
        return struct.unpack(read_format, bytedata)[0]

    @staticmethod
    def _cut_pages(data):

        """
        Documentation:
            https://www.xiph.org/vorbis/doc/framing.html
        """

        if not isinstance(data, bytes):
            raise Exception("Wrong type {0}.".format(type(data)))

        while True:

            match = re.search(
                r"\x4f\x67\x67\x53.{22}[\x00-\xff]",
                data,
                re.DOTALL
            )
            if not match:
                return data
            page_segments = ord(match.group()[-1])

            _start = match.start()
            _end = match.end() + page_segments
            data = data[:_start] + data[_end:]

    def _get_comments(self):

        with io.BytesIO(self._comments_raw_data) as audioFile:

            vendor_length = self._unsigned_int(audioFile.read(4))

            vendor_string = codecs.decode(
                audioFile.read(vendor_length),
                "utf_8"
            )
            if vendor_string:
                yield ("VENDOR", vendor_string)

            user_comment_list_length = self._unsigned_int(audioFile.read(4))

            for i in xrange(user_comment_list_length):

                comment_length = self._unsigned_int(audioFile.read(4))
                comment_data = audioFile.read(comment_length)
                if comment_length != len(comment_data):
                    self.LOGGER.exception(
                        "Wrong comment length. Should be %d. There is %d.",
                        comment_length,
                        len(comment_data)
                    )
                    continue
                try:
                    comment_name, value = self.parse_comment(comment_data)
                except SkipComment as ex:
                    self.LOGGER.debug(ex.message)
                    continue
                except Exception as ex:
                    self.LOGGER.exception(
                        "An error occurred while parsing %d comment.\n%s",
                        (i + 1),
                        ex.message
                    )
                else:
                    yield (comment_name, value)
            if self.VORBISTYPE == "vorbis":
                framing_bit = struct.unpack('?', audioFile.read(1))[0]
                if not framing_bit:
                    raise IncorrectTag("Incorrect tag.")

    @classmethod
    def parse_comment(cls, bytedata):

        if "\x3d" not in bytedata:
            raise SkipComment(bytedata)

        name, value = re.split(r"\x3d", bytedata, 1)
        name = name.upper()
        if name == "METADATA_BLOCK_PICTURE":
            value = cls._parse_image_comment(value)
        else:
            value = codecs.decode(value, "utf_8")

        return (name, value)

    @classmethod
    def _parse_image_comment(cls, vorbis_picture_bytedata):

        """
        Documentation:
            https://wiki.xiph.org/VorbisComment#METADATA_BLOCK_PICTURE
            https://xiph.org/flac/format.html#metadata_block_picture

        Important:
            Unlike the "Vorbis" integer, where used LE byte order,
            in this comment, integers should be read as BE.
        """

        vorbis_picture_bytedata = base64.b64decode(
            vorbis_picture_bytedata
        )
        with io.BytesIO(vorbis_picture_bytedata) as image:

            picture_type = id3.APIC_TYPES[
                cls._unsigned_int(image.read(4), False)
            ]

            MIME_type_length = cls._unsigned_int(image.read(4), False)
            MIME_type = image.read(MIME_type_length)

            description_length = cls._unsigned_int(image.read(4), False)
            description = codecs.decode(
                image.read(description_length),
                "utf_8"
            )

            width = cls._unsigned_int(image.read(4), False)
            height = cls._unsigned_int(image.read(4), False)
            color_depth = cls._unsigned_int(image.read(4), False)
            colors = cls._unsigned_int(image.read(4), False)

            imagedata_length = cls._unsigned_int(image.read(4), False)

            imagedata = image.read(imagedata_length)

            if imagedata_length != len(imagedata):
                raise SkipComment(
                    "Wrong image length. Should be {0}. There is {1}.".format(
                        imagedata_length,
                        len(imagedata)
                    )
                )

            _filename = picture_type + IMAGE_MIME_EXT.get(MIME_type, ".jpg")
            return (_filename, imagedata)
