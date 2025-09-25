# =============================================================================
# BUTTON.PY - HỆ THỐNG BUTTON CHO GAME PAC-MAN
# =============================================================================
# File này chứa các class Button để tạo UI buttons
# Hỗ trợ hover effects, click events, và keyboard navigation

import pygame
import math
from ui.uicomponent import UIComponent
from ui.constants import *


class Button(UIComponent):
    """
    Class Button cơ bản cho UI
    - Hỗ trợ hover effects và click events
    - Có thể tùy chỉnh kích thước, font, và vị trí
    - Hỗ trợ keyboard navigation
    """
    def __init__(self, app, pos, text, size=(300, 70), font_size=22, onclick=None, topleft=False):
        """
        Khởi tạo button
        Args:
            app: Tham chiếu đến App chính
            pos: Vị trí button (x, y)
            text: Text hiển thị trên button
            size: Kích thước button (width, height)
            font_size: Kích thước font
            onclick: List các callback khi click
            topleft: Có sử dụng topleft positioning không
        """
        super().__init__(app)
        self.text = str(text)
        self.w, self.h = size
        # Tính toán vị trí dựa trên topleft flag
        self.x = pos[0] - self.w // 2 if not topleft else pos[0]
        self.y = pos[1] - self.h // 2 if not topleft else pos[1]
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        
        # Trạng thái button
        self.is_hovered = False      # Có đang hover không
        self._pressed_inside = False # Có đang press bên trong không
        self.is_focused = False      # Có đang focus không (keyboard nav)
        
        # Callbacks và font
        self.onclick = list(onclick) if onclick else []
        self.font_path = FONT_PATH
        self.font_size = font_size
        self._font = pygame.font.Font(self.font_path, self.font_size)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._pressed_inside = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed_inside and self.rect.collidepoint(event.pos):
                self._trigger_click()
            self._pressed_inside = False

    
    def _trigger_click(self):
        """Trigger button click action"""
        for cb in self.onclick:
            cb()
    
    def set_focus(self, focused):
        self.is_focused = focused
        # self.is_focused = focused

    def render(self):
        # Basic rounded button
        base_color = (40, 40, 40)
        hover_color = (60, 60, 60)
        color = hover_color if self.is_hovered else base_color
        pygame.draw.rect(self.surface, color, self.rect, border_radius=10)
        pygame.draw.rect(self.surface, (200, 200, 200), self.rect, width=2, border_radius=10)

        # Centered text
        label = self._font.render(self.text, True, (255, 255, 255))
        text_rect = label.get_rect(center=self.rect.center)
        self.surface.blit(label, text_rect)

    def update(self):
        pass


class PacManButton(Button):
    def __init__(self, app, pos, text, onclick=None, primary=False):
        super().__init__(app, pos, text, size=BUTTON_SIZE, font_size=BUTTON_FONT_SIZE, onclick=onclick)
        self.original_pos = pos
        self.animation_time = 0
        self.primary = primary
        self.is_focused = False

        # Pac-Man inspired colors
        if primary:
            self.base_color = PAC_YELLOW
            self.hover_color = (255, 210, 0)
            self.accent_color = (255, 100, 100)
            self.text_color = (0, 0, 0)
            self.outline_color = (255, 255, 255)
        else:
            self.base_color = GHOST_BLUE
            self.hover_color = (100, 170, 255)
            self.accent_color = (255, 255, 255)
            self.text_color = (255, 255, 255)
            self.outline_color = (0, 0, 0)

        self.scale = 1.0
        self.target_scale = 1.0

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEMOTION:
            # Update hover flag for animation
            self.is_hovered = self.rect.collidepoint(event.pos)
        
    def render(self):
        self.animation_time += ANIMATION_SPEED

        # Smooth scaling animation
        scale_diff = self.target_scale - self.scale
        self.scale += scale_diff * 0.15

        # Subtle float animation
        float_offset = int(FLOAT_AMPLITUDE * math.sin(self.animation_time * 2))
        current_pos = (self.original_pos[0], self.original_pos[1] + float_offset)

        # Button dimensions
        base_width, base_height = BUTTON_SIZE
        button_width = int(base_width * self.scale)
        button_height = int(base_height * self.scale)

        button_rect = pygame.Rect(0, 0, button_width, button_height)
        button_rect.center = current_pos

        # Color selection
        if self.is_hovered or self.is_focused:
            self.target_scale = 1.05
            main_color = self.hover_color
            pulse = int(PULSE_AMPLITUDE * math.sin(self.animation_time * 6))
            main_color = tuple(min(255, max(50, c + pulse)) for c in main_color)
        else:
            self.target_scale = 1.0
            main_color = self.base_color

        # Draw button background - arcade style
        self._draw_arcade_button(button_rect, main_color)

        # Text rendering (with outline)
        font = pygame.font.Font(self.font_path, int(20 * self.scale))
        text_str = self.text

        # Outline
        outline_offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for ox, oy in outline_offsets:
            outline_text = font.render(text_str, True, self.outline_color)
            outline_rect = outline_text.get_rect(center=(current_pos[0] + ox, current_pos[1] + oy))
            self.surface.blit(outline_text, outline_rect)

        # Main text
        text_surface = font.render(text_str, True, self.text_color)
        text_rect = text_surface.get_rect(center=current_pos)
        self.surface.blit(text_surface, text_rect)

        # Update collision rect to match scaled button
        self.rect = button_rect

    def _draw_arcade_button(self, rect, main_color):
        # Shadow with alpha surface
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect(), border_radius=15)
        self.surface.blit(shadow_surf, (rect.x + 4, rect.y + 4))

        # Button base (darker)
        dark_color = tuple(max(0, c - 60) for c in main_color)
        pygame.draw.rect(self.surface, dark_color, rect, border_radius=15)

        # Button top (lighter)
        top_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height - 6)
        pygame.draw.rect(self.surface, main_color, top_rect, border_radius=15)

        # Highlight
        highlight_rect = pygame.Rect(rect.x + 8, rect.y + 8, rect.width - 16, rect.height // 3)
        highlight_color = tuple(min(255, c + 40) for c in main_color)
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, (*highlight_color, 120), highlight_surf.get_rect(), border_radius=8)
        self.surface.blit(highlight_surf, highlight_rect)

        # Border
        border_color = self.accent_color if self.is_hovered else (200, 200, 200)
        pygame.draw.rect(self.surface, border_color, top_rect, width=3, border_radius=15)