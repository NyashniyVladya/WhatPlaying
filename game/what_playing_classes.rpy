
init -2 python in _whatPlaying:

    """
    Классы для различных оптимизаций.
    """


    class Preferences(NoRollback):
    
        """
        Настройки предпочтений юзера и инкапсуляция работы с persistent data.
        """
    
        __author__ = "Vladya"
        
        DEFAULT_VALUES = {
            "channel_name": "music",
            "alpha": 1.,
            "alignment": "tr"
        }
        
        alignment_pattern = re.compile(
            r"(?<!.)(((?P<yalign>[tb])?(?P<xalign>[lr])?)|(?P<center>c))(?!.)",
            flags=(re.IGNORECASE|re.DOTALL)
        )
        
        def __init__(self, pref_id):

            if not isinstance(pref_id, basestring):
                raise TypeError(__("Идентификатор должен быть строкой."))
            self.__pref_id = re.sub(r"\s+", '_', pref_id, flags=re.UNICODE)

            self.__locks = {}
            for name, value in self.DEFAULT_VALUES.iteritems():
                persistent_name = self._get_persistent_name(name)
                if getattr(persistent, persistent_name) is None:
                    setattr(persistent, persistent_name, value)
                self.__locks[name] = threading.Lock()

        def _get_persistent_name(self, name):
            """
            Преобразует строку в имя persistent атрибута.
            """
            return "_what_playing_pref_{0}_{1}".format(self.__pref_id, name)
            
        @property
        def channel_name(self):
            """
            Имя аудио канала.
            """
            name = self._get_persistent_name("channel_name")
            with self.__locks["channel_name"]:
                return getattr(persistent, name)

        @channel_name.setter
        def channel_name(self, new_channel_name):
            with self.__locks["channel_name"]:
                try:
                    # Проверяем, существует ли канал.
                    channel = get_channel(new_channel_name)
                except Exception:
                    raise ValueError(__("Некорректное имя канала."))
                else:
                    name = self._get_persistent_name("channel_name")
                    if channel.name != getattr(persistent, name):
                        setattr(persistent, name, channel.name)

        @property
        def alpha(self):
            """
            Непрозрачность окна.
            """
            name = self._get_persistent_name("alpha")
            with self.__locks["alpha"]:
                return getattr(persistent, name)
                
        @alpha.setter
        def alpha(self, new_alpha):

            if not isinstance(new_alpha, (int, float)):
                raise TypeError(__("Неверный тип 'alpha'."))
            new_alpha = max(min(float(new_alpha), 1.), .0)

            name = self._get_persistent_name("alpha")
            with self.__locks["alpha"]:
                if new_alpha != getattr(persistent, name):
                    setattr(persistent, name, new_alpha)

        
        @property
        def xalign(self):
            xalign, yalign = self._alignment_to_tuple(self.alignment)
            return xalign
        
        @property
        def yalign(self):
            xalign, yalign = self._alignment_to_tuple(self.alignment)
            return yalign

        @property
        def alignment(self):
            """
            Выравнивание объектов к определённой стороне.
            Значения параметра эквивалентны значениям ренпаевского Side.
            """
            name = self._get_persistent_name("alignment")
            with self.__locks["alignment"]:
                return getattr(persistent, name)

        @alignment.setter
        def alignment(self, new_alignment):
            new_alignment = self._alignment_to_text(new_alignment)
            name = self._get_persistent_name("alignment")
            with self.__locks["alignment"]:
                if new_alignment != getattr(persistent, name):
                    setattr(persistent, name, new_alignment)

        @classmethod
        def _alignment_to_text(cls, alignment_data):
            """
            Преобразует произвольное значение выравнивания в текстовую форму.
            """
            xalign, yalign = cls._alignment_to_tuple(alignment_data)
            xalign = {.0: 'l', 1.: 'r'}.get(xalign, 'c')
            yalign = {.0: 't', 1.: 'b'}.get(yalign, 'c')
            alignment_data = "{0}{1}".format(yalign, xalign)
            if alignment_data == "cc":
                return 'c'
            return alignment_data

        @classmethod
        def _alignment_to_tuple(cls, alignment_data):
            """
            Преобразует произвольное значение выравнивания в кортеж float.
            tl - (0.0, 0.0)
            r  - (1.0, 0.5)
            bl - (0.0, 1.0)
            и т.д.
            """
            
            if isinstance(alignment_data, tuple):
                if len(alignment_data) == 2:
                    if all(map(lambda x: (x in (.0, .5, 1.)), alignment_data)):
                        return tuple(map(float, alignment_data))
                raise ValueError(__("Неверный формат кортежа выравнивания."))

            elif isinstance(alignment_data, basestring):
                alignment_data = cls.alignment_pattern.search(alignment_data)
                if alignment_data:
                    alignment_data = alignment_data.groupdict()
                    if any(alignment_data.itervalues()):
                        if alignment_data["center"]:
                            return (.5, .5)
                        xalign = {'l': .0, 'r': 1.}.get(
                            (alignment_data["xalign"] or "").lower(), 
                           .5
                        )
                        yalign = {'t': .0, 'b': 1.}.get(
                            (alignment_data["yalign"] or "").lower(),
                            .5
                        )
                        return (xalign, yalign)
                raise ValueError(__("Неверный формат строки выравнивания."))

            raise TypeError(__("Неверный тип данных выравнивания."))


    class _AudioPositionValue(BarValue, FieldEquality):
        
        identity_fields = ["viewer_object"]
        
        def __init__(self, viewer_object):
            self.viewer_object = viewer_object

        def get_adjustment(self):
            position = self.viewer_object._get_position()
            self.adjustment = ui.adjustment(
                range=1.,
                value=(position or .0),
                adjustable=False
            )
            return self.adjustment

        def periodic(self, st):
            position = self.viewer_object._get_position()
            if isinstance(position, float):
                self.adjustment.change(position)
            return .0

    class _ScanThreadStatusValue(BarValue, FieldEquality):
        
        def __init__(self, scanner_thread_object):
            self.__scanner = scanner_thread_object
            
        def get_adjustment(self):
            self.adjustment = ui.adjustment(
                range=1.,
                value=self.__scanner.scan_status,
                adjustable=False
            )
            return self.adjustment
            
        def periodic(self, st):
            self.adjustment.change(self.__scanner.scan_status)
            return .0
            


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
                DisplayableWrapper._clear_cache()
