# -*- coding: utf-8 -*-
"""
Module for obtaining metadata from audio file.

@author: Vladya
"""

# TODO:
#     Притараканить ID3 всех четырёх версий (1, 2.2, 2.3, 2.4):
#         DONE!
#     Присобачить VORBIS/OPUS:
#         DONE!
#     APE второй туда же. Первый - нафиг. Кто-то на полном серьёзе его юзает?:
#         DONE!
#     Заделать модуль обращения к БД айТюнза:
#         DONE!
#     Не забыть удалить этот накроманский TODO, перед публикацией.
#         WiP

import logging
import sys
import re
from os import path
from .other_data import (
    IMAGE_MIME_EXT,
    ID3V1GENRES
)

__author__ = "Vladya"
__version__ = "1.0.0"

USE_WEB_DB = True


DATABASE_FOLDER = path.abspath(
    path.join(
        path.expanduser(u'~'),
        u"vladya's projects database",
        u"AudioMetaData",
        __version__
    )
)

logging.basicConfig()
LOGGER = logging.getLogger("AudioMetaData")
LOGGER.setLevel(logging.DEBUG)


class WrongData(Exception):
    pass


class IncorrectTag(Exception):
    pass


class NotFindHeader(IncorrectTag):
    pass


class TagNotDefined(Exception):
    pass


class AudioTag(object):

    """
    Abstract class for inheriting specific types of tags.
    """

    __author__ = "Vladya"
    LOGGER = LOGGER.getChild("AudioTag")

    def __init__(self, audio, datatype="filePath", filename=None):

        """
        :datatype:

            Interpretation of variable "audio".

            Possible values:
                "filePath" (default):
                    "audio" will be interpreted like file path.
                "fileObject":
                    "audio" will be interpreted like file object.
                "bytes":
                    "audio" will be interpreted like byte string.
        """
        if not isinstance(filename, basestring):
            filename = None
        if datatype in ("filePath", "fileObject"):
            if datatype == "filePath":
                audio = path.abspath(audio)
                if not path.isfile(audio):
                    raise Exception("File \"{0}\" is not exist.".format(audio))
            try:
                if datatype == "filePath":
                    audio = open(audio, "rb")
                else:
                    audio.seek(0, 0)
                data = b""
                while True:
                    chunk = audio.read((2 ** 20))  # 1mB
                    if not chunk:
                        break
                    data += chunk
                if (not filename) and hasattr(audio, "name"):
                    if isinstance(audio.name, basestring):
                        filename = audio.name
            finally:
                if datatype == "filePath":
                    audio.close()
        elif (datatype == "bytes") and isinstance(audio, bytes):
            data = audio
        else:
            raise WrongData(
                "Incorrect datatype \"{0}\" or data.".format(datatype)
            )

        if not data:
            raise WrongData("Data not found.")

        if filename:
            filename = path.splitext(path.basename(path.normpath(filename)))[0]
            if isinstance(filename, bytes):
                _enc = (sys.getfilesystemencoding() or "utf_8")
                filename = filename.decode(_enc, "ignore")
            self._filename = filename
        else:
            self._filename = None

        self._bytedata = data

    def __nonzero__(self):
        return bool((self.title_tag or self.artist_tag or self.album_tag))

    def __unicode__(self):
        title = u" - ".join(filter(bool, (self.artist_tag, self.title_tag)))
        if self.album_tag:
            title += u" ({0})".format(self.album_tag)
        return title.strip()

    def __str__(self):
        return self.__unicode__().encode("utf-8")

    def __repr__(self):
        return "<AudioTag {0}: {1}>".format(
            self.__class__.__name__,
            (self.__str__() or "Not detected basic metadata")
        )

    @property
    def title_tag(self):
        """
        Unicode string or None.
        """
        raise NotImplementedError("Must be redefined.")

    @property
    def artist_tag(self):
        """
        Unicode string or None.
        """
        raise NotImplementedError("Must be redefined.")

    @property
    def album_tag(self):
        """
        Unicode string or None.
        """
        raise NotImplementedError("Must be redefined.")

    @property
    def coveralbum_tag(self):
        """
        Tuple of the following format or None:
            (filename with ext, picture binary data)
        """
        raise NotImplementedError("Must be redefined.")

    @property
    def date_tag(self):
        """
        Unicode string or None.
        """
        raise NotImplementedError("Must be redefined.")

    @property
    def genre_tag(self):
        """
        Unicode string or None.
        """
        raise NotImplementedError("Must be redefined.")


class FilenameTag(AudioTag):

    """
    If file does not contain any tags, trying to parse the filename.
    """

    def __init__(self, audio, datatype="filePath", filename=None):

        super(FilenameTag, self).__init__(audio, datatype, filename)

        if not self._filename:
            raise NotFindHeader("Not found filename.")

        self.__title = map(
            lambda x: re.sub(r"[\s\\/_]+", u' ', x).strip(),
            re.split(r"[\s\\/\-_]{2,}", self._filename, 1)
        )
        if len(self.__title) > 1:
            self.__artist, self.__title = self.__title
        else:
            self.__title = self.__title[0]
            self.__artist = None

    @property
    def title_tag(self):
        return self.__title

    @property
    def artist_tag(self):
        return self.__artist

    @property
    def album_tag(self):
        return None

    @property
    def coveralbum_tag(self):
        return None

    @property
    def date_tag(self):
        return None

    @property
    def genre_tag(self):
        return None