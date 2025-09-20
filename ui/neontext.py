import math
import pygame
from ui.uicomponent import UIComponent
from ui.constants import FONT_PATH

class NeonText(UIComponent):
    def __init__(self, app, text, color, x, y, size, glow=False, rainbow=False, outline=False):
        super().__init__(app)
        self.text = text
        self.base_color = color
        self.size = size
        self.glow = glow
        self.rainbow = rainbow
        self.outline = outline
        self.font = pygame.font.Font(FONT_PATH, size)
        
        # Khởi tạo rect
        initial_label = self.font.render(str(self.text), True, self.base_color)
        self.rect = initial_label.get_rect(center=(x, y))
        self.animation_time = 0
        self.pulse_time = 0

    def render(self):
        text_value = self.text() if callable(self.text) else self.text
        
        self.animation_time += 0.06
        self.pulse_time += 0.1
        
        if self.rainbow:
            r = int(127 + 128 * math.sin(self.animation_time * 1.5))
            g = int(127 + 128 * math.sin(self.animation_time * 1.5 + 2.094))  # 120 degrees
            b = int(127 + 128 * math.sin(self.animation_time * 1.5 + 4.188))  # 240 degrees
            base_color = (max(100, r), max(100, g), max(100, b))  # Ensure bright colors
        else:
            base_color = self.base_color

        if self.outline:
            outline_offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]
            for ox, oy in outline_offsets:
                outline_label = self.font.render(str(text_value), True, (0, 0, 0))
                outline_rect = outline_label.get_rect(center=(self.rect.centerx + ox, self.rect.centery + oy))
                self.surface.blit(outline_label, outline_rect)

        if self.glow:
            glow_layers = [8, 6, 4, 2]
            glow_alphas = [60, 100, 140, 180]
            for offset, alpha in zip(glow_layers, glow_alphas):
                glow_color = tuple(min(255, c + 40) for c in base_color)
                glow_surf = pygame.Surface((self.rect.width + offset*2, self.rect.height + offset*2), pygame.SRCALPHA)
                glow_label = self.font.render(str(text_value), True, glow_color)
                glow_rect = glow_label.get_rect(center=(glow_surf.get_width()//2, glow_surf.get_height()//2))
                glow_surf.blit(glow_label, glow_rect)
                glow_surf.set_alpha(alpha)
                
                self.surface.blit(glow_surf, (self.rect.centerx - glow_surf.get_width()//2, 
                                            self.rect.centery - glow_surf.get_height()//2))

        label = self.font.render(str(text_value), True, base_color)
        label_rect = label.get_rect(center=self.rect.center)
        self.surface.blit(label, label_rect)

    def update(self):
        pass
