# labeling/selection_manager.py - Verwaltung von aktiver Auswahl und Interaktionen

class SelectionManager:
    def __init__(self):
        self.active_shape = None
        self.hovered_shape = None
        self.moving = False
        self.hovered_corner_index = None  # 0-3 wenn über Ecke, sonst None
        self.resizing = False
        self.last_mouse_pos = None

    def select_shape(self, shape, mouse_pos):
        self.active_shape = shape
        self.moving = True
        self.last_mouse_pos = mouse_pos


    def set_hovered_corner(self, corner_index):
        self.hovered_corner_index = corner_index

    def clear_hover(self):
        self.hovered_shape = None
        self.hovered_corner_index = None

    def start_resizing(self, shape, corner_index, mouse_pos):
        self.active_shape = shape
        self.hovered_corner_index = corner_index
        self.resizing = True
        self.last_mouse_pos = mouse_pos

    def stop_resizing(self):
        self.resizing = False
        self.active_shape = None
        self.hovered_corner_index = None

    def move_active_shape(self, new_mouse_pos):
        if not self.active_shape or not self.moving:
            return

        delta = new_mouse_pos - self.last_mouse_pos
        self.last_mouse_pos = new_mouse_pos

        if hasattr(self.active_shape, "rect"):
            self.active_shape.rect.translate(delta)

    def clear_selection(self):
        self.active_shape = None
        self.moving = False
        self.last_mouse_pos = None
    
    def is_shape_active(self, shape):
        return self.active_shape == shape

    def set_hovered_shape(self, shape):
        self.hovered_shape = shape    

    def is_shape_active(self, shape):
        return self.active_shape == shape
    
    def is_shape_hovered(self, shape):
        return self.hovered_shape == shape
    
    def move_resize(self, new_mouse_pos):
        if not self.active_shape or not self.resizing:
            return

        delta = new_mouse_pos - self.last_mouse_pos
        self.last_mouse_pos = new_mouse_pos

        rect = self.active_shape.rect

        if self.hovered_corner_index == 0:  # Top-Left
            rect.setTopLeft(rect.topLeft() + delta)
        elif self.hovered_corner_index == 1:  # Top-Right
            rect.setTopRight(rect.topRight() + delta)
        elif self.hovered_corner_index == 2:  # Bottom-Left
            rect.setBottomLeft(rect.bottomLeft() + delta)
        elif self.hovered_corner_index == 3:  # Bottom-Right
            rect.setBottomRight(rect.bottomRight() + delta)

        # Optional: Mindestgrößenprüfung (z.B. verhindern, dass Box "kippt")
        min_size = 5
        if rect.width() < min_size or rect.height() < min_size:
            # Box nicht kleiner als Mindestgröße werden lassen
            rect.setWidth(max(rect.width(), min_size))
            rect.setHeight(max(rect.height(), min_size))

        self.active_shape.rect = rect