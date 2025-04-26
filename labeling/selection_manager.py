# labeling/selection_manager.py - Verwaltung von aktiver Auswahl und Interaktionen

class SelectionManager:
    def __init__(self):
        self.active_shape = None
        self.hovered_shape = None
        self.moving = False
        self.last_mouse_pos = None

    def select_shape(self, shape, mouse_pos):
        self.active_shape = shape
        self.moving = True
        self.last_mouse_pos = mouse_pos

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