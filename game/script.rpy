
init 100 python:

    config.debug = True
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
            spacing _whatPlaying.recalculate_to_screen_size(300)
            hbox:
                yalign 1.
                box_reverse True
                spacing _whatPlaying.recalculate_to_screen_size(50)
                viewport id "test_music":
                    yalign 1.
                    mousewheel True
                    draggable True
                    xfill False
                    yfill False
                    vbox:
                        for basename, renpy_name in music_array:
                            textbutton basename:
                                style "_wp_button"
                                text_style "_wp_button_text"
                                action Play("music", renpy_name)
                vbar value YScrollValue("test_music") yalign 1.
            vbox:
                yalign 1.
                text _("Что включить?") xalign .0 size 80 style "_wp_text"
                textbutton _("Выйти") xalign 1. action Return()
    else:
        vbox:
            align (.75, .75)
            text _("Не найдено треков в файлах игры.") size 50
            textbutton _("Выйти") action Return()


label start:
    scene expression im.Image("background2.png")
    while True:
        menu:
            "Собрать билду":
                if _whatPlaying.DEBUG:
                    "Внимание! Билда собирается с включённым режимом дебага."
                $ _what_playing_build._RPA.create_build(
                    build_name="WhatPlaying"
                )
                "Готово."
            "Настройки рендера":
                call screen _choose_renderer
            "Переключить язык":
                $ renpy.change_language(
                    menu(
                        (("Русский", "None"),) + tuple(
                            map(
                                lambda x: (x.title(), x),
                                renpy.known_languages()
                            )
                        )
                    )
                )
            "Тестировать":
                call screen test_music
    return
