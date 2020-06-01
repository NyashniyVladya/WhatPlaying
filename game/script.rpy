
init python:
    config.debug_sound = True
    config.debug_equality = True
    
screen test_music:

    default music_array = tuple(
        sorted(_whatPlaying.MusicScanner._get_all_tracks(), key=lambda x: x[0])
    )
    showif music_array:
        hbox:
            align (.5, .5)
            ysize .75
            spacing 70
            box_reverse True
            text _("Что включить?") size 100 yalign 1.
            viewport id "test_music":
                yalign 1.
                mousewheel True
                draggable True
                xfill False
                yfill False
                vbox:
                    for basename, renpy_name in music_array:
                        textbutton basename:
                            text_size  30
                            action Play("music", renpy_name)
            vbar value YScrollValue("test_music") yalign 1.
    else:
        text _("Не найдено треков в файлах игры."):
            size 50
            align (.75, .75)


label start:
    call screen test_music
    return
