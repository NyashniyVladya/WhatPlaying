# -*- coding: utf-8 -*-
"""
ID3 Parsers.

@author: Vladya
"""

import re
import io
import zlib
import codecs
from . import (
    AudioTag,
    ID3V1GENRES,
    IMAGE_MIME_EXT,
    IncorrectTag,
    NotFindHeader
)


_FRAME_DECLARATION = {
    2: {
        "IPL": "Involved people list",
        "PIC": "Attached picture",
        "TAL": "Album/Movie/Show title",
        "TBP": "BPM (Beats Per Minute)",
        "TCM": "Composer",
        "TCO": "Content type",
        "TCR": "Copyright message",
        "TDA": "Date",
        "TDY": "Playlist delay",
        "TEN": "Encoded by",
        "TFT": "File type",
        "TIM": "Time",
        "TKE": "Initial key",
        "TLA": "Language(s)",
        "TLE": "Length",
        "TMT": "Media type",
        "TOA": "Original artist(s)/performer(s)",
        "TOF": "Original filename",
        "TOL": "Original Lyricist(s)/text writer(s)",
        "TOR": "Original release year",
        "TOT": "Original album/Movie/Show title",
        "TP1": "Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group",
        "TP2": "Band/Orchestra/Accompaniment",
        "TP3": "Conductor/Performer refinement",
        "TP4": "Interpreted, remixed, or otherwise modified by",
        "TPA": "Part of a set",
        "TPB": "Publisher",
        "TRC": "ISRC (International Standard Recording Code)",
        "TRD": "Recording dates",
        "TRK": "Track number/Position in set",
        "TSI": "Size",
        "TSS": "Software/hardware and settings used for encoding",
        "TT1": "Content group description",
        "TT2": "Title/Songname/Content description",
        "TT3": "Subtitle/Description refinement",
        "TXT": "Lyricist/text writer",
        "TXX": "User defined text information frame",
        "TYE": "Year",
        "WAF": "Official audio file webpage",
        "WAR": "Official artist/performer webpage",
        "WAS": "Official audio source webpage",
        "WCM": "Commercial information",
        "WCP": "Copyright/Legal information",
        "WPB": "Publishers official webpage",
        "WXX": "User defined URL link frame"
    },
    3: {
        "APIC": "Attached picture",
        "IPLS": "Involved people list",
        "TALB": "Album/Movie/Show title",
        "TBPM": "BPM (beats per minute)",
        "TCOM": "Composer",
        "TCON": "Content type",
        "TCOP": "Copyright message",
        "TDAT": "Date",
        "TDEN": "Encoding time",
        "TDLY": "Playlist delay",
        "TDOR": "Original release time",
        "TDRC": "Recording time",
        "TDRL": "Release time",
        "TDTG": "Tagging time",
        "TENC": "Encoded by",
        "TEXT": "Lyricist/Text writer",
        "TFLT": "File type",
        "TIME": "Time",
        "TIPL": "Involved people list",
        "TIT1": "Content group description",
        "TIT2": "Title/songname/content description",
        "TIT3": "Subtitle/Description refinement",
        "TKEY": "Initial key",
        "TLAN": "Language(s)",
        "TLEN": "Length",
        "TMCL": "Musician credits list",
        "TMED": "Media type",
        "TMOO": "Mood",
        "TOAL": "Original album/movie/show title",
        "TOFN": "Original filename",
        "TOLY": "Original lyricist(s)/text writer(s)",
        "TOPE": "Original artist(s)/performer(s)",
        "TORY": "Original release year",
        "TOWN": "File owner/licensee",
        "TPE1": "Lead performer(s)/Soloist(s)",
        "TPE2": "Band/orchestra/accompaniment",
        "TPE3": "Conductor/performer refinement",
        "TPE4": "Interpreted, remixed, or otherwise modified by",
        "TPOS": "Part of a set",
        "TPRO": "Produced notice",
        "TPUB": "Publisher",
        "TRCK": "Track number/Position in set",
        "TRDA": "Recording dates",
        "TRSN": "Internet radio station name",
        "TRSO": "Internet radio station owner",
        "TSIZ": "Size",
        "TSOA": "Album sort order",
        "TSOP": "Performer sort order",
        "TSOT": "Title sort order",
        "TSRC": "ISRC (international standard recording code)",
        "TSSE": "Software/Hardware and settings used for encoding",
        "TSST": "Set subtitle",
        "TXXX": "User defined text information frame",
        "TYER": "Year",
        "WCOM": "Commercial information",
        "WCOP": "Copyright/Legal information",
        "WOAF": "Official audio file webpage",
        "WOAR": "Official artist/performer webpage",
        "WOAS": "Official audio source webpage",
        "WORS": "Official internet radio station homepage",
        "WPAY": "Payment",
        "WPUB": "Publishers official webpage",
        "WXXX": "User defined URL link frame"
    }
}
_FRAME_DECLARATION[4] = _FRAME_DECLARATION[3].copy()

