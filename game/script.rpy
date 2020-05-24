
init python:
    
    from os import path
    from renpy.audio.audio import get_channel
    from AudioMetaData import (
        audio as _meta_audio,
        TagNotDefined,
        USE_WEB_DB as _META_USE_WEB_DB
    )
    
    
    class ShowMetadata(renpy.Displayable, NoRollback):
    
        __author__ = "Vladya"
        
        DEBUG = True
        
    
        def __init__(self, channel="music"):
            
            super(ShowMetadata, self).__init__()
            self.__channel = get_channel(channel)
            self.__metadata_objects = {}
            self.cache_all_tracks()
            
            
        def __call__(self, *args, **kwargs):
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
                file_exts = (".wav", ".mp2", ".mp3", ".ogg", ".opus")
            
            for _fn in renpy.list_files():
                fn = path.normpath(_fn)
                ext = path.splitext(fn)[-1].lower()
                if ext not in file_exts:
                    continue
                metadata_object = self._get_metadata_object(filename=_fn)
                if not metadata_object:
                    continue
                if not _META_USE_WEB_DB:
                    continue
                if metadata_object._web and metadata_object._web.web_tag:
                    metadata_object._web.web_tag.coveralbum_tag

        def _get_metadata_object(self, filename=None):
            
            """
            Возвращает объект AudioMetaData.audio.AudioFile либо None.
            """
            if not isinstance(filename, basestring):
                filename = self._get_playing()
            if not filename:
                return None
            if filename in self.__metadata_objects:
                return self.__metadata_objects[filename]
            with renpy.file(filename) as _file:
                try:
                    metadata_object = _meta_audio.AudioFile(
                        audio=_file,
                        datatype="fileObject",
                        filename=filename
                    )
                except TagNotDefined:
                    #  Тегов не обнаружено.
                    self.__metadata_objects[filename] = None
                    return None
                except Exception as ex:
                    #  Непредвиденная ошибка.
                    if self.DEBUG:
                        raise ex
                    self.__metadata_objects[filename] = None
                    return None
                else:
                    self.__metadata_objects[filename] = metadata_object
                    return metadata_object
                    
        def _get_playing(self):
            """
            Возвращает имя файла воспроизводимой композиции либо None.
            """
            try:
                fn = self.channel.get_playing()
            except Exception:
                return None
            if not isinstance(fn, basestring):
                return None
            filename = self.channel.file_prefix
            filename += self.channel.split_filename(fn, False)[0]
            filename += self.channel.file_suffix
            try:
                filename = renpy.fsdecode(filename)
            except Exception as ex:
                if self.DEBUG:
                    raise ex
                return None
            else:
                return filename

        def render(self, width, height, st, at):
            
            metadata = self._get_metadata_object()
            if metadata:
                _text = metadata.title_tag
            else:
                _text = "Ничего не играет"
                raise Exception(_text)
            _text = Text(_text, size=50)
            surf = renpy.render(_text, width, height, st, at)
            
            rend = renpy.Render(*map(int, surf.get_size()))
            rend.blit(surf, (0, 0))
            
            renpy.redraw(self, .0)
            return rend
            
    renpy.display.screen.define_screen(
        ShowMetadata.__name__,
        ShowMetadata(),
        layer="master"
    )
    config.overlay_screens.append(ShowMetadata.__name__)


label start:

    "Some text."
    return
