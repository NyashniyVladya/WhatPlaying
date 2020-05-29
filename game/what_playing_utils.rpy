
init -3 python in _whatPlaying:

    """
    Импорты, всякие флаги, доп. функции. Чтобы не загромождать основной файл.
    """

    import io
    import random
    import zipfile
    import threading
    from os import path
    from renpy.audio.audio import get_channel
    from AudioMetaData import (
        audio,
        TagNotDefined,
        WrongData
    )
    from store import (
        im,
        config,
        persistent,
        NoRollback,
        Transform,
        Text,
        HBox,
        VBox,
        FieldValue
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
    
        
    # Константа золотого сечения. Для позиционирования объектов на экране.
    PHI_CONST = (((5. ** (1. / 2.)) - 1.) / 2.)
    
    def recalculate_to_screen_size(value, width=True):
        """
        Пересчитывает значение под текущее разрешение экрана.
        Принимаемое значение инвариантно для разрешения 1920x1080.

        :width:
            True - Считать от ширины
            False - От высоты

        """
        if not isinstance(value, (int, float)):
            raise TypeError(__("Неверный тип переданного значения."))
        if width:
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
        
    def get_texts_disp(string_data, **text_kwargs):
        """
        Возвращает объект текста.
        (Для синхронизации стилей.)
        """
        if not isinstance(string_data, basestring):
            try:
                string_data = unicode(string_data)
            except Exception:
                raise TypeError(__("Передан не текст."))

        default_kwargs = {
            "size": recalculate_to_screen_size(35),
            "layout": "nobreak",
            "text_align": 1.
        }
        default_kwargs.update(text_kwargs)
        return Text(string_data, **default_kwargs)
        
    def get_bar_disp(**bar_kwargs):
        """
        Возвращает объект бара.
        (Всё для той же цели. Синхронизация стилей.)
        """
        default_kwargs = {}
        if bar_kwargs.get("vertical", False):
            # Вертикальный бар.
            default_kwargs["width"] = recalculate_to_screen_size(22)
        else:
            # Горизонтальный.
            default_kwargs["height"] = recalculate_to_screen_size(22, False)
        default_kwargs.update(bar_kwargs)
        
        # Если переданы конкретные размеры - они должны быть неизменны.
        if "width" in default_kwargs:
            default_kwargs["xminimum"] = default_kwargs["width"]
            default_kwargs["xmaximum"] = default_kwargs["width"]
            
        if "height" in default_kwargs:
            default_kwargs["yminimum"] = default_kwargs["height"]
            default_kwargs["ymaximum"] = default_kwargs["height"]

        return renpy.display.behavior.Bar(**default_kwargs)

