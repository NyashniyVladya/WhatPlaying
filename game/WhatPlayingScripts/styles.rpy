
init 2:

    style _wp_text is default:
        layout "nobreak"
    
    style _wp_button_text is _wp_text:
        hover_color "#888"
        
    # Пикчи
    style _wp_vbar is default:
        bar_vertical True
        top_bar Frame("gui/bar/top.png")
        bottom_bar Frame("gui/bar/bottom.png")
        
    style _wp_hbar is default:
        bar_vertical False
        left_bar Frame("gui/bar/left.png")
        right_bar Frame("gui/bar/right.png")
    
    style _wp_vbox is default:
        box_layout "vertical"
    style _wp_hbox is default:
        box_layout "horizontal"
    
    style _wp_button is default:
        focus_mask None
        xpadding 0
        ypadding 0

    style _wp_transform is default