_MORE_THAN_ONE = (
    "TXX",
    "TXXX",
    "WAR",
    "WCM",
    "WCOM",
    "WOAR",
    "WXX",
    "WXXX"
)

BASIC_METADATA = {
    2: {
        "album": ("TAL", "TOT"),
        "artist": (
            "TP1",
            "TP2",
            "TP3",
            "TOA",
            "TP4",
            "TCM",
            "TXT",
            "TOL",
            "IPL"
        ),
        "coveralbum": ("PIC",),
        "date": ("TYE", "TRD"),
        "genre": ("TCO",),
        "title": ("TT2", "TOF")
    },
    3: {
        "album": ("TALB", "TOAL"),
        "artist": (
            "TPE1",
            "TPE2",
            "TPE3",
            "TOPE",
            "TPE4",
            "TCOM",
            "TEXT",
            "TOLY",
            "TIPL",
            "IPLS"
        ),
        "coveralbum": ("APIC",),
        "date": ("TDRL", "TDRC", "TDOR"),
        "genre": ("TCON",),
        "title": ("TIT2", "TOFN")
    }
}
BASIC_METADATA[4] = BASIC_METADATA[3].copy()


APIC_TYPES = {
    0x00: "Other",
    0x01: "32x32 pixels 'file icon' (PNG only)",
    0x02: "Other file icon",
    0x03: "Cover (front)",
    0x04: "Cover (back)",
    0x05: "Leaflet page",
    0x06: "Media (e.g. lable side of CD)",
    0x07: "Lead artist/lead performer/soloist",
    0x08: "Artist/performer",
    0x09: "Conductor",
    0x0a: "Band/Orchestra",
    0x0b: "Composer",
    0x0c: "Lyricist/text writer",
    0x0d: "Recording Location",
    0x0e: "During recording",
    0x0f: "During performance",
    0x10: "Movie/video screen capture",
    0x11: "A bright coloured fish",
    0x12: "Illustration",
    0x13: "Band/artist logotype",
    0x14: "Publisher/Studio logotype"
}


class SkipFrame(Exception):
    pass


