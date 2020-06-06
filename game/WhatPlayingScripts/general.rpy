
init 10 python in _whatPlaying:

    """
    Disclaimer:
    Внимание! Возможны багосы с кодировками на версиях ренпая старше 6.99.12.
    (https://www.renpy.org/doc/html/changelog.html#ren-py-6-99-12)
    Багрепорты по этим версиям не принимаются.

    Код пишется с расчётом, что дефолтная строка ("") имеет тип unicode,
    а сей функционал ПайТом завёз только в RenPy 6.99.12 и моложе.

    Код является рабочим на версии 7.3.5 (последняя на момент его написания).
    """


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

            self.__is_hovered = None  # Наведение на окно.
            self.__is_true_hovered = None  # Наведение на непрозрачный пиксель.

            self.__general_displayable = None  # Основной DisplayableWrapper.
            self.__drag_object = None
            self.__extra = ExtraFunctional(viewer_object=self)

            self.__scanner_thread = MusicScanner(viewer_object=self)
            self.__scanner_thread.start()


        def __call__(self, *args, **kwargs):
            """
            Для вызова в качестве скрина.
            """
            if not self.__drag_object:
                self.__drag_object = NonRevertableDrag(
                    self,
                    draggable=True,
                    droppable=False,
                    style="_wp_drag"
                )
            ui.add(self.__drag_object)

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
            if self.__is_hovered:
                return False
            return self.preferences.minimize

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
            disp = self.__general_displayable
            if disp:
                self.__is_hovered = (
                    ((0 <= x <= disp.width) and (0 <= y <= disp.height))
                )
                if self.__is_hovered:
                    self.__is_true_hovered = (
                        disp.surface.is_pixel_opaque(x, y)
                    )
                    disp.displayable.event(ev, x, y, st)
                    raise renpy.IgnoreEvent()
                else:
                    self.__is_true_hovered = False
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
                    width=int(text_displayable.width)
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
            if is_minimized:
                spacing = cover.width_golden_small
            else:
                spacing = (cover.width * .2)
            base_block = DisplayableWrapper(
                self.disp_getter.HBox(
                    text_block,
                    (cover, {"yalign": .5}),
                    spacing=spacing
                ),
                *render_args
            )
            if is_minimized:
                return base_block

            # Оборачиваем в рамочку.
            base_block = DisplayableWrapper(
                self.disp_getter.Window(
                    base_block.displayable,
                    xpadding=7,
                    ypadding=7
                ),
                *render_args
            )

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

        def _drag_periodic(self, width, height):
            """
            Контроль положения Drag объекта. Вызывать из метода рендера.
            """
            if not self.__drag_object:
                return

            width, height = map(float, (width, height))
            x, y = self.__drag_object.x, self.__drag_object.y
            w = h = None
            if self.__general_displayable:
                w, h = self.__general_displayable.size

            grabbed = (renpy.display.focus.get_grab() is self.__drag_object)
            if grabbed and all(map(lambda _x: (_x is not None), (x, y, w, h))):
                # Юзер перетаскивает окно.
                x, y = map(float, (x, y))
                max_w = width - w
                max_h = height - h
                xalign, yalign = (x / max_w), (y / max_h)

                # Округляем align до значений, кратных 0.5.
                xalign, yalign = map(
                    lambda x: (round((max(min(x, 1.), .0) * 2.)) / 2.),
                    (xalign, yalign)
                )
                try:
                    self.preferences.alignment = (xalign, yalign)
                except Exception as ex:
                    if DEBUG:
                        raise ex
                    self.preferences.alignment = "tr"

            if (not grabbed) and all(map(lambda _x: (_x is not None), (w, h))):
                # Окно отпущено. Выравниваем.
                xanchor, yanchor = self.preferences._alignment_to_tuple(
                    self.preferences.alignment
                )
                xpos, ypos = map(
                    lambda a: ((a * .998) + .001),
                    (xanchor, yanchor)
                )
                xpos = int(((width * xpos) - (w * xanchor)))
                ypos = int(((height * ypos) - (h * yanchor)))
                if (x, y) != (xpos, ypos):
                    self.__drag_object.snap(xpos, ypos)

        def render(self, width, height, st, at):

            render_args = (width, height, st, at)
            is_minimized = self.is_minimized()

            if self.scanner_thread.scan_completed:
                # Сканирование завершено.
                if DEBUG and self.scanner_thread.exception:
                    # Во время сканирования произошла ошибка.
                    raise self.scanner_thread.exception

                if config.skipping:
                    # Перемотка.
                    general_block = DisplayableWrapper(
                        self.disp_getter.Text(__("Вж-ж-ж-ж-ж.")),
                        *render_args
                    )
                else:
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

            if self.__is_hovered:
                # Если есть наведение - рисуем экстра блок и альфа-бар.

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
            self.__general_displayable = general_block
            render_w, render_h = tuple(map(int, general_block.size))
            render_object = renpy.Render(render_w, render_h)
            render_object.blit(general_block.surface, (0, 0))

            if self.__is_true_hovered:
                render_object.add_focus(self, w=render_w, h=render_h)

            self._drag_periodic(width, height)
            renpy.redraw(self, .0)
            return render_object


    renpy.display.screen.define_screen(
        MetaDataViewer.__name__,
        MetaDataViewer(),
        layer="master"
    )
    config.overlay_screens.append(MetaDataViewer.__name__)
