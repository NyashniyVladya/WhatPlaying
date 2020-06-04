
init 3 python in _whatPlaying:

    """
    Класс реализации доп. функционала.
    """
    
    
    class SearchBase(NoRollback):
    
        """
        Основной класс с методами поиска на различных сайтах.
        
        :NAME:
            Отображаемое имя поискового сервиса.
        :URL:
            Объект 'urllib2.urlparse.ParseResult', в котором на место поля
            query будет подставлен поисковый запрос.
        :query_search_field_name:
            Имя поля основого запроса.
        :space_is_plus:
            Если True, пробелы будут экранированы символом '+',
            если False - кодом '%20'.
            (На разных сайтах разные положения по этому поводу.)
        """
        
        NAME = None
        
        URL = None
        query_search_field_name = None
        space_is_plus = True

        
        @classmethod
        def quote(cls, *args, **kwargs):
            if cls.space_is_plus:
                return urllib.quote_plus(*args, **kwargs)
            return urllib.quote(*args, **kwargs)
        
        @classmethod
        def _status_func_decorator(cls, status_func):
            def _new_status_func(message):
                return status_func(cls.NAME, message.format(name=cls.NAME))
            return _new_status_func
        
        @classmethod
        def _create_url(cls, search_request, **params):
            """
            Создаёт ссылку.
            :search_request:
                Основной запрос. Может быть None, если запрос не явыляется
                частью 'query' (как в niconico).
            :_work_url:
                Объект 'urllib2.urlparse.ParseResult'.
                Если передан, будет использоваться вместо 'cls.URL'.
            """
            _work_url = params.pop("_work_url", cls.URL)
            if cls.query_search_field_name and search_request:
                _query = {cls.query_search_field_name: search_request}
            else:
                _query = {}
            _query.update(params)
            query = set()
            for k, v in _query.iteritems():
                if isinstance(k, unicode):
                    k = k.encode("utf_8", "ignore")
                if isinstance(v, unicode):
                    v = v.encode("utf_8", "ignore")
                k, v = map(cls.quote, map(bytes, (k, v)))
                query.add(b"{}={}".format(k, v))
            url = urllib2.urlparse.ParseResult(
                _work_url.scheme,
                _work_url.netloc,
                _work_url.path,
                _work_url.params,
                b'&'.join(query),
                _work_url.fragment
            )
            return url.geturl()

        @classmethod
        def open_page(cls, search_request, **params):
        
            """
            Основной метод. Делать запросы через него.
            """
            
            status_func = params.pop("status_func", None)
            if not callable(status_func):
                def status_func(source, message):
                    pass
            status_func = cls._status_func_decorator(status_func)
                    
            status_func(__("Формируется ссылка."))
            try:
                url = cls._create_url(search_request, **params)
            except Exception as ex:
                if DEBUG:
                    raise ex
                status_func(__("Ошибка при формировании ссылки."))
                return False

            status_func(__("Открывается страница."))
            try:
                webbrowser.open_new_tab(url)
            except Exception:
                status_func(__("Ошибка при открытии страницы."))
                return False
            else:
                status_func(__("Страница открыта."))
                return True

        
    class YouTubeSearch(SearchBase):
        
        NAME = "YouTube"
        
        URL = urllib2.urlparse.urlparse("https://www.youtube.com/results")
        query_search_field_name = "search_query"
        space_is_plus = True
        
        
    class GeniusSearch(SearchBase):
        
        NAME = "Genius"
        
        URL = urllib2.urlparse.urlparse("https://genius.com/search")
        query_search_field_name = 'q'
        space_is_plus = False
        
        
    class YandexSearch(SearchBase):
        
        NAME = "Yandex"
        
        URL = urllib2.urlparse.urlparse("https://yandex.ru/search/")
        query_search_field_name = "text"
        space_is_plus = False
        
        
    class YandexMusicSearch(YandexSearch):
        
        NAME = "Yandex Music"
        
        URL = urllib2.urlparse.urlparse("https://music.yandex.ru/search")
        
        
    class GoogleSearch(SearchBase):
        
        NAME = "Google"
        
        URL = urllib2.urlparse.urlparse("https://www.google.com/search")
        query_search_field_name = 'q'
        space_is_plus = True
        
        
    class NicoNicoSearch(SearchBase):
        
        NAME = "NicoNico Douga"
        
        URL = urllib2.urlparse.urlparse("https://www.nicovideo.jp/search/")
        space_is_plus = False
        
        @classmethod
        def _create_url(cls, search_request, **params):
            if isinstance(search_request, unicode):
                search_request = search_request.encode("utf_8", "ignore")
            search_request = cls.quote(bytes(search_request))
            url = urllib2.urlparse.urljoin(cls.URL.geturl(), search_request)
            return super(NicoNicoSearch, cls)._create_url(
                search_request=None,
                _work_url=urllib2.urlparse.urlparse(url),
                **params
            )
        
        
    class VKSearch(SearchBase):
        
        NAME = "ВКонтакте"
        
        URL = urllib2.urlparse.urlparse("https://vk.com/audio")
        query_search_field_name = 'q'
        space_is_plus = False


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
            VKSearch
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
                if self.__viewer_object._get_metadata_object():
                    text_view = __(
                        """
                        Жми {{i}}ЛКМ{{/i}} на нужную часть информации о песне,
                        чтобы скопировать её в {{i}}буфер обмена{{/i}}.{{N}}
                        Жми {{i}}ПКМ{{/i}}, чтобы найти её через сервис
                        {{i}}"{0}"{{/i}} (откроется браузер).
                        """
                    ).format(self.search_engine.NAME)
                    _text_info = DisplayableWrapper(
                        self.__viewer_object.disp_getter.Text(
                            unpack_multiline_string(text_view),
                            layout="tex"
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
