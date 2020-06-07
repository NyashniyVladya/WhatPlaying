
init 2:

    style _wp_text is default:
        size _whatPlaying.recalculate_to_screen_size(22)
        layout "nobreak"
        color "#fff"
        outlines [(_whatPlaying.recalculate_to_screen_size(2), "#000", 0, 0)]

    style _wp_button_text is _wp_text:
        hover_color Color(style._wp_text.color).shade(_whatPlaying.PHI_CONST)

    style _wp_vbar is default:
        bar_vertical True
        top_bar Frame("whatPlayingImages/bar_empty.png", 6, 6, tile=True)
        bottom_bar Frame("whatPlayingImages/bar_full.png", 6, 6, tile=True)
        left_gutter 5
        right_gutter 5
        top_gutter 5
        bottom_gutter 5

    style _wp_hbar is default:
        bar_vertical False
        right_bar Frame("whatPlayingImages/bar_empty.png", 6, 6, tile=True)
        left_bar Frame("whatPlayingImages/bar_full.png", 6, 6, tile=True)
        left_gutter 5
        right_gutter 5
        top_gutter 5
        bottom_gutter 5

    style _wp_vbox is default:
        box_layout "vertical"

    style _wp_hbox is default:
        box_layout "horizontal"

    style _wp_button is default:
        focus_mask None

    style _wp_imagebutton is _wp_button:
        focus_mask True

    style _wp_transform is default

    style _wp_window is default:
        background Frame("whatPlayingImages/frame.png", 6, 6, tile=True)
        xpadding 5
        ypadding 5

    style _wp_drag is default:
        focus_mask None
