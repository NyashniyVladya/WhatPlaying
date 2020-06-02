﻿
init -1 python in _whatPlaying:

    """
    Внимание! Возможны багосы с кодировками на версиях ренпая старше 6.99.12.
    (https://www.renpy.org/doc/html/changelog.html#ren-py-6-99-12)
    Багрепорты по этим версиям не принимаются.
    
    Код пишется с расчётом, что дефолтная строка ("") имеет тип unicode,
    а сей функционал ПайТом завёз только в RenPy 6.99.12 и моложе.
    
    Код является рабочим на версии 7.3.5 (последняя на момент его написания).
    """


    class _AlbumCover(renpy.Displayable, NoRollback):
        
        __author__ = "Vladya"
        
        placeholders_archive = path.abspath(
            renpy.loader.transfn("albumCoverPlaceholders.zip")
        )

        def __init__(self, metadata_object):
            
            super(_AlbumCover, self).__init__()
            
            if metadata_object.coveralbum_tag:
                fn, picture_bytedata = metadata_object.coveralbum_tag
                fn = "{0} {1}".format(metadata_object.__unicode__(), fn)
                image = im.Data(data=picture_bytedata, filename=fn)
            else:
                with zipfile.ZipFile(self.placeholders_archive, 'r') as _zip:
                    image = im.ZipFileImage(
                        self.placeholders_archive,
                        random.choice(_zip.namelist())
                    )

            self.__image = image
            self.__square_area_len = None


        def __eq__(self, other):
            if type(other) is not type(self):
                return False
            if self._image != other._image:
                return False
            return True

        @property
        def _image(self):
            return self.__image

        @property
        def square_area_len(self):
            """
            Длина стороны квадрата, куда будет вписана обложка альбома.
            """
            return self.__square_area_len
            
        @square_area_len.setter
        def square_area_len(self, new_len):
            if not (isinstance(new_len, (int, float)) and (new_len > .0)):
                raise ValueError(__("Неверное значение длины."))
            self.__square_area_len = float(new_len)
            renpy.redraw(self, .0)

        def render(self, width, height, st, at):
        
            if not self.square_area_len:
                # Ждём установки размера.
                renpy.redraw(self, .0)
                return renpy.Render(1, 1)
            
            surf = im.cache.get(self._image)
            old_w, old_h = map(float, surf.get_size())
            zoom_w, zoom_h = map(
                lambda x: (self.square_area_len / x),
                (old_w, old_h)
            )
            zoom = min(zoom_w, zoom_h)
            new_w, new_h = map(lambda x: int((x * zoom)), (old_w, old_h))
            
            rend = renpy.Render(new_w, new_h)
            rend.blit(
                renpy.display.scale.smoothscale(surf, (new_w, new_h)),
                (0, 0)
            )
            return rend
    
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
            self.__cover_album = _AlbumCover(metadata_object=self)
            
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


    class MetaDataViewer(renpy.Displayable, NoRollback):
    
        __author__ = "Vladya"
        
        
        MAX_SIZE = (
            (float(config.screen_width) * PHI_CONST),
            (float(config.screen_height) * PHI_CONST)
        )

        def __init__(self):
            
            super(MetaDataViewer, self).__init__()
            
            self.__preferences = Preferences(pref_id=self.__class__.__name__)
            
            self.__disp_getter = DispGetter(preferences=self.preferences)
            
            self.__channel = get_channel(self.preferences.channel_name)
            self.__channel_lock = threading.Lock()
            
            self.__metadata_objects = {}
            self._metadata_lock = threading.Lock()
            
            self.__size = None
            self.__is_hovered = None
            
            self.__general_displayable = None
            self.__extra = ExtraFunctional(viewer_object=self)
            
            self.__scanner_thread = MusicScanner(viewer_object=self)
            self.__scanner_thread.start()
            
            
        def __call__(self, *args, **kwargs):
            """
            Для вызова в качестве скрина.
            """
            xanchor, yanchor = self.preferences._alignment_to_tuple(
                self.preferences.alignment
            )
            xpos, ypos = map(lambda a: ((a * .98) + .01), (xanchor, yanchor))
            ui.add(
                Transform(self, anchor=(xanchor, yanchor), pos=(xpos, ypos))
            )
            
        @property
        def preferences(self):
            """
            Объект 'Preferences'. Различные настройки.
            """
            return self.__preferences
            
        @property
        def disp_getter(self):
            """
            Объект 'DispGetter'. Для составления Displayable.
            """
            return self.__disp_getter
            
        @property
        def extra(self):
            """
            Объект доп. функционала.
            """
            return self.__extra
            
            
        @property
        def channel(self):
            with self.__channel_lock:
                if self.__channel.name != self.preferences.channel_name:
                    self.__channel = get_channel(self.preferences.channel_name)
                return self.__channel
                
        @property
        def scanner_thread(self):
            return self.__scanner_thread

        def is_minimized(self):
            """
            Находится ли модуль в "свёрнутом" режиме.
            """
            # Пока что целиком зависит от 'self.__is_hovered'.
            # Может добавлю ещё условий: настройка юзера, например.
            return (not self.__is_hovered)
            

        def _get_metadata_object(self, filename=None, not_create=False):
            """
            Возвращает объект RenPyAudioFile либо None.
            
            :not_create:
                Возвращает объект, только если он уже есть в базе данных.
                Для доступа к файлам во время сканирования.
            """
            with self._metadata_lock:

                if not filename:
                    filename = self._get_playing()
                    if not filename:
                        return None

                if not isinstance(filename, basestring):
                    raise TypeError(__("Некорректное имя файла."))
                if filename in self.__metadata_objects:
                    return self.__metadata_objects[filename]

                if not_create:
                    return None

                try:
                    metadata_object = RenPyAudioFile(
                        filename=filename,
                        viewer_object=self
                    )
                except TagNotDefined, WrongData:
                    # Тегов не обнаружено.
                    self.__metadata_objects[filename] = None
                    return None
                except Exception as ex:
                    # Непредвиденная ошибка.
                    if DEBUG:
                        raise ex
                    self.__metadata_objects[filename] = None
                    return None
                else:
                    self.__metadata_objects[filename] = metadata_object
                    return metadata_object


        def _get_playing(self):
            """
            Обёртка над ренпаевским 'get_playing'.
            
            Возвращает имя файла воспроизводимой композиции,
            либо объект AudioData,
            либо None.
            
            Напоминалка:
                AudioData наследуется от unicode.
                Проверка на тип basestring даст True.
            """
            try:
                fn = self.channel.get_playing()
            except Exception:
                return None
            if not isinstance(fn, basestring):
                return None
            if isinstance(fn, AudioData):
                return fn
            filename = self.channel.file_prefix
            filename += self.channel.split_filename(fn, False)[0]
            filename += self.channel.file_suffix
            try:
                filename = renpy.fsdecode(filename)
            except Exception as ex:
                if DEBUG:
                    raise ex
                return None
            else:
                return filename

        def _get_position(self):
            
            """
            Возвращает значение от .0 до 1. включительно,
            выражающее отношение воспроизведённой части трека к длительности;
            либо None.
            """
            try:
                position_on_ms = float(self.channel.get_pos())
                duration_on_sec = float(self.channel.get_duration())
            except Exception:
                # Ошибка со стороны модуля renpysound при подсчёте данных.
                return None
            if not ((position_on_ms >= .0) and (duration_on_sec > .0)):
                return None
            return min((position_on_ms / (duration_on_sec * 1e3)), 1.)

        def event(self, ev, x, y, st):
        
            if self.__size:
                rend_w, rend_h = self.__size
                self.__is_hovered = ((0 <= x <= rend_w) and (0 <= y <= rend_h))
                if self.__is_hovered:
                    if self.__general_displayable:
                        self.__general_displayable.event(ev, x, y, st)
                    raise renpy.IgnoreEvent()
                else:
                    self.__extra._clean_status_messages()

        def _get_scan_block(self, is_minimized, *render_args):
            """
            Составляет блок статуса сканирования.
            
            (Возвращает DisplayableWrapper объект.)
            """
            
            text_view = self.scanner_thread._get_text_view(
                short_view=is_minimized
            )

            # Основной текст.
            text_displayable = DisplayableWrapper(
                self.disp_getter.Text(text_view),
                *render_args
            )
            if is_minimized:
                return text_displayable
            
            # Отрисовываем бар статуса сканирования.
            status_bar = DisplayableWrapper(
                self.disp_getter.HBar(
                    value=_ScanThreadStatusValue(
                        scanner_thread_object=self.scanner_thread
                    ),
                    width=int(text_displayable.width),
                    height=int(
                        (float(text_displayable.style.size) * PHI_CONST)
                    )
                ),
                *render_args
            )
            
            # Пририсовываем бар к текстовому блоку.
            base_block = DisplayableWrapper(
                self.disp_getter.VBox(text_displayable, status_bar),
                *render_args
            )
            return base_block


        def _get_base_block(self, metadata, is_minimized, *render_args):
            """
            Составляет основной блок данных:
                Название трека, статус бар, обложку.
            
            (Возвращает DisplayableWrapper объект.)
            """
            
            song_info_tuple = metadata._get_info_displayables(
                only_title=is_minimized
            )
            if song_info_tuple:
                song_info_tuple = tuple(
                    map(
                        lambda d: DisplayableWrapper(d, *render_args),
                        song_info_tuple
                    )
                )
                if len(song_info_tuple) == 1:
                    text_block = song_info_tuple[0]
                else:
                    text_block = DisplayableWrapper(
                        self.disp_getter.VBox(*song_info_tuple, spacing=0),
                        *render_args
                    )
                    
            else:
                # Данные получить не удалось.
                text_block = DisplayableWrapper(
                    self.disp_getter.Text(__("Метаданных не обнаружено.")),
                    *render_args
                )

            # Подгоняем размер обложки альбома под высоту текста.
            metadata.cover_album.square_area_len = text_block.height
            cover = DisplayableWrapper(metadata.cover_album, *render_args)

            # Горизонтальный контейнер с текстом и обложкой.
            base_block = DisplayableWrapper(
                self.disp_getter.HBox(text_block, (cover, {"yalign": .5})),
                *render_args
            )
            if is_minimized:
                return base_block

            position = self._get_position()
            # Если известна позиция трека - отрисовываем статус-бар.
            if isinstance(position, float):

                status_bar = DisplayableWrapper(
                    self.disp_getter.HBar(
                        value=_AudioPositionValue(viewer_object=self),
                        width=int(base_block.width)
                    ),
                    *render_args
                )

                # Дорисовываем бар к основному изображению.
                base_block = DisplayableWrapper(
                    self.disp_getter.VBox(base_block, status_bar),
                    *render_args
                )
            
            return base_block

        def render(self, width, height, st, at):

            render_args = (width, height, st, at)
            is_minimized = self.is_minimized()

            if self.scanner_thread.scan_completed:
                # Сканирование завершено.
                if DEBUG and self.scanner_thread.exception:
                    # Во время сканирования произошла ошибка.
                    raise self.scanner_thread.exception

                metadata = self._get_metadata_object()
                # Основной блок. Текстовые данные.
                if metadata:
                    # Музыка играет. Данные доступны.
                    general_block = self._get_base_block(
                        metadata,
                        is_minimized,
                        *render_args
                    )
                else:
                    # Тишина в эфире.
                    general_block = DisplayableWrapper(
                        self.disp_getter.Text(__("Тишина в эфире.")),
                        *render_args
                    )
                    
            else:
                # Идёт сканирование. Выводим информацию.
                general_block = self._get_scan_block(
                    is_minimized,
                    *render_args
                )
            
            if not is_minimized:
                # Если не свёрнуто - рисуем экстра блок и альфа-бар.
                
                # Рисуем экстра-блок.
                extra_block = self.__extra.get_extra_block(*render_args)
                general_block = DisplayableWrapper(
                    self.disp_getter.VBox(general_block, extra_block),
                    *render_args
                )

                # Рисуем альфа-бар.
                alpha_bar = DisplayableWrapper(
                    self.disp_getter.VBar(
                        value=FieldValue(
                            object=self.preferences,
                            field="alpha",
                            range=1.,
                            step=.01
                        ),
                        height=int(general_block.height)
                    ),
                    *render_args
                )

                # Дорисовываем бар к блоку.
                general_block = DisplayableWrapper(
                    self.disp_getter.HBox(general_block, alpha_bar),
                    *render_args
                )
                
                
            # Завершающая часть. Подгоняем готовую картинку.
            if not self.__is_hovered:
                # Если наведения нет - меняем состояние альфа-канала.
                general_block = DisplayableWrapper(
                    self.disp_getter.Transform(
                        general_block.displayable,
                        alpha=self.preferences.alpha
                    ),
                    *render_args
                )

            max_w, max_h = self.MAX_SIZE
            coefficient = min(
                (max_w / general_block.width),
                (max_h / general_block.height)
            )
            if coefficient < 1.:
                # Если картинка слишком большая - поджимаем.
                general_block = DisplayableWrapper(
                    self.disp_getter.Transform(
                        general_block.displayable,
                        zoom=coefficient
                    ),
                    *render_args
                )

            # Финальный рендер.
            self.__general_displayable = general_block.displayable
            render_w, render_h = self.__size = tuple(
                map(int, general_block.size)
            )
            render_object = renpy.Render(render_w, render_h)
            render_object.blit(general_block.surface, (0, 0))

            if self.__is_hovered:
                render_object.add_focus(self, x=0, y=0, w=render_w, h=render_h)

            renpy.redraw(self, .0)
            return render_object
            
        
            
            
    renpy.display.screen.define_screen(
        MetaDataViewer.__name__,
        MetaDataViewer(),
        layer="master"
    )
    config.overlay_screens.append(MetaDataViewer.__name__)
