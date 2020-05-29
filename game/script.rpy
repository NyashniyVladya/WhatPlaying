
init python:
    config.debug_sound = True
    
screen test_music:

    default _get_func = _whatPlaying.MusicScanner._get_all_tracks
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
                for basename, renpy_name in _get_func():
                    textbutton basename:
                        text_size  30
                        action Play("music", renpy_name)
        vbar value YScrollValue("test_music") yalign 1.


label start:
    call screen test_music
    return
