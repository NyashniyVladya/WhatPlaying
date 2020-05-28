

init python:
    
    from os import path

    def _get_menu_items():
        """
        Для проверки работоспособности.
        """

        yield ("Что включить?", None)
        for _fn in renpy.list_files():
            fn, ext = path.splitext(path.basename(path.normpath(_fn)))
            if ext.lower() in _whatPlaying.MusicScanner.file_exts:
                yield (fn, _fn)
                
                
                
    config.debug_sound = True
    
label start:
    while True:
        $ renpy.music.play(menu(list(_get_menu_items())))
    return