class ID3V1(AudioTag):

    """
    ID3V1.0-1.1 tag parser.

    Documentation:
        https://id3.org/ID3v1

    0..2       'TAG' (3 Bytes)
    3..32      Song Name (30 bytes)
    33..62     Artist (30 Bytes)
    63..92     Album Name (30 Bytes)
    93..96     Year (4 Bytes)
    97..126    Comment (30 Bytes) (or 28, if 1.1 ver.)
    127        1 Byte Song Genre Identifier

    """

    LOGGER = AudioTag.LOGGER.getChild("ID3V1")

    def __init__(self, audio, datatype="filePath", filename=None):

        super(ID3V1, self).__init__(audio, datatype, filename)

        with io.BytesIO(self._bytedata[-128:]) as tag:

            TAG = tag.read(3)
            if TAG != "TAG":
                raise NotFindHeader("Not detected ID3V1 header.")

            self.song_name = codecs.decode(
                tag.read(30).strip("\x00"),
                "latin_1"
            )

            self.artist = codecs.decode(
                tag.read(30).strip("\x00"),
                "latin_1"
            )

            self.album_name = codecs.decode(
                tag.read(30).strip("\x00"),
                "latin_1"
            )

            self.year = codecs.decode(
                tag.read(4).strip("\x00"),
                "latin_1"
            )

            self.comment = tag.read(30)
            if (self.comment[-2] == "\x00") and (self.comment[-1] != "\x00"):
                self.VERSION = (1, 1)
                self.album_track = ord(self.comment[-1])
                self.comment = codecs.decode(
                    self.comment[:-2].strip("\x00"),
                    "latin_1"
                )
            else:
                self.VERSION = (1, 0)
                self.album_track = None
                self.comment = codecs.decode(
                    self.comment.strip("\x00"),
                    "latin_1"
                )
            try:
                self.genre = ID3V1GENRES[ord(tag.read(1))]
            except IndexError:
                self.genre = ID3V1GENRES[12]  # Tag "other"

    @property
    def title_tag(self):
        return (self.song_name or None)

    @property
    def artist_tag(self):
        return (self.artist or None)

    @property
    def album_tag(self):
        return (self.album_name or None)

    @property
    def coveralbum_tag(self):
        return None

    @property
    def date_tag(self):
        return (self.year or None)

    @property
    def genre_tag(self):
        return self.genre


