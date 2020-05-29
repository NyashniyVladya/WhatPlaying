
init -2 python in _whatPlaying:

    """
    Классы для различных оптимизаций.
    """


    class DisplayableWrapper(NoRollback):
    
        """
        Инкапсуляция диспов, для извлечения отрендеренных параметров,
        как атрибутов.
        
        Экземпляры НЕ являются Displayable.
        """
        
        __author__ = "Vladya"
        
        def __init__(self, disp, width, height, st, at):
            
            if not isinstance(disp, renpy.display.core.Displayable):
                raise Exception(__("Передан не 'renpy.Displayable'."))
            
            self.__displayable = disp
            self.__render_args = (width, height, st, at)
            
            self.__surface = None
            
        def __getattr__(self, key):
            if key.startswith("__") and key.endswith("__"):
                raise AttributeError(key)
            return getattr(self.displayable, key)

        @property
        def displayable(self):
            """
            Сам Displayable.
            """
            return self.__displayable
            
        @property
        def surface(self):
            """
            Объект рендера.
            """
            if not self.__surface:
                self.__surface = renpy.render(
                    self.displayable,
                    *self.__render_args
                )
            return self.__surface

        @property
        def width(self):
            """
            Ширина отрендеренного диспа.
            """
            return self.surface.width

        @property
        def height(self):
            """
            Высота.
            """
            return self.surface.height



    class MusicScanner(threading.Thread, NoRollback):
    
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


        @classmethod
        def _get_all_tracks(cls):
            """
            Возвращает всё поддерживаемое аудио из папок игры в формате:
                (Читаемое имя файла, Полный путь в RenPy формате)
            """
            for renpy_fn in renpy.list_files():
                basename, ext = path.splitext(
                    path.basename(path.normpath(renpy_fn))
                )
                if ext.lower() in cls.file_exts:
                    yield (basename, renpy_fn)

        def run(self):
        
            try:
                targets = frozenset(self._get_all_tracks())
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






    class ExtraFunctional(renpy.Displayable, NoRollback):
    
        """
        TODO: Заделать этот самый функционал.
        Копирование в БО.
        Вывод доп. информации и прочее.
        """
        
        __author__ = "Vladya"
        
        def __init__(self):
            
            super(ExtraFunctional, self).__init__()
    
        
    
    
    
    
    
    
    
    
    