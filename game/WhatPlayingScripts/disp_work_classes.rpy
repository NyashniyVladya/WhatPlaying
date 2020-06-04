
init 4 python in _whatPlaying:

    """
    Классы для различных взаимодействий с Displayable.
    """


    class DispGetter(NoRollback):
        
        """
        Для унификации Displayable объектов по свойствам и стилю.
        """
        
        __author__ = "Vladya"
        
        def __init__(self, preferences):
            self.__preferences = preferences

        @staticmethod
        def _add_args_object(kwargs_dict):
            """
            Добавляет в словарь аргументов ключ _args,
            со значением всех аргументов инициализации.
            
            Для проверки идентичности объектов при кешировании.
            """
            if not isinstance(kwargs_dict, __builtin__.dict):
                raise TypeError(__("'kwargs_dict' должен быть словарём."))
            args = kwargs_dict.pop("_args", None)
            if not isinstance(args, renpy.display.core.DisplayableArguments):
                args = renpy.display.core.DisplayableArguments()
            args.__dict__.update(kwargs_dict)
            kwargs_dict["_args"] = args
            return kwargs_dict


        def Text(self, text, **text_kwargs):
            """
            Возвращает объект текста.
            """
            if not isinstance(text, basestring):
                try:
                    text = unicode(text)
                except Exception:
                    raise TypeError(__("Передан не текст."))

            kwargs = {
                "style": "_wp_text",
                "text": text,
                "size": recalculate_to_screen_size(35),
                "text_align": self.__preferences.xalign
            }
            kwargs.update(text_kwargs)
            
            return Text(**self._add_args_object(kwargs))
            
        @classmethod
        def VBar(cls, **bar_kwargs):
            bar_kwargs["vertical"] = True
            return cls._Bar(**bar_kwargs)
        
        
        @classmethod
        def HBar(cls, **bar_kwargs):
            bar_kwargs["vertical"] = False
            return cls._Bar(**bar_kwargs)
        
        @classmethod
        def _Bar(cls, **bar_kwargs):
            """
            Возвращает объект бара.
            """
            kwargs = {}
            if bar_kwargs.get("vertical", False):
                # Вертикальный бар.
                kwargs = {
                    "width": recalculate_to_screen_size(22),
                    "style": "_wp_vbar"
                }
            else:
                # Горизонтальный.
                kwargs = {
                    "height": recalculate_to_screen_size(22, False),
                    "style": "_wp_hbar"
                }
            kwargs.update(bar_kwargs)
            
            # Если переданы конкретные размеры - они должны быть неизменны.
            if "width" in kwargs:
                kwargs.update(
                    dict.fromkeys(
                        ("xsize", "xminimum", "xmaximum"),
                        kwargs["width"]
                    )
                )

            if "height" in kwargs:
                kwargs.update(
                    dict.fromkeys(
                        ("ysize", "yminimum", "ymaximum"),
                        kwargs["height"]
                    )
                )

            return renpy.display.behavior.Bar(**cls._add_args_object(kwargs))
            

        def TextButton(self, text, clicked, **tb_kwargs):
            """
            Возвращает объект кнопки.
            Немного видоизменённая реализация Пайтомовской TextButton,
            с учётом особенностей проекта.
            """
            
            kwargs = {
                "text_text": text,
                "text_style": "_wp_button_text",
                "style": "_wp_button",
                "clicked": clicked
            }
            kwargs.update(tb_kwargs)
            
            text_kwargs, button_kwargs = renpy.easy.split_properties(
                kwargs,
                "text_",
                ""
            )
            button_kwargs["child"] = self.Text(**text_kwargs)
            return Button(**self._add_args_object(button_kwargs))


        def VBox(self, *disps, **_kwargs):
            _kwargs["_vertical"] = True
            return self._Box(*disps, **_kwargs)


        def HBox(self, *disps, **_kwargs):
            _kwargs["_vertical"] = False
            return self._Box(*disps, **_kwargs)


        def _Box(self, *_disps, **_kwargs):

            """
            Упаковывает диспы в контейнер.
            
            Работает только с 'DisplayableWrapper' объектами,
            т.к. нужно определять размеры по ходу составления.
            
            Также можно передать кортеж из двух элементов,
            где первый - DisplayableWrapper,
            а второй - словарь с параметрами только для этого диспа.
            """

            if len(_disps) < 2:
                raise TypeError(__("Объектов должно быть не менее чем 2."))

            _ArgClass = namedtuple("disp_and_dict", "disp kwargs")
            disps = []
            for d in _disps:
                d_kwargs = {}
                if isinstance(d, tuple):
                    if len(d) == 1:
                        d = d[0]
                    elif len(d) == 2:
                        d, d_kwargs = d
                    else:
                        raise ValueError(__("Неверный размер кортежа."))

                if not isinstance(d, DisplayableWrapper):
                    raise TypeError(
                        __("Принимаются только 'DisplayableWrapper' объекты.")
                    )
                if not isinstance(d_kwargs, __builtin__.dict):
                    raise TypeError(__("Аргументы должны быть в словаре."))
                disps.append(_ArgClass(d, d_kwargs))
                    
            xalign, yalign = self.__preferences._alignment_to_tuple(
                self.__preferences.alignment
            )

            if _kwargs.get("_vertical", True):
                _BoxClass = VBox
                kwargs = {
                    "transform_xalign": xalign,
                    "style": "_wp_vbox",
                    "spacing": int(disps[-1].disp.height_golden_small),
                    "box_reverse": (yalign > .5)
                }
                
            else:
                _BoxClass = HBox
                kwargs = {
                    "transform_yalign": yalign,
                    "style": "_wp_hbox",
                    "spacing": int(disps[-1].disp.width_golden_small),
                    "box_reverse": (xalign < .5)
                }
            kwargs.update(_kwargs)
            
            transform_kwargs, box_kwargs = renpy.easy.split_properties(
                kwargs,
                "transform_",
                ""
            )
            
            _childs = []
            for d in disps:
                d_kwargs = transform_kwargs.copy()
                # Обновляем общие пропы собственными, если есть.
                d_kwargs.update(d.kwargs)
                _childs.append(self.Transform(d.disp.displayable, **d_kwargs))

            box_kwargs["_childs"] = tuple(_childs)
            box_kwargs = self._add_args_object(box_kwargs)
            childs = box_kwargs.pop("_childs")
            box_kwargs.pop("_vertical", None)
            return _BoxClass(*childs, **box_kwargs)
            
        @classmethod
        def Transform(cls, child, **_kwargs):
            kwargs = {
                "child": child,
                "style": "_wp_transform"
            }
            kwargs.update(_kwargs)
            return Transform(**cls._add_args_object(kwargs))

    class DisplayableWrapper(NoRollback):
    
        """
        Инкапсуляция диспов, для извлечения отрендеренных параметров,
        как атрибутов.
        
        Экземпляры НЕ являются Displayable.
        """
        
        __author__ = "Vladya"
        
        DISP_CACHE = []
        CACHE_MAX_SIZE = 5000
        cache_lock = threading.Lock()
        
        def __init__(self, disp, width, height, st, at):
            
            if not isinstance(disp, renpy.display.core.Displayable):
                raise Exception(__("Передан не 'renpy.Displayable'."))

            with self.cache_lock:

                for cached_disp in self.DISP_CACHE:
                    if self.is_equal_two_disp(disp, cached_disp):
                        disp = cached_disp
                        if isinstance(disp, renpy.display.behavior.Bar):
                            if isinstance(disp.value, BarValue):
                                disp.adjustment = disp.value.get_adjustment()
                        break
                else:
                    self.DISP_CACHE.append(disp)

                if len(self.DISP_CACHE) > self.CACHE_MAX_SIZE:
                    self.__class__.DISP_CACHE = []
                    
            
            self.__displayable = disp
            self.__render_args = (width, height, st, at)
            
            self.__surface = None
            
        def __getattr__(self, key):
            if key.startswith("__") and key.endswith("__"):
                raise AttributeError(key)
            return getattr(self.displayable, key)
            
        @classmethod
        def _clear_cache(cls):
            with cls.cache_lock:
                cls.DISP_CACHE = []

        def is_equal_two_disp(self, disp1, disp2):
        
            """
            Проверяет, идентичны ли два диспа по аргументам инициализатора.
            """

            # Оба объекта должны быть диспами
            if not isinstance(disp1, renpy.display.core.Displayable):
                return False
            if not isinstance(disp2, renpy.display.core.Displayable):
                return False
                
            # Если определён свой метод - проверяем им.
            if hasattr(disp1, "__eq__"):
                return disp1.__eq__(disp2)
                
            # Базовая проверка от класса 'Displayable' на тип и всё такое.
            if not disp1._equals(disp2):
                return False
                
            # Проверка по аргументам инициализатора.
            args1, args2 = disp1._args, disp2._args
            if not isinstance(args1, renpy.display.core.DisplayableArguments):
                return False
            if not isinstance(args2, renpy.display.core.DisplayableArguments):
                return False

            keys = frozenset(args1.__dict__.iterkeys())
            if keys != frozenset(args2.__dict__.iterkeys()):
                return False
            if not keys:
                return False
                
            for key in keys:
                value1, value2 = getattr(args1, key), getattr(args2, key)
                if not self.__is_equal_two_objects(value1, value2):
                    return False

            return True

        def __is_equal_two_objects(self, value1, value2):
            """
            Проверка идентичности двух объектов.
            Дополнение к предыдущему методу.
            """
            if type(value1) is not type(value2):
                return False
            if isinstance(value1, (__builtin__.list, tuple)):
                # Контейнеры рекурсивно отправляем на проверку.
                if len(value1) != len(value2):
                    return False
                for _value1, _value2 in zip(value1, value2):
                    if not self.__is_equal_two_objects(_value1, _value2):
                        return False
            elif isinstance(value1, renpy.display.core.Displayable):
                # Диспы тоже.
                if not self.is_equal_two_disp(value1, value2):
                    return False
            else:
                # Иные типы проверяем обычным образом.
                if value1 != value2:
                    return False
            return True


        @property
        def displayable(self):
            """
            Сам Displayable.
            """
            return self.__displayable
            
        @property
        def surface(self):
            """
            Объект рендера.
            """
            if not self.__surface:
                self.__surface = renpy.render(
                    self.displayable,
                    *self.__render_args
                )
            return self.__surface
            
        @property
        def size(self):
            """
            Кортеж высоты и ширины.
            (float)
            """
            return tuple(map(float, self.surface.get_size()))

        @property
        def width(self):
            """
            Ширина отрендеренного диспа.
            (float)
            """
            width, height = self.size
            return width

        @property
        def height(self):
            """
            Высота.
            (float)
            """
            width, height = self.size
            return height
            
        @property
        def width_golden_small(self):
            """
            Возвращает меньшее значение золотого сечения от ширины.
            """
            return (self.width * (1. - PHI_CONST))
            
        @property
        def width_golden_big(self):
            """
            Возвращает большее значение золотого сечения от ширины.
            """
            return (self.width * PHI_CONST)
            
        @property
        def height_golden_small(self):
            """
            Возвращает меньшее значение золотого сечения от высоты.
            """
            return (self.height * (1. - PHI_CONST))
            
        @property
        def height_golden_big(self):
            """
            Возвращает большее значение золотого сечения от высоты.
            """
            return (self.height * PHI_CONST)


