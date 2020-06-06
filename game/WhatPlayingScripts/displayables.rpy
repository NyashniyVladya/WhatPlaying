
init 4 python in _whatPlaying:

    """
    Свои Displayable классы.
    """


    class _AlbumCover(renpy.Displayable, NoRollback):

        __author__ = "Vladya"

        def __init__(self, metadata_object, viewer_object):

            super(_AlbumCover, self).__init__()

            if metadata_object.coveralbum_tag:
                fn, picture_bytedata = metadata_object.coveralbum_tag
                fn = "{0} {1}".format(metadata_object.__unicode__(), fn)
            else:
                with renpy.file("albumCoverPlaceholders.zip") as _raw_zipfile:
                    with zipfile.ZipFile(_raw_zipfile, 'r') as _archive:
                        _placeholder = random.choice(_archive.infolist())
                        with _archive.open(_placeholder, 'r') as _imagefile:
                            fn = _imagefile.name
                            picture_bytedata = b""
                            while True:
                                chunk = _imagefile.read((2 ** 20))
                                if not chunk:
                                    break
                                picture_bytedata += chunk

            self.__image = im.Data(data=picture_bytedata, filename=fn)
            self.__itunes_link = getattr(metadata_object, "trackViewUrl", None)
            self.__square_area_len = None
            self.__viewer_object = viewer_object

            self.__itunes_button = None
            self.__itunes_button_offset = None

        def __eq__(self, other):
            return (self is other)

        @property
        def _image(self):
            return self.__image

        @property
        def _itunes_link(self):
            return self.__itunes_link

        @property
        def square_area_len(self):
            """
            Длина стороны квадрата, в который будет вписана обложка альбома.
            """
            return self.__square_area_len

        @square_area_len.setter
        def square_area_len(self, new_len):
            if not (isinstance(new_len, (int, float)) and (new_len > .0)):
                raise ValueError(__("Неверное значение длины."))
            self.__square_area_len = float(new_len)
            renpy.redraw(self, .0)

        def event(self, ev, x, y, st):
            if self.__itunes_button and self.__itunes_button_offset:
                xoff, yoff = self.__itunes_button_offset
                x -= xoff
                y -= yoff
                if all(
                    (
                        (0 <= x <= self.__itunes_button.height),
                        (0 <= y <= self.__itunes_button.width)
                    )
                ):
                    self.__itunes_button.displayable.event(ev, x, y, st)
                    raise renpy.IgnoreEvent()

        def render(self, width, height, st, at):

            if not self.square_area_len:
                # Ждём установки размера.
                renpy.redraw(self, .0)
                return renpy.Render(1, 1)

            render_args = (width, height, st, at)
            image = DisplayableWrapper(self._image, *render_args)

            zoom = min(
                map(lambda x: (self.square_area_len / x), image.size)
            )
            image = DisplayableWrapper(
                self.__viewer_object.disp_getter.Transform(
                    image.displayable,
                    zoom=zoom
                ),
                *render_args
            )

            render_object = renpy.Render(*map(int, image.size))
            render_object.blit(image.surface, (0, 0))

            if self._itunes_link:
                # Если есть ссылка на трек в iTunes.
                _logo = DisplayableWrapper(
                    im.MatrixColor(
                        im.Image("whatPlayingImages/itunes_logo.jpg"),
                        ( # Удаляем белый цвет жипег подложки.
                             1.0,  0.0,  0.0, 0.0, 0.0,
                             0.0,  1.0,  0.0, 0.0, 0.0,
                             0.0,  0.0,  1.0, 0.0, 0.0,
                            -1.0, -1.0, -1.0, 3.0, 0.0
                        )
                    ),
                    *render_args
                )
                zoom = min(
                    (image.width / _logo.width),
                    (image.height / _logo.height)
                )
                _logo = DisplayableWrapper(
                    self.__viewer_object.disp_getter.Transform(
                        _logo.displayable,
                        zoom=(zoom * (1. - PHI_CONST))
                    ),
                    *render_args
                )

                button = self.__itunes_button = DisplayableWrapper(
                    self.__viewer_object.disp_getter.ImageButton(
                        idle_image=_logo.displayable,
                        hover_image=None, # Автогенерация hover.
                        clicked=Function(try_open_page, self._itunes_link)
                    ),
                    *render_args
                )

                _pref = self.__viewer_object.preferences
                xanchor, yanchor = _pref._alignment_to_tuple(_pref.alignment)
                xpos, ypos = map(
                    lambda a: ((a * .98) + .01),
                    (xanchor, yanchor)
                )

                xpos, ypos = self.__itunes_button_offset = (
                    int(((image.width * xpos) - (button.width * xanchor))),
                    int(((image.height * ypos) - (button.height * yanchor)))
                )

                render_object.blit(button.surface, (xpos, ypos))

                render_object.add_focus(
                    self,
                    x=xpos,
                    y=ypos,
                    w=int(button.width),
                    h=int(button.height)
                )

            return render_object

    class NonRevertableDrag(Drag, NoRollback):
        pass
