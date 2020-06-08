
init 2:

    python:
        def _matrix_on_frame(matrix):
            """
            Применяет переданную матрицу на пикчу фрейма.
            """
            _frame = im.Image("whatPlayingImages/frame.png")
            return Frame(im.MatrixColor(_frame, matrix), 6, 6, tile=True)

        _empty_color = Color("#2a456e")
        _full_color = _empty_color.tint(_whatPlaying.PHI_CONST)

    style _wp_text is default:
        size _whatPlaying.recalculate_to_screen_size(22)
        layout "nobreak"
        color "#fff"
        outlines [(_whatPlaying.recalculate_to_screen_size(2), "#000", 0, 0)]

    style _wp_button_text is _wp_text:
        hover_color Color(style._wp_text.color).shade(_whatPlaying.PHI_CONST)

    style _wp_vbar is default:
        bar_vertical True
        top_bar _matrix_on_frame(im.matrix.colorize("#000", _empty_color))
        bottom_bar _matrix_on_frame(im.matrix.colorize("#000", _full_color))
        left_gutter 5
        right_gutter 5
        top_gutter 5
        bottom_gutter 5

    style _wp_hbar is default:
        bar_vertical False
        right_bar _matrix_on_frame(im.matrix.colorize("#000", _empty_color))
        left_bar _matrix_on_frame(im.matrix.colorize("#000", _full_color))
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
        background _matrix_on_frame(
            ( # Белый в тёмно-прозрачный.
                 0.1,  0.0,  0.0, 0.0, 0.0,
                 0.0,  0.1,  0.0, 0.0, 0.0,
                 0.0,  0.0,  0.1, 0.0, 0.0,
                -0.2, -0.2, -0.2, 1.0, 0.0
            )
        )
        xpadding 5
        ypadding 5

    style _wp_drag is default:
        focus_mask None
