import pygame

# the fontmanager class handles loading fonts at different sizes efficiently

class FontManager():
    def __init__(self):
        self.fonts = {}
    def get_font(self,name,size):
        font_entry = self.fonts.get(name)
        font = None
        if font_entry:
            font = font_entry.get(size)
        if font:
            return font
        else:
            self.fonts[name] = {}
            self.fonts[name][size] = pygame.font.Font(f"assets/fonts/{name}",size)
            font = self.fonts[name].get(size)
            print(f"Loaded font {name}")
            return font