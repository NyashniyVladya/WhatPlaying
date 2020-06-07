
init 4 python in _whatPlaying:

    """
    Класс реализации доп. функционала.
    """


    class ExtraFunctional(NoRollback):

        """
        Копирование в БО, вывод доп. информации и прочее.
        """

        __author__ = "Vladya"

        search_classes = (
            YouTubeSearch,
            GeniusSearch,
            YandexSearch,
            YandexMusicSearch,
            GoogleSearch,
            NicoNicoSearch,
            VKSearch,
            WikipediaSearch
        )


        def __init__(self, viewer_object):

            self.__viewer_object = viewer_object


            # Всякие информационные сообщения о успешном копировании и пр.
            self.__status_messages = OrderedDict()
            self.__status_lock = threading.Lock()

        @property
        def search_engine(self):
            _name = self.__viewer_object.preferences.search_engine
            for sc in self.search_classes:
                if _name == sc.NAME:
                    return sc
            if DEBUG:
                raise UnboundLocalError(
                    __("Не найдено класса с именем '{0}'.").format(_name)
                )
            return YouTubeSearch

        def _set_next_search_engine(self):
            _index = self.search_classes.index(self.search_engine)
            _new_index = (_index + 1) % len(self.search_classes)
            new_se = self.search_classes[_new_index]
            self.__viewer_object.preferences.search_engine = new_se.NAME

        @property
        def status_messages(self):
            """
            Забрать сообщения.
            """
            with self.__status_lock:
                return tuple(self.__status_messages.itervalues())

        def add_message(self, source, message):
            """
            Добавить сообщение.
            """
            if not isinstance(message, basestring):
                raise TypeError(__("Передан не текст."))
            try:
                hash(source)
            except TypeError:
                raise TypeError(__("Неверный тип источника."))
            with self.__status_lock:
                self.__status_messages[source] = message

        def _clean_status_messages(self):
            with self.__status_lock:
                self.__status_messages.clear()

        def get_extra_block(self, *render_args):
            """
            Возвращает объект 'DisplayableWrapper'.
            """
            base_block = None
            if self.__viewer_object.scanner_thread.scan_completed:
                if not config.skipping:
                    if self.__viewer_object._get_metadata_object():
                        text_view = __(
                            """
                            Жми {{i}}ЛКМ{{/i}} на нужную часть
                            информации о песне, чтобы скопировать её
                            в {{i}}буфер обмена{{/i}}.{{N}}
                            Жми {{i}}ПКМ{{/i}}, чтобы найти её через сервис
                            {{i}}"{0}"{{/i}} (откроется браузер).
                            """
                        ).format(__(self.search_engine.NAME))
                        _text_info = DisplayableWrapper(
                            self.__viewer_object.disp_getter.Text(
                                unpack_multiline_string(text_view),
                                layout="subtitle",
                                xmaximum=int(self.__viewer_object.MAX_SIZE[0])
                            ),
                            *render_args
                        )
                        text_view = __(
                            "Жми на эту надпись, чтобы сменить сервис поиска."
                        )
                        _button = DisplayableWrapper(
                            self.__viewer_object.disp_getter.TextButton(
                                text_view,
                                Function(self._set_next_search_engine)
                            ),
                            *render_args
                        )
                        base_block = DisplayableWrapper(
                            self.__viewer_object.disp_getter.VBox(
                                _text_info,
                                _button,
                                spacing=0
                            ),
                            *render_args
                        )

            else:
                # Скан ещё идёт.
                text_view = __(
                    """
                    Идёт сканирование музыкальных файлов.{N}
                    В зависимости от их количества, это может занять
                    продолжительное время; но не стоит беспокоиться:
                    процедура единоразовая, данные кешируются.
                    """
                )
                base_block = DisplayableWrapper(
                    self.__viewer_object.disp_getter.Text(
                        unpack_multiline_string(text_view),
                        layout="subtitle",
                        xmaximum=int(self.__viewer_object.MAX_SIZE[0])
                    ),
                    *render_args
                )

            # Настройка показа информации.
            text_view = __("Показывать {0} описание когда нет наведения.")
            if self.__viewer_object.preferences.minimize:
                text_view = text_view.format(__("полное"))
            else:
                text_view = text_view.format(__("краткое"))
            button = DisplayableWrapper(
                self.__viewer_object.disp_getter.TextButton(
                    text_view,
                    SetField(
                        self.__viewer_object.preferences,
                        "minimize",
                        (not self.__viewer_object.preferences.minimize)
                    )
                ),
                *render_args
            )
            disp_to_box = [button]

            # Режим перетаскивания.
            text_view = __("{0} режим перетаскивания.")
            if self.__viewer_object.preferences.drag_mode:
                text_view = text_view.format(__("Отключить"))
            else:
                text_view = text_view.format(__("Включить"))
            button = DisplayableWrapper(
                self.__viewer_object.disp_getter.TextButton(
                    text_view,
                    SetField(
                        self.__viewer_object.preferences,
                        "drag_mode",
                        (not self.__viewer_object.preferences.drag_mode)
                    )
                ),
                *render_args
            )
            if self.__viewer_object.preferences.drag_mode:
                # Примечание по Drag&Drop.
                note = __(
                    """
                    Рекомендуется отключить режим перетаскивания
                    после установки оптимального положения, т.к.
                    качество рендера окна в режиме перетаскивания
                    значительно ниже.
                    """
                )
                note = DisplayableWrapper(
                    self.__viewer_object.disp_getter.Text(
                        unpack_multiline_string(note),
                        color="#f00",
                        layout="subtitle",
                        xmaximum=int(self.__viewer_object.MAX_SIZE[0])
                    ),
                    *render_args
                )
                button = DisplayableWrapper(
                    self.__viewer_object.disp_getter.VBox(
                        button,
                        note,
                        spacing=0
                    ),
                    *render_args
                )
            disp_to_box.append(button)

            if base_block:
                disp_to_box.insert(0, base_block)

            base_block = DisplayableWrapper(
                self.__viewer_object.disp_getter.VBox(*disp_to_box, spacing=0),
                *render_args
            )

            # Описание альфа бара.
            text_view = __(
                """
                А вон тем баром {0} можно установить уровень
                непрозрачности окна.
                """
            )
            if self.__viewer_object.preferences.xalign >= .5:
                _direction = __("справа")
            else:
                _direction = __("слева")
            alpha_bar_desc = DisplayableWrapper(
                self.__viewer_object.disp_getter.Text(
                    unpack_multiline_string(text_view).format(_direction),
                    layout="subtitle"
                ),
                *render_args
            )
            base_block = DisplayableWrapper(
                self.__viewer_object.disp_getter.VBox(
                    base_block,
                    alpha_bar_desc
                ),
                *render_args
            )

            # Докидываем сообщения.
            messages = tuple(
                map(
                    lambda x: DisplayableWrapper(
                        self.__viewer_object.disp_getter.Text(
                            "{{i}}{0}{{/i}}".format(x)
                        ),
                        *render_args
                    ),
                    self.status_messages
                )
            )
            if messages:
                if len(messages) >= 2:
                    messages = DisplayableWrapper(
                        self.__viewer_object.disp_getter.VBox(
                            *messages,
                            spacing=0
                        ),
                        *render_args
                    )
                else:
                    messages = messages[0]
                base_block = DisplayableWrapper(
                    self.__viewer_object.disp_getter.VBox(
                        base_block,
                        messages
                    ),
                    *render_args
                )

            return base_block

        def _copy_to_clipboard(self, string_data):
            if not isinstance(string_data, basestring):
                raise TypeError(__("Передан не текст."))
            self.add_message(
                source="_copy_to_clipboard",
                message=__("Начат процесс копирования данных.")
            )
            if isinstance(string_data, unicode):
                string_data = string_data.encode("utf_8", "ignore")
            try:
                pygame.scrap.put(pygame.scrap.SCRAP_TEXT, string_data)
            except Exception:
                self.add_message(
                    source="_copy_to_clipboard",
                    message=__("Копирование неудачно.")
                )
            else:
                self.add_message(
                    source="_copy_to_clipboard",
                    message=__("Копирование успешно.")
                )

        def _search_on_web(self, search_request, **other_params):
            other_params["status_func"] = self.add_message
            return self.search_engine.open_page(search_request, **other_params)
