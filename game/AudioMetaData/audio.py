# -*- coding: utf-8 -*-
"""
Combining tag parsers in a single class.

@author: Vladya
"""

from . import (
    id3,
    vorbis,
    apev2,
    itunes,
    AudioTag,
    FilenameTag,
    IncorrectTag,
    NotFindHeader,
    TagNotDefined,
    LOGGER,
    USE_WEB_DB
)


class AudioFile(AudioTag):

    LOGGER = LOGGER.getChild("AudioFile")

    def __init__(self, audio, datatype="filePath", filename=None):

        super(AudioFile, self).__init__(audio, datatype, filename)

        _tags = []
        tags_priority = (
            id3.ID3V2,
            vorbis.VorbisComment,
            apev2.APEv2,
            id3.ID3V1,
            FilenameTag
        )
        for _tagClass in tags_priority:
            _name = _tagClass.__name__
            try:
                tag = _tagClass(
                    audio=self._bytedata,
                    datatype="bytes",
                    filename=self._filename
                )
            except NotFindHeader:
                self.LOGGER.debug("Tag {0} is not detected.".format(_name))
            except IncorrectTag:
                self.LOGGER.debug("Tag {0} incorrect.".format(_name))
            except Exception:
                self.LOGGER.exception(
                    "An error occurred while parsing {0} tag.".format(_name)
                )
            else:
                # After initialization, there is no need to store
                # such large amounts of unnecessary data.
                delattr(tag, "_bytedata")

                _tags.append(tag)

        self._tags = tuple(_tags)
        if not self._tags:
            raise TagNotDefined("No tags found.")

        if USE_WEB_DB:
            try:
                self._web = itunes.ITunesWebParser(self)
            except Exception:
                self._web = None
        else:
            self._web = None

        delattr(self, "_bytedata")

    def __getattr__(self, key, ignore_web_tag=False):

        if not ignore_web_tag:
            if ("_web" in self.__dict__) and self._web and self._web.web_tag:
                if self._web.web_tag not in self._tags:
                    self._tags = (self._web.web_tag,) + self._tags

        for tag in self._tags:
            if ignore_web_tag and isinstance(tag, itunes.WebTag):
                continue
            result = getattr(tag, key, None)
            if result:
                return result
        raise AttributeError(key)

    def _get_basic_tag(self, name, ignore_web_tag=False):
        try:
            return self.__getattr__(name, ignore_web_tag=ignore_web_tag)
        except AttributeError:
            return None

    @property
    def title_tag(self):
        return self._get_basic_tag("title_tag")

    @property
    def artist_tag(self):
        return self._get_basic_tag("artist_tag")

    @property
    def album_tag(self):
        return self._get_basic_tag("album_tag")

    @property
    def coveralbum_tag(self):
        return self._get_basic_tag("coveralbum_tag")

    @property
    def date_tag(self):
        return self._get_basic_tag("date_tag")

    @property
    def genre_tag(self):
        return self._get_basic_tag("genre_tag")
