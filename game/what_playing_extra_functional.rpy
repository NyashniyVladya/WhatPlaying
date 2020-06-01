
init -3 python in _whatPlaying:

    """
    Класс реализации доп. функционала.
    """

    class ExtraFunctional(NoRollback):
    
        """
        Копирование в БО, вывод доп. информации и прочее.
        """
        
        __author__ = "Vladya"
        
        def __init__(self, viewer_object):
        
            self.__viewer_object = viewer_object

            
            # Всякие информационные сообщения о успешном копировании и пр.
            self.__status_messages = OrderedDict()
            self.__status_lock = threading.Lock()

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
                if self.__viewer_object._get_metadata_object():
                    text_view = __(
                        """
                        Жми {i}ЛКМ{/i} на нужную часть информации о песне,
                        чтобы скопировать её в {i}буфер обмена{/i}.{N}
                        Жми {i}ПКМ{/i}, чтобы найти её на YouTube
                        (откроется браузер).
                        """
                    )
                    base_block = DisplayableWrapper(
                        self.__viewer_object.disp_getter.Text(
                            unpack_multiline_string(text_view),
                            layout="tex"
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
                        layout="tex"
                    ),
                    *render_args
                )

            # Описание альфа бара.
            text_view = __(
                """
                А вон тем баром {0} можно установить уровень
                непрозрачности окна.
                """
            )
            if self.__viewer_object.preferences.xalign > .5:
                _direction = __("справа")
            else:
                _direction = __("слева")
            alpha_bar_desc = DisplayableWrapper(
                self.__viewer_object.disp_getter.Text(
                    unpack_multiline_string(text_view).format(_direction),
                    layout="tex"
                ),
                *render_args
            )
            if base_block:
                base_block = DisplayableWrapper(
                    self.__viewer_object.disp_getter.VBox(
                        base_block,
                        alpha_bar_desc
                    ),
                    *render_args
                )
            else:
                base_block = alpha_bar_desc
                
            # Докидываем сообщения.
            text_view = '\n'.join(
                map(lambda x: "{{i}}{0}{{/i}}".format(x), self.status_messages)
            )
            if text_view:
                messages = DisplayableWrapper(
                    self.__viewer_object.disp_getter.Text(text_view),
                    *render_args
                )
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
            #TODO
            
        def _search_on_youtube(self, string_data):
            if not isinstance(string_data, basestring):
                raise TypeError(__("Передан не текст."))
            self.add_message(
                source="_search_on_youtube",
                message=__("Страница открывается.")
            )
            #TODO