class ID3V2(AudioTag):

    """

    ID3V2.2.0-2.4.0 tag parser.

    Documentation:
        https://id3.org/id3v2-00
        https://id3.org/id3v2.3.0
        https://id3.org/id3v2.4.0-structure
        https://id3.org/id3v2.4.0-frames


    Struct of general header:

    identifier    "ID3"
    version       $0x 00
    flags         %xxxx0000
    size          4 * %0xxxxxxx



    Struct of frame header (2.2.0):

    frame ID      $xx xx xx  (three characters)
    size          $xx xx xx


    Struct of frame header (2.3.0):

    frame ID      $xx xx xx xx  (four characters)
    size          $xx xx xx xx
    flags         $xx xx


    Struct of frame header (2.4.0):

    frame ID      $xx xx xx xx  (four characters)
    size          4 * %0xxxxxxx (synchsafe integer)
    flags         $xx xx

    """

    LOGGER = AudioTag.LOGGER.getChild("ID3V2")

    HEADER = re.compile(
        r"\x49\x44\x33[\x00-\xfe]{2}[\x00-\xff][\x00-\x7f]{4}"
    )
    FLAGS_INFO = {
        "UNSYNCHRONISATION_FLAG": {
            2: 0b10000000,
            3: 0b10000000,
            4: 0b10000000
        },
        "EXTENDED_HEADER_FLAG": {
            2: 0b00000000,
            3: 0b01000000,
            4: 0b01000000
        },
        "EXPERIMENTAL_INDICATOR_FLAG": {
            2: 0b00000000,
            3: 0b00100000,
            4: 0b00100000
        },
        "FOOTER_PRESENT_FLAG": {
            2: 0b00000000,
            3: 0b00000000,
            4: 0b00010000
        },
        "COMPRESSION_FLAG": {
            # He is, but he is not used. Version 2.2.0, WTF?
            2: 0b01000000,
            3: 0b00000000,
            4: 0b00000000
        }
    }

    FRAME_HEADER_FORMAT_DESC_FLAGS = {
        "COMPRESSION_FLAG": {
            3: 0b10000000,
            4: 0b00001000
        },
        "DATA_LEN_ID_FLAG": {
            3: 0b00000000,
            4: 0b00000001
        },
        "ENCRYPTION_FLAG": {
            3: 0b01000000,
            4: 0b00000100
        },
        "GROUPING_FLAG": {
            3: 0b00100000,
            4: 0b01000000
        },
        "UNSYNC_FLAG": {
            3: 0b00000000,
            4: 0b00000010
        }
    }

    def __init__(self, audio, datatype="filePath", filename=None):

        super(ID3V2, self).__init__(audio, datatype, filename)

        version = (2, 0)
        header = None
        for _header in self.HEADER.finditer(self._bytedata):

            decode_data = tuple(map(ord, _header.group()))

            if (4, 0) >= decode_data[3:5] >= version:
                version = decode_data[3:5]
                header = _header

        if not header:
            raise NotFindHeader("Not detected ID3V2 header.")

        decode_data = tuple(map(ord, header.group()))
        self.VERSION = (2,) + version
        self._FLAGS_BYTE = decode_data[5]

        if self.COMPRESSION_FLAG:
            raise IncorrectTag(
                "Tag compression version 2.2.0 is not supported."
            )
        _size = self.parse_size(decode_data[6:], synchsafe=True)

        offset = header.end()
        self._frames_raw_data = self._bytedata[offset:(_size + offset)]
        self._frames = self.__get_frames_dict()
        if not self._frames:
            raise IncorrectTag("No frames found.")

    def __get_frames_dict(self):

        """
        Groups frames into a dict.
        """

        frames = {}
        for frame_id, frame_data in self._get_frames_data():
            if frame_id in _MORE_THAN_ONE:
                frames.setdefault(frame_id, set()).add(frame_data)
            else:
                frames[frame_id] = frame_data

        for _fr_id in filter(frames.__contains__, _MORE_THAN_ONE):
            frames[_fr_id] = tuple(sorted(frames[_fr_id]))

        return frames

    def __getattr__(self, key):

        if ("_FLAGS_BYTE" in self.__dict__) and (key in self.FLAGS_INFO):
            ver = self.VERSION[1]
            return bool((self._FLAGS_BYTE & self.FLAGS_INFO[key][ver]))

        if "_frames" in self.__dict__:
            if key in self._frames:
                return self._frames[key]

            user_data = (
                (self._frames.get("TXXX", ()) + self._frames.get("WXXX", ()))
            )
            for description, data in user_data:
                if key == description:
                    return data
        raise AttributeError(key)

    @staticmethod
    def parse_size(int_or_bytes_array, synchsafe=False):
        """
        Parse bytes to standart int.

        :synchsafe:
            Highest bit will not be taken into account when reading data.
        """
        if isinstance(int_or_bytes_array, bytes):
            int_or_bytes_array = map(ord, int_or_bytes_array)

        result = 0b0
        for order, _byte in enumerate(reversed(int_or_bytes_array)):
            _byte &= (0b01111111 if synchsafe else 0b11111111)
            _byte <<= ((7 if synchsafe else 8) * order)
            result |= _byte
        return result

    @staticmethod
    def _get_encoding(bytecode):
        """
        Return encoding and splitter.
        """
        return (
            ("latin_1", r"\x00(?!\x00)"),
            ("utf_16", r"\x00\x00(?!\x00)"),
            ("utf_16_be", r"\x00\x00(?!\x00)"),
            ("utf_8", r"\x00(?!\x00)")
        )[ord(bytecode)]

    def _get_basic_tag(self, name):
        for _variant in BASIC_METADATA[self.VERSION[1]][name]:
            result = getattr(self, _variant, None)
            if result:
                return result
        return None

    @property
    def title_tag(self):
        return self._get_basic_tag("title")

    @property
    def artist_tag(self):
        return self._get_basic_tag("artist")

    @property
    def album_tag(self):
        return self._get_basic_tag("album")

    @property
    def coveralbum_tag(self):
        return self._get_basic_tag("coveralbum")

    @property
    def date_tag(self):
        return self._get_basic_tag("date")

    @property
    def genre_tag(self):
        genre = self._get_basic_tag("genre")
        if not genre:
            return None
        _id3v1_pattern = re.compile(r"(?<!\()\(\w+\)")
        genres = []
        for i in _id3v1_pattern.finditer(genre):
            _genre = i.group()[1:-1]
            if _genre.isdigit():
                try:
                    _genre = ID3V1GENRES[int(_genre)]
                except IndexError:
                    continue
                else:
                    genres.append(_genre)
            else:
                _genre = {
                    "RX": "Remix",
                    "CR": "Cover"
                }.get(_genre.upper(), None)
                if _genre:
                    genres.append(_genre)
        genre = _id3v1_pattern.sub(u"", genre).strip()
        if genre:
            genres.append(genre)
        return u'/'.join(genres)

    def _get_frames_data(self):
        """
        Yield mapping:
            "Frame ID": Data in a human-readable form.
        """

        for frame_id, matchObject in self._get_frames_headers():
            try:
                frame_id, frame_bytedata = self._parse_frame(matchObject)
                frame_data = self.frame_handler(frame_id, frame_bytedata)
            except SkipFrame as ex:
                self.LOGGER.debug("Skip %s frame.\n%s", frame_id, ex.message)
            except Exception as ex:
                self.LOGGER.exception(
                    "An error occurred while parsing frame %s.\n%s",
                    frame_id,
                    ex.message
                )
            else:
                yield (frame_id, frame_data)

    def _get_frames_headers(self):

        """
        Yield mapping:
            "Frame ID": re.Match pattern
        """
        _declaration = _FRAME_DECLARATION[self.VERSION[1]]
        if self.VERSION[1] == 2:
            find_format_pattern = r"{0}[\x00-\xff]{{3}}"
        elif self.VERSION[1] == 3:
            find_format_pattern = r"{0}[\x00-\xff]{{6}}"
        else:
            find_format_pattern = r"{0}[\x00-\x7f]{{4}}[\x00-\xff]{{2}}"

        for frame_id in _declaration.iterkeys():
            _find_pattern = find_format_pattern.format(frame_id)
            candidate = None
            for _cand in re.finditer(_find_pattern, self._frames_raw_data):
                if frame_id in _MORE_THAN_ONE:
                    yield (frame_id, _cand)
                else:
                    # Only last will be yield.
                    candidate = _cand
            if candidate:
                yield (frame_id, candidate)

    def _parse_frame(self, matchPattern):

        """
        Primary handling.
        Return tuple with FRAME ID and readable (decompression/sync) bytedata.
        """

        with io.BytesIO(matchPattern.group()) as header:

            if self.VERSION[1] == 2:
                frame_id = header.read(3)
                size = self.parse_size(header.read(3), synchsafe=False)
            else:
                frame_id = header.read(4)
                size = self.parse_size(
                    header.read(4),
                    synchsafe=(self.VERSION[1] == 4)
                )
            if not size:
                raise SkipFrame("Frame is empty.")

            offset = matchPattern.end()
            frame_data = self._frames_raw_data[offset:(size + offset)]

            if self.VERSION[1] == 2:

                if self.UNSYNCHRONISATION_FLAG:
                    self.LOGGER.debug("%s is unsync.", frame_id)
                    frame_data = re.sub(r"\xff\x00", "\xff", frame_data)

                return (frame_id, frame_data)

            header.read(1)  # "Status messages" flag.
            # "Status messages" flag is not needed of this module.
            format_description_flag = ord(header.read(1))
        description_flags = dict(
            map(
                lambda x: (
                    x[0],
                    bool((x[1][self.VERSION[1]] & format_description_flag))
                ),
                self.FRAME_HEADER_FORMAT_DESC_FLAGS.iteritems()
            )
        )
        description_flags["UNSYNC_FLAG"] = (
            (description_flags["UNSYNC_FLAG"] or self.UNSYNCHRONISATION_FLAG)
        )

        with io.BytesIO(frame_data) as frame:

            data_length = None
            encryption_method = None
            group_id = None
            if self.VERSION[1] == 3:
                if description_flags["COMPRESSION_FLAG"]:
                    data_length = self.parse_size(
                        frame.read(4),
                        synchsafe=False
                    )
                if description_flags["ENCRYPTION_FLAG"]:
                    encryption_method = ord(frame.read(1))
                if description_flags["GROUPING_FLAG"]:
                    group_id = ord(frame.read(1))
            else:
                if description_flags["GROUPING_FLAG"]:
                    group_id = ord(frame.read(1))
                if description_flags["COMPRESSION_FLAG"]:
                    if not description_flags["DATA_LEN_ID_FLAG"]:
                        raise SkipFrame()
                if description_flags["ENCRYPTION_FLAG"]:
                    encryption_method = ord(frame.read(1))
                if description_flags["DATA_LEN_ID_FLAG"]:
                    data_length = self.parse_size(
                        frame.read(4),
                        synchsafe=True
                    )

            frame_data = frame.read()

        if description_flags["GROUPING_FLAG"]:
            self.LOGGER.debug("%s in group %d.", frame_id, group_id)

        if description_flags["UNSYNC_FLAG"]:
            self.LOGGER.debug("%s is unsync.", frame_id)
            frame_data = re.sub(r"\xff\x00", "\xff", frame_data)

        if description_flags["COMPRESSION_FLAG"]:
            self.LOGGER.debug("%s is compressed.", frame_id)
            frame_data = zlib.decompress(frame_data)

        if description_flags["ENCRYPTION_FLAG"]:
            self.LOGGER.debug("%s is encrypted.", frame_id)
            raise SkipFrame("Decryption is not supported.")

        return (frame_id, frame_data)

    def frame_handler(self, frame_id, frame_bytedata):

        """
        Handle frame bytedata and returns information in a human-readable form.
        """

        if frame_id in ("PIC", "APIC"):
            # Attached picture
            text_encoding, splitter = self._get_encoding(frame_bytedata[0])
            frame_bytedata = frame_bytedata[1:]

            if self.VERSION[1] == 2:
                MIME_type = frame_bytedata[:3]
                frame_bytedata = frame_bytedata[3:]
            else:
                MIME_type, frame_bytedata = re.split(
                    r"\x00",
                    frame_bytedata,
                    1
                )
                MIME_type = codecs.decode(MIME_type, "latin_1")

            picture_type = APIC_TYPES[ord(frame_bytedata[0])]
            frame_bytedata = frame_bytedata[1:]

            description, picture_data = re.split(splitter, frame_bytedata, 1)
            description = codecs.decode(description, text_encoding)
            _filename = picture_type + IMAGE_MIME_EXT.get(MIME_type, ".jpg")
            return (_filename, picture_data)

        elif (frame_id[0] == 'T') or (frame_id in ("IPL", "IPLS")):
            # Text information or involved people list.
            text_encoding, splitter = self._get_encoding(frame_bytedata[0])
            frame_bytedata = frame_bytedata[1:]

            description = b""
            if frame_id in ("TXX", "TXXX"):
                description, frame_bytedata = re.split(
                    splitter,
                    frame_bytedata,
                    1
                )

            # 0x00 byte - a sign of line termination.
            frame_bytedata = re.split(splitter, frame_bytedata, 1)[0]

            description, value = map(
                lambda x: codecs.decode(x, text_encoding),
                (description, frame_bytedata)
            )
            if frame_id in ("TXX", "TXXX"):
                return (description, value)
            return value

        elif frame_id[0] == 'W':
            # URL link
            description = None
            if frame_id in ("WXX", "WXXX"):
                text_encoding, splitter = self._get_encoding(frame_bytedata[0])
                frame_bytedata = frame_bytedata[1:]

                description, frame_bytedata = re.split(
                    splitter,
                    frame_bytedata,
                    1
                )
                description = codecs.decode(description, text_encoding)

            # 0x00 byte - a sign of line termination.
            frame_bytedata = re.split(r"\x00", frame_bytedata, 1)[0]

            url = codecs.decode(frame_bytedata, "latin_1")

            if frame_id in ("WXX", "WXXX"):
                return (description, url)
            return url

        raise SkipFrame(
            "Handling of \"{0}\" frame is not implemented.".format(frame_id)
        )
