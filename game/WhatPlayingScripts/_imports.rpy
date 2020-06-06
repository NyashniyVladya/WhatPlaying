
init 1 python in _whatPlaying:

    """
    Импорты, всякие флаги, доп. функции.
    """

    import __builtin__
    import io
    import re
    import logging
    import random
    import zipfile
    import threading
    import urllib
    import urllib2
    import webbrowser
    import pygame_sdl2 as pygame
    from os import path
    from renpy.audio.audio import get_channel
    from collections import (
        OrderedDict,
        namedtuple
    )
    from AudioMetaData import (
        audio,
        itunes,
        TagNotDefined,
        WrongData,
        LOGGER
    )
    from store import (
        _preferences,
        im,
        config,
        persistent,
        NoRollback,
        FieldValue,
        Function,
        Color,
        BarValue,
        FieldEquality,
        SetField,
        Transform,
        HBox,
        VBox,
        Button,
        ImageButton,
        Text,
        Window,
        Drag
    )
    try:
        from store import AudioData
    except ImportError:
        class AudioData(object):
            """
            Для более старых версий ренпая, где ещё не было AudioData.
            """
            pass

    DEBUG = True  # Флаг для отладки.
    LOGGER.setLevel((logging.DEBUG if DEBUG else logging.CRITICAL))
    _logger = LOGGER.getChild("RenPyLogger")
    languages_codes = {
        "russian": "RU",
        "english": "US",
        "spanish": "ES",
        "italian": "IT",
        "chinese": "CN",
        "latvian": "LV"
    }

    itunes.ITunesWebParser.ITUNES_COUNTRY = languages_codes.get(
        _preferences.language,
        None
    )

    # Константа золотого сечения. Для позиционирования объектов на экране.
    PHI_CONST = (((5. ** (1. / 2.)) - 1.) / 2.)

    def recalculate_to_screen_size(value, is_width=True):
        """
        Пересчитывает значение под текущее разрешение экрана.
        Принимаемое значение инвариантно для разрешения 1920x1080.

        :is_width:
            True - Считать от ширины
            False - От высоты

        """
        if not isinstance(value, (int, float)):
            raise TypeError(__("Неверный тип переданного значения."))
        if is_width:
            coefficient = float(config.screen_width) / 1920.
        else:
            coefficient = float(config.screen_height) / 1080.

        result = (float(value) * coefficient)
        if isinstance(value, int):
            return int(round(result))
        return result

    def quote_text(text):
        """
        Экранирование спец. символов ренпая.
        """
        if not isinstance(text, basestring):
            raise TypeError(__("Передан не текст."))
        for old, new in {'[': "[[", '{': "{{"}.iteritems():
            text = text.replace(old, new)
        return text

    def unpack_multiline_string(string):
        """
        Удаляет избыточные пробелы и переносы в мультистроках
        (это которые вот как этот комментарий).

        Для сохранения переноса, добавлять в строку '{N}'.
        Сей символ будет заменён на перенос строки.
        """
        if not isinstance(string, basestring):
            raise TypeError(__("Передан не текст."))

        string = re.sub(r"\s+", ' ', string, flags=re.UNICODE)
        string = re.sub(r"\s*\{N\}\s*", '\n', string, flags=re.UNICODE)
        return string.strip()

    def try_open_page(url):
        try:
            webbrowser.open_new_tab(url)
        except Exception as ex:
            _logger.error(
                "Ошибка при открытии страницы '%s'\n%s.",
                url,
                ex.message
            )
