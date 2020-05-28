

init -2 python in _whatPlaying:

    """
    Импорты и всякие доп. функции. Чтобы не загромождать основной файл.
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
    
        
    # Константа золотого сечения. Для выведения объектов на экране.
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
        default_kwargs = {
            "size": recalculate_to_screen_size(35),
            "text_align": 1.
        }
        default_kwargs.update(text_kwargs)
        return Text(string_data, **default_kwargs)
        
    def get_bar_disp(**bar_kwargs):
        """
        Возвращает объект бара.
        (Всё для той же цели. Синхронизация стилей.)
        """
        if bar_kwargs.get("vertical", False):
            # Вертикальный бар.
            default_kwargs = {
                "width": recalculate_to_screen_size(22),
                "xminimum": 1,
                "yminimum": 2,
            }
        else:
            # Горизонтальный.
            default_kwargs = {
                "height": recalculate_to_screen_size(22),
                "xminimum": 2,
                "yminimum": 1,
            }

        default_kwargs.update(bar_kwargs)
        return renpy.display.behavior.Bar(**default_kwargs)


    class MusicScanner(threading.Thread):
    
        """
        Демон для предварительной загрузки данных.
        """
    
        __author__ = "Vladya"
        
        
        file_exts = frozenset({".wav", ".mp2", ".mp3", ".ogg", ".opus"})
    
        def __init__(self, viewer_object):
        
            super(MusicScanner, self).__init__()
            self.daemon = True

            self.__viewer_object = viewer_object

            self.__scan_completed = False

            self.__scan_status = .0
            self.__scan_now = None
            self.__exception = None

        @property
        def scan_completed(self):
            """
            Булевое значение - завершено ли сканирование.
            """
            return self.__scan_completed
            
        @property
        def scan_status(self):
            """
            Значение от .0 до 1., выражающее отношение
            количества уже просканированных файлов к общему их числу.
            """
            return self.__scan_status
            
        @property
        def scan_now(self):
            """
            Название сканируемого файла.
            """
            return self.__scan_now

        @property
        def exception(self):
            """
            Если во время сканирование произошла ошибка - забирать отсюда.
            """
            return self.__exception
            
        def _get_text_view(self, short_view=False):
            """
            Возвращает текстовое описание состояния сканирования.
            :short_view:
                Краткое описание. Вернётся только имя сканируемого файла.
            """

            if self.scan_completed:
                return __("Сканирование завершено.")

            scan_now = self.scan_now
            if scan_now:
                text_view = __("Сканируется {{i}}\"{0}\"{{/i}}.").format(
                    quote_text(scan_now)
                )
                if short_view:
                    return text_view
                    
                text_view = '\n'.join(
                    (
                        text_view,
                        __("Завершено {0:.0%}.").format(self.scan_status)
                    )
                )
                return text_view

            else:
                return __("Сканирование вот-вот начнётся.")


        def run(self):
        
            try:
                targets = set()
                for renpy_fn in renpy.list_files():
                    basename, ext = path.splitext(
                        path.basename(path.normpath(renpy_fn))
                    )
                    ext = ext.lower()
                    if ext in self.file_exts:
                        targets.add((basename, renpy_fn))

                targets_number = float(len(targets))
                for i, (basename, renpy_fn) in enumerate(targets):
                    self.__scan_status = float(i) / targets_number
                    self.__scan_now = basename
                    self.__viewer_object._get_metadata_object(
                        filename=renpy_fn
                    )
                    
            except Exception as ex:
                self.__exception = ex
                raise ex
            finally:
                self.__scan_completed = True
                self.__scan_status = 1.
                self.__scan_now = None
