
init 4 python in _whatPlaying:

    """
    Прочие классы для различных оптимизаций.
    """

    class RenPyAudioFile(audio.AudioFile, NoRollback):

        def __init__(self, filename, viewer_object):

            """
            Обёртка над основным классом, для работы в ренпае.
            :filename:
                Имя файла в ренпаевском формате, либо объект AudioData.
            """

            if not isinstance(filename, basestring):
                raise TypeError(__("Неверный тип имени файла."))

            if isinstance(filename, AudioData):
                super(RenPyAudioFile, self).__init__(
                    audio=filename.data,
                    datatype="bytes",
                    filename=filename
                )
            else:
                with renpy.file(filename) as _file:
                    super(RenPyAudioFile, self).__init__(
                        audio=_file,
                        datatype="fileObject",
                        filename=filename
                    )

            self.__viewer_object = viewer_object
            self.__cover_album = _AlbumCover(
                metadata_object=self,
                viewer_object=viewer_object
            )

        def __nonzero__(self):
            return bool(self.title_tag)

        @property
        def cover_album(self):
            return self.__cover_album

        def _get_info_displayables(self, only_title=False):

            """
            Возвращает кортеж Displayable с информацией о песне или None.
            (Для размещения в вертикальном контейнере)

            :only_title:
                Вернуть только Displayable названия.

            Без флага 'only_title' кортеж будет иметь вид:
                (
                    "Артист - Название",
                               "Альбом",
                           "07.11.1917",
                                 "Жанр"
                )

            """
            artist = title = album = date = genre = None
            if self.artist_tag:
                artist = "{{b}}{0}{{/b}}".format(quote_text(self.artist_tag))
            if self.title_tag:
                title = "{{b}}{0}{{/b}}".format(quote_text(self.title_tag))
            if self.album_tag:
                album = quote_text(self.album_tag)
            if self.date_tag:
                date = quote_text(self.date_tag)
            if self.genre_tag:
                genre = "{{i}}{0}{{/i}}".format(quote_text(self.genre_tag))

            if only_title:
                if title:
                    return (self.__viewer_object.disp_getter.Text(title),)
                return None

            result = []
            artist_title_text_data = " - ".join(filter(bool, (artist, title)))
            for show_text, source_text in zip(
                (artist_title_text_data, album, date, genre),
                (
                    ' '.join(filter(bool, (self.artist_tag, self.title_tag))),
                    self.album_tag,
                    self.date_tag,
                    self.genre_tag
                )

            ):
                if source_text:
                    _tb = self.__viewer_object.disp_getter.TextButton(
                        show_text,
                        clicked=Function(
                            self.__viewer_object.extra._copy_to_clipboard,
                            source_text
                        ),
                        alternate=Function(
                            self.__viewer_object.extra._search_on_web,
                            source_text
                        )
                    )
                    result.append(_tb)
            if not result:
                return None
            return tuple(result)

    class _AudioPositionValue(BarValue, FieldEquality, NoRollback):

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

    class _ScanThreadStatusValue(BarValue, FieldEquality, NoRollback):

        identity_fields = ["scanner"]

        def __init__(self, scanner_thread_object):
            self.scanner = scanner_thread_object

        def get_adjustment(self):
            self.adjustment = ui.adjustment(
                range=1.,
                value=self.scanner.scan_status,
                adjustable=False
            )
            return self.adjustment

        def periodic(self, st):
            self.adjustment.change(self.scanner.scan_status)
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
