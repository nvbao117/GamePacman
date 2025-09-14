import pygame
from ui import UIComponent
from utils.constants import *
from ui import Text
from ui import Button
from config import *
import sys

class MenuText(UIComponent):
    def __init__(self, app, text, color, x, y, size):
        super().__init__(app)
        self.text = text
        self.color = color
        self.size = size
        self.font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", size)
        self.label = self.font.render(self.text, True, self.color)
        self.rect = self.label.get_rect(center=(x, y))
    
    def render(self):
        self.surface.blit(self.label, self.rect)
    
    def update(self):
        pass 

class Menu(UIComponent):
    HOME = 'home'
    OPTIONS = 'option'
    
    def __init__(self, screen):
        super().__init__(screen)
        self.scene = Menu.HOME
        
        theme_img = pygame.image.load(THEME_IMG).convert_alpha()
        self.theme = pygame.transform.scale(theme_img, (self.app.WIDTH, self.app.HEIGHT))
        self.theme.set_alpha(140)
        center_x = self.app.WIDTH // 2
        center_y = self.app.HEIGHT // 2
        self.UIComponents = {
            Menu.HOME: [
                MenuText(screen, "FAC-MAN", (207, 184, 43), center_x, 320, 120),
                Button(screen, pos=(center_x, center_y-200), text="START", onclick=[self.start_game]),
                Button(screen, pos=(center_x, center_y-50), text="OPTIONS",onclick = [Menu.quit]),
                Button(screen, pos=(center_x, center_y+100), text="QUIT",onclick = [Menu.quit]),
            ],
            Menu.OPTIONS: [
                MenuText(screen, "Options Menu", WHITE, center_x, 320, 50),
                Button(screen, pos=(200, 500), text="BACK", onclick=[self.back_to_home])
            ]
        }

    def start_game(self):
        self.scene = Menu.OPTIONS

    def back_to_home(self):
        self.scene = Menu.HOME

    def render(self):
        if self.scene == Menu.OPTIONS:
            self.surface.blit(self.theme, (0, 0))
        for comp in self.UIComponents[self.scene]:
            comp.render()

    def update(self):
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, 'update'):
                comp.update()

    def eventHandling(self, event):
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, "handle_event"):
                comp.handle_event(event)

    @classmethod
    def quit(cls):
        pygame.quit()
        sys.exit(0)