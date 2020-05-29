# -*- coding: utf-8 -*-
"""
Module for verifying tags with data from iTunes.

@author: Vladya
"""

import time
import json
import re
import urllib
import urllib2
import io
import os
import hashlib
import threading
from os import path
from datetime import datetime
from . import (
    LOGGER,
    DATABASE_FOLDER,
    AudioTag
)


class InternetConnectionError(Exception):
    pass


class JSONError(Exception):
    pass


class WebTag(AudioTag):

    LOGGER = AudioTag.LOGGER.getChild("WebTag")

    def __init__(self, itunes_dict):

        self.__itunes_data = itunes_dict.copy()
        self.__coveralbum = None

        self.__coveralbum_lock = threading.Lock()

    def __getattr__(self, key):
        if key.startswith("__") and key.endswith("__"):
            raise AttributeError(key)
        if key in self.__itunes_data:
            return self.__itunes_data[key]
        raise AttributeError(key)

    def _get_cover_link(self):
        variants = {}
        for key in self.__itunes_data.iterkeys():
            result = re.search(r"(?<=artworkUrl)\d+", key, re.UNICODE)
            if result:
                variants[key] = int(result.group())
        if not variants:
            return None

        key = max(variants.iterkeys(), key=variants.__getitem__)
        return self.__itunes_data[key]

    @property
    def title_tag(self):  # Guaranteed in response
        return self.trackName

    @property
    def artist_tag(self):  # Guaranteed in response
        return self.artistName

    @property
    def album_tag(self):  # Guaranteed in response
        return self.collectionName

    @property
    def coveralbum_tag(self):  # Optional
        with self.__coveralbum_lock:
            if self.__coveralbum:
                if self.__coveralbum == "noOptionFound":
                    return None
                return self.__coveralbum
            url = self._get_cover_link()
            if not url:
                self.__coveralbum = "noOptionFound"
                return None
            try:
                image = ITunesWebParser._openurl(url)
            except InternetConnectionError:
                return None
            except Exception as ex:
                self.LOGGER.error("Unrecognized error.\n%s", ex.message)
                return None
            imagedata = b""
            while True:
                chunk = image.read((2 ** 20))
                if not chunk:
                    self.__coveralbum = (path.basename(url), imagedata)
                    return self.__coveralbum
                imagedata += chunk

    @property
    def date_tag(self):  # Optional
        if "releaseDate" not in self.__itunes_data:
            return None
        try:
            date = datetime.strptime(self.releaseDate, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return None
        else:
            return date.strftime("%d.%m.%Y")

    @property
    def genre_tag(self):  # Optional
        if "primaryGenreName" not in self.__itunes_data:
            return None
        return self.primaryGenreName


class ITunesWebParser(object):

    """
    API Documentation:
        https://affiliate.itunes.apple.com/
        resources/documentation/itunes-store-web-service-search-api/
    """

    __author__ = "Vladya"

    LOGGER = LOGGER.getChild("ITunesWebData")
    URL = urllib2.urlparse.urlparse("https://itunes.apple.com/search")
    CACHE_FOLDER = path.join(DATABASE_FOLDER, u"WebCache")
    RPM = 20.  # Request per minute
    LAST_REQUEST = .0

    WEBPAGE_FILE_LOCK = threading.Lock()
    WEB_LOCK = threading.Lock()

    def __init__(self, audio_file):

        artist = audio_file._get_basic_tag("artist_tag", ignore_web_tag=True)
        title = audio_file._get_basic_tag("title_tag", ignore_web_tag=True)
        if not (artist and title):
            raise Exception("Not enough data to search.")

        self._audio = audio_file
        self.__web_tag = None

        self.__web_tag_lock = threading.Lock()

    @property
    def web_tag(self):

        with self.__web_tag_lock:

            if self.__web_tag:
                if self.__web_tag == "noOptionFound":
                    return None
                return self.__web_tag

            try:
                variants = self._get_results_about_track()
            except InternetConnectionError:
                return None
            except JSONError:
                self.LOGGER.error("JSON decode error.")
                self.__web_tag = "noOptionFound"
                return None
            except Exception as ex:
                self.LOGGER.error("Unrecognized error.\n%s", ex.message)
                return None

            if len(variants) == 1:
                self.__web_tag = WebTag(variants[0])
                return self.__web_tag

            _tit = self._audio._get_basic_tag("title_tag", ignore_web_tag=True)
            _alb = self._audio._get_basic_tag("album_tag", ignore_web_tag=True)
            for variant in map(WebTag, variants):
                if _tit.lower() == variant.title_tag.lower():
                    if _alb and (_alb.lower() != variant.album_tag.lower()):
                        continue
                    self.__web_tag = variant
                    return self.__web_tag
            self.__web_tag = "noOptionFound"
            return None

    @classmethod
    def _openurl(cls, url, force_update=False):
        """
        io.BytesIO object containing the page data will be returned.
        """
        _url = urllib2.urlparse.urlparse(url)
        _folder = path.join(
            cls.CACHE_FOLDER,
            _url.hostname
        )
        cache_flename = u"{0}.webpage".format(
            hashlib.sha512(
                urllib2.quote(_url.geturl(), safe="")
            ).hexdigest().decode("ascii")
        )
        cache_flename = path.join(_folder, cache_flename)

        with cls.WEBPAGE_FILE_LOCK:

            if not path.isdir(_folder):
                os.makedirs(_folder)

            if force_update or (not path.isfile(cache_flename)):

                answer = cls._urllib_urlopen(url)
                _temp_fn = u"{0}.temp".format(cache_flename)
                with open(_temp_fn, "wb") as _file:
                    while True:
                        chunk = answer.read((2 ** 17))
                        if not chunk:
                            break
                        _file.write(chunk)
                if path.isfile(cache_flename):
                    os.remove(cache_flename)
                os.rename(_temp_fn, cache_flename)

            result = b""
            with open(cache_flename, "rb") as _file:
                while True:
                    chunk = _file.read((2 ** 20))
                    if not chunk:
                        return io.BytesIO(result)
                    result += chunk

    @classmethod
    def _urllib_urlopen(cls, *args, **kwargs):
        with cls.WEB_LOCK:
            while (time.time() - cls.LAST_REQUEST) < (60. / cls.RPM):
                time.sleep(.01)
            try:
                return urllib2.urlopen(*args, **kwargs)
            except Exception as ex:
                raise InternetConnectionError(ex.message)
            finally:
                cls.LAST_REQUEST = time.time()

    def _get_results_about_track(self):

        term = u' '.join(
            (
                self._audio._get_basic_tag("artist_tag", ignore_web_tag=True),
                self._audio._get_basic_tag("title_tag", ignore_web_tag=True)
            )
        )
        _album = self._audio._get_basic_tag("album_tag", ignore_web_tag=True)
        if _album:
            term += u" {0}".format(_album)
        self.LOGGER.debug(u"Term is \"%s\".", term)
        with self.search(term=term) as webpage:
            try:
                results = json.load(webpage, encoding="utf_8")
            except Exception as ex:
                raise JSONError(ex.message)
        if u"results" not in results:
            raise JSONError()
        return results[u"results"]

    @classmethod
    def search(cls, term, **search_params):

        _params = {
            "term": term,
            "country": "RU",
            "media": "music",
            "entity": "song",
            "attribute": "mixTerm",
            "limit": 200
        }
        _params.update(search_params)

        search_params = _params.copy()
        _params = {}

        for k, v in search_params.iteritems():
            if isinstance(k, unicode):
                k = k.encode("utf_8")
            if isinstance(v, unicode):
                v = v.encode("utf_8")
            _params[k] = v

        _params = tuple(sorted(_params.iteritems(), key=lambda x: x[0]))
        url = urllib2.urlparse.ParseResult(
            cls.URL.scheme,
            cls.URL.netloc,
            cls.URL.path,
            cls.URL.params,
            urllib.urlencode(_params),  # query
            cls.URL.fragment
        )

        return cls._openurl(url.geturl())
