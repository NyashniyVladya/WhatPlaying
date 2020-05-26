
init -1 python in _whatPlaying:

    """
    Внимание! Возможны багосы с кодировками на версиях ренпая старше 6.99.12.
    (https://www.renpy.org/doc/html/changelog.html#ren-py-6-99-12)
    Багрепорты по этим версиям не принимаются.
    
    Код пишется с расчётом, что дефолтная строка ("") имеет тип unicode,
    а сей функционал ПайТом завёз только в RenPy 6.99.12 и моложе.
    
    Код является рабочим на версии 7.3.5 (последняя на момент его написания).
    """
    
    import io
    import random
    import zipfile
    from os import path
    from renpy.audio.audio import get_channel
    from AudioMetaData import (
        audio,
        TagNotDefined,
        WrongData
    )
    from store import (
        im,
        config,
        NoRollback,
        Transform,
        Text,
        HBox
    )
    try:
        from store import AudioData
    except ImportError:
        class AudioData(object):
            """
            Для более старых версий ренпая, где ещё не было AudioData.
            """
            pass
    
    
    DEBUG = True  # Флаг для отладки.
    
    
    def quote_text(text):
        """
        Экранирование спец. символов ренпая.
        """
        assert isinstance(text, basestring), "Передан не текст."
        for old, new in {'[': "[[", '{': "{{"}.iteritems():
            text = text.replace(old, new)
        return text

    
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
            self.__size = (100., 100.)
            
        @property
        def size(self):
            return self.__size
            
        @size.setter
        def size(self, new_size):
            assert all(filter(lambda x: isinstance(x, (int, float)), new_size))
            assert len(new_size) == 2
            self.__size = tuple(map(float, new_size))
            renpy.redraw(self, .0)
            
        def render(self, width, height, st, at):
            
            _preload_surf = renpy.render(self.__image, width, height, st, at)
            old_w, old_h = map(float, _preload_surf.get_size())
            w, h = self.__size
            
            surf = renpy.render(
                Transform(self.__image, zoom=min((w / old_w), (h / old_h))),
                width,
                height,
                st,
                at
            )
            new_w, new_h = map(int, surf.get_size())

            rend = renpy.Render(new_w, new_h)
            rend.blit(surf, (0, 0))

            return rend

    
    class RenPyAudioFile(audio.AudioFile):
    
        def __init__(self, filename):
        
            """
            Обёртка над основным классом, для работы в ренпае.
            :filename:
                Имя файла в ренпаевском формате, либо объект AudioData.
            """
            
            assert isinstance(filename, basestring), "Передан неверный тип."
            
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
                    
            self.__cover_album = _AlbumCover(metadata_object=self)
            
        @property
        def cover_album(self):
            return self.__cover_album
            
        def _get_text_view(self):
            
            """
            Возвращает текст в том виде, в котором он будет показан на экране
            либо None.
            
            Текст будет иметь вид:
            
                Артист - Название (Альбом)
                                07.11.1917
                                      Жанр

            """
            
            text_view = '\n'.join(
                filter(
                    bool,
                    (
                        self.__unicode__(),
                        self.date_tag,
                        self.genre_tag
                    )
                )
            )
            if not text_view:
                return None
            return quote_text(text_view)


    class ShowMetadata(renpy.Displayable, NoRollback):
    
        __author__ = "Vladya"

        def __init__(self, channel="music"):
            
            super(ShowMetadata, self).__init__()
            self.__channel = get_channel(channel)
            self.__metadata_objects = {}
            
            self.cache_all_tracks()
            
            
        def __call__(self, *args, **kwargs):
            """
            Для вызова в качестве скрина.
            """
            ui.add(Transform(self, anchor=(1., .0), pos=(.99, .01)))
            
        @property
        def channel(self):
            return self.__channel
            
        @channel.setter
        def channel(self, new_channel):
            new_channel = get_channel(new_channel)
            self.__channel = new_channel
        

        def cache_all_tracks(self, file_exts=None):
            
            if not isinstance(file_exts, (list, tuple)):
                file_exts = {".wav", ".mp2", ".mp3", ".ogg", ".opus"}
            
            for _fn in renpy.list_files():
                fn = path.normpath(_fn)
                ext = path.splitext(fn)[-1].lower()
                if ext not in file_exts:
                    continue
                self._get_metadata_object(filename=_fn)


        def _get_metadata_object(self, filename=None):
            """
            Возвращает объект RenPyAudioFile либо None.
            """
            if not isinstance(filename, basestring):
                filename = self._get_playing()
            if not filename:
                return None
            if filename in self.__metadata_objects:
                return self.__metadata_objects[filename]
                
            try:
                metadata_object = RenPyAudioFile(filename=filename)
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
                duration_on_min = float(self.channel.get_duration())
            except Exception:
                # Ошибка со стороны модуля renpysound при подсчёте данных.
                return None
            if not ((position_on_ms >= .0) and (duration_on_min > .0)):
                return None
            # TODO


        def render(self, width, height, st, at):
        
            metadata = self._get_metadata_object()
            text_view = (metadata._get_text_view() if metadata else None)
            if text_view:
            
                text_displayable = Text(text_view, size=30, text_align=1.)
                text_surf = renpy.render(
                    text_displayable,
                    width,
                    height,
                    st,
                    at
                )
                text_w, text_h = text_surf.get_size()

                metadata.cover_album.size = (text_h, text_h)
                cover_surf = renpy.render(
                    metadata.cover_album,
                    width,
                    height,
                    st,
                    at
                )
                cover_w, cover_h = cover_surf.get_size()
                
                displayable = HBox(
                    text_displayable,
                    metadata.cover_album,
                    spacing=int((float(cover_w) / 3.))
                )
                surf = renpy.render(displayable, width, height, st, at)
                rend = renpy.Render(*map(int, surf.get_size()))
                rend.blit(surf, (0, 0))
                
            else:
                rend = renpy.Render(1, 1)
            
            renpy.redraw(self, .0)
            return rend
            
     
            
            
    renpy.display.screen.define_screen(
        ShowMetadata.__name__,
        ShowMetadata(),
        layer="master"
    )
    config.overlay_screens.append(ShowMetadata.__name__)

