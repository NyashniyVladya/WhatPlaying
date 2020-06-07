
init 4 python in _whatPlaying:

    """
    Настройки юзера.
    """

    class Preferences(NoRollback):

        """
        Настройки предпочтений юзера и инкапсуляция работы с persistent data.
        """

        __author__ = "Vladya"

        DEFAULT_VALUES = {
            "channel_name": "music",
            "alpha": 1.,
            "alignment": "tr",
            "search_engine": "YouTube",
            "minimize": True,
            "drag_mode": False
        }

        alignment_pattern = re.compile(
            r"(?<!.)(((?P<yalign>[tb])?(?P<xalign>[lr])?)|(?P<center>c))(?!.)",
            flags=(re.IGNORECASE | re.DOTALL)
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
            return "what_playing_pref_{0}_{1}".format(self.__pref_id, name)

        @property
        def drag_mode(self):
            """
            Является ли основное окно перетаскиваемым.
            """
            name = self._get_persistent_name("drag_mode")
            with self.__locks["drag_mode"]:
                return getattr(persistent, name)

        @drag_mode.setter
        def drag_mode(self, new_drag_mode):
            new_drag_mode = bool(new_drag_mode)
            name = self._get_persistent_name("drag_mode")
            with self.__locks["drag_mode"]:
                if new_drag_mode != getattr(persistent, name):
                    setattr(persistent, name, new_drag_mode)
                    DisplayableWrapper._clear_cache()
                    renpy.restart_interaction()  # Реинициализация скрина.

        @property
        def minimize(self):
            """
            Сворачивать ли окно, когда нет наведения.
            """
            name = self._get_persistent_name("minimize")
            with self.__locks["minimize"]:
                return getattr(persistent, name)

        @minimize.setter
        def minimize(self, new_minimize):
            new_minimize = bool(new_minimize)
            name = self._get_persistent_name("minimize")
            with self.__locks["minimize"]:
                if new_minimize != getattr(persistent, name):
                    setattr(persistent, name, new_minimize)

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
        def search_engine(self):
            """
            Поисковый сервис, используемый для... Ну... Для поиска!
            """

            name = self._get_persistent_name("search_engine")
            with self.__locks["search_engine"]:
                return getattr(persistent, name)

        @search_engine.setter
        def search_engine(self, new_search_engine):
            if isinstance(new_search_engine, SearchBase):
                new_search_engine = new_search_engine.NAME
            if not isinstance(new_search_engine, basestring):
                raise TypeError(__("Неверный тип 'search_engine'."))
            new_search_engine = new_search_engine.lower()
            for sc in ExtraFunctional.search_classes:
                if new_search_engine in (sc.__name__.lower(), sc.NAME.lower()):
                    name = self._get_persistent_name("search_engine")
                    with self.__locks["search_engine"]:
                        if getattr(persistent, name) != sc.NAME:
                            setattr(persistent, name, sc.NAME)
                            break
            else:
                raise ValueError(
                    __("{0} не является поисковым сервисом.").format(
                        new_search_engine
                    )
                )

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
            return alignment_data.strip('c')

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
