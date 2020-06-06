
init 3 python in _whatPlaying:

    """
    Формирование ссылок для поиска.
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

        __author__ = "Vladya"

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
                Основной запрос. Может быть None, если запрос не является
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

        NAME = "Яндекс"

        URL = urllib2.urlparse.urlparse("https://yandex.ru/search/")
        query_search_field_name = "text"
        space_is_plus = False

    class YandexMusicSearch(YandexSearch):

        NAME = "Яндекc Музыка"

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

    class WikipediaSearch(SearchBase):

        NAME = "Википедия"

        URL = urllib2.urlparse.urlparse("https://wikipedia.org/w/index.php")
        query_search_field_name = "search"
        space_is_plus = True
