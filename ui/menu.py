import sys
import math
import pygame
import random
from config import *
from ui.uicomponent import UIComponent
from ui.text import Text
from ui.button import Button
from pathlib import Path
from game.game import Game
# Khởi tạo pygame
pygame.init()
# Lấy thông tin màn hình
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Tạo cửa sổ fullscreen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Pac-Man Arcade")

# Load ảnh nền
IMG_PATH = Path("assets/images/pm.jpg")
if not IMG_PATH.exists():
    raise FileNotFoundError(f"Background image not found at {IMG_PATH}")

bg = pygame.image.load(str(IMG_PATH)).convert_alpha()
bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

class NeonText(UIComponent):
    def __init__(self, app, text, color, x, y, size, glow=False, rainbow=False, outline=False):
        super().__init__(app)
        self.text = text
        self.base_color = color
        self.size = size
        self.glow = glow
        self.rainbow = rainbow
        self.outline = outline
        self.font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", size)
        
        # Khởi tạo rect
        initial_label = self.font.render(str(self.text), True, self.base_color)
        self.rect = initial_label.get_rect(center=(x, y))
        self.animation_time = 0
        self.pulse_time = 0

    def render(self):
        # Lấy text động
        text_value = self.text() if callable(self.text) else self.text
        
        # Animation timing
        self.animation_time += 0.06
        self.pulse_time += 0.1
        
        if self.rainbow:
            # Pac-Man style rainbow - bright colors
            r = int(127 + 128 * math.sin(self.animation_time * 1.5))
            g = int(127 + 128 * math.sin(self.animation_time * 1.5 + 2.094))  # 120 degrees
            b = int(127 + 128 * math.sin(self.animation_time * 1.5 + 4.188))  # 240 degrees
            base_color = (max(100, r), max(100, g), max(100, b))  # Ensure bright colors
        else:
            base_color = self.base_color

        # Outline for better readability on colorful background
        if self.outline:
            outline_offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]
            for ox, oy in outline_offsets:
                outline_label = self.font.render(str(text_value), True, (0, 0, 0))
                outline_rect = outline_label.get_rect(center=(self.rect.centerx + ox, self.rect.centery + oy))
                self.surface.blit(outline_label, outline_rect)

        # Glow effect for neon look
        if self.glow:
            glow_layers = [(8, 60), (6, 100), (4, 140), (2, 180)]
            for offset, alpha in glow_layers:
                glow_color = tuple(min(255, c + 40) for c in base_color)
                glow_surf = pygame.Surface((self.rect.width + offset*2, self.rect.height + offset*2), pygame.SRCALPHA)
                glow_label = self.font.render(str(text_value), True, glow_color)
                glow_rect = glow_label.get_rect(center=(glow_surf.get_width()//2, glow_surf.get_height()//2))
                glow_surf.blit(glow_label, glow_rect)
                glow_surf.set_alpha(alpha)
                
                self.surface.blit(glow_surf, (self.rect.centerx - glow_surf.get_width()//2, 
                                            self.rect.centery - glow_surf.get_height()//2))

        # Main text
        label = self.font.render(str(text_value), True, base_color)
        label_rect = label.get_rect(center=self.rect.center)
        self.surface.blit(label, label_rect)

    def update(self):
        pass

class PacManButton(Button):
    def __init__(self, app, pos, text, onclick, primary=False):
        super().__init__(app, pos, text, size=(300, 70), font_size=20, onclick=onclick)
        self.original_pos = pos
        self.animation_time = 0
        self.is_hovered = False
        self.primary = primary
        self.onclick = onclick if onclick else []
        
        # Pac-Man inspired colors
        if primary:
            self.base_color = (255, 255, 0)  # Pac-Man yellow
            self.hover_color = (255, 200, 0)
            self.accent_color = (255, 100, 100)  # Cherry red
        else:
            self.base_color = (0, 100, 255)  # Ghost blue
            self.hover_color = (100, 150, 255)
            self.accent_color = (255, 255, 255)
        
        # Animation properties
        self.scale = 1.0
        self.target_scale = 1.0
        
    def render(self):
        self.animation_time += 0.08
        
        # Smooth scaling animation
        scale_diff = self.target_scale - self.scale
        self.scale += scale_diff * 0.15
        
        # Subtle float animation
        float_offset = int(3 * math.sin(self.animation_time * 2))
        current_pos = (self.original_pos[0], self.original_pos[1] + float_offset)
        
        # Button dimensions
        base_width, base_height = 300, 70
        button_width = int(base_width * self.scale)
        button_height = int(base_height * self.scale)
        
        button_rect = pygame.Rect(0, 0, button_width, button_height)
        button_rect.center = current_pos
        
        # Color selection
        if self.is_hovered:
            self.target_scale = 1.05
            main_color = self.hover_color
            # Pulsing effect
            pulse = int(20 * math.sin(self.animation_time * 6))
            main_color = tuple(min(255, max(50, c + pulse)) for c in main_color)
        else:
            self.target_scale = 1.0
            main_color = self.base_color

        # Draw button background - arcade style
        self._draw_arcade_button(button_rect, main_color)
        
        # Text rendering
        font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", int(20 * self.scale))
        text_str = self.text.text if hasattr(self.text, 'text') else str(self.text)
        
        # Text with outline for readability
        text_color = (0, 0, 0) if self.primary else (255, 255, 255)
        
        # Outline
        outline_offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        outline_color = (255, 255, 255) if self.primary else (0, 0, 0)
        for ox, oy in outline_offsets:
            outline_text = font.render(text_str, True, outline_color)
            outline_rect = outline_text.get_rect(center=(current_pos[0] + ox, current_pos[1] + oy))
            self.surface.blit(outline_text, outline_rect)
        
        # Main text
        text_surface = font.render(text_str, True, text_color)
        text_rect = text_surface.get_rect(center=current_pos)
        self.surface.blit(text_surface, text_rect)
        
        # Update collision rect
        self.rect = button_rect
    
    def _draw_arcade_button(self, rect, main_color):
        """Draw arcade-style button with 3D effect"""
        # Shadow/depth
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(self.surface, (0, 0, 0, 100), shadow_rect, border_radius=15)
        
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

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                for callback in self.onclick:
                    callback()

class Menu(UIComponent):
    HOME = 'home'
    OPTIONS = 'option'

    def __init__(self, app):
        super().__init__(app)
        self.scene = Menu.HOME
        self.animation_time = 0
        self.selected_algorithm = 'BFS'
        self._algorithms = ['BFS', 'DFS', 'IDS', 'UCS']
        
        # Use original background without overlay
        self.background = bg
        
        # Screen dimensions
        center_x = self.app.WIDTH // 2
        center_y = self.app.HEIGHT // 2
        
        # Pac-Man inspired colors
        pac_yellow = (255, 255, 0)
        ghost_blue = (0, 150, 255)
        ghost_pink = (255, 184, 255)
        ghost_red = (255, 0, 0)
        ghost_orange = (255, 184, 82)
        dot_white = (255, 255, 255)
        
        self.algo_button = None
        
        self.UIComponents = {
            Menu.HOME: [
                # Title - Pac-Man style with rainbow effect
                NeonText(app, "PAC-MAN", pac_yellow, center_x, center_y - 180, 90, 
                        glow=True, rainbow=True, outline=True),
                NeonText(app, "ARCADE ADVENTURE", ghost_pink, center_x, center_y - 110, 24, 
                        glow=True, outline=True),
                
                # Arcade-style buttons
                PacManButton(app, pos=(center_x, center_y - 30), text="▶ START GAME", 
                           onclick=[self.start_game], primary=True),
                PacManButton(app, pos=(center_x, center_y + 50), text="⚙ OPTIONS", 
                           onclick=[self.show_options]),
                PacManButton(app, pos=(center_x, center_y + 130), text="✕ EXIT", 
                           onclick=[Menu.quit]),
                
                # Game info
                NeonText(app, "Use Arrow Keys to Navigate", dot_white, center_x, center_y + 200, 14, 
                        outline=True),
                NeonText(app, "● Collect All Dots to Win! ●", ghost_orange, center_x, center_y + 225, 12, 
                        glow=True, outline=True),
            ],
            
            Menu.OPTIONS: [
                NeonText(app, "OPTIONS", ghost_pink, center_x, center_y - 120, 60, 
                        glow=True, outline=True),
                NeonText(app, "Choose AI Algorithm:", dot_white, center_x, center_y - 60, 18, outline=True),
                
                PacManButton(app, pos=(center_x, center_y - 10), text=f"AI: {self.selected_algorithm}", 
                           onclick=[self.cycle_algorithm], primary=True),
                PacManButton(app, pos=(center_x, center_y + 70), text="❮ BACK", 
                           onclick=[self.back_to_home]),
                           
                # Algorithm info
                NeonText(app, lambda: self.get_algo_description(), (255, 255, 255), 
                        center_x, center_y + 140, 14, outline=True),
            ]
        }
        
        # Save algorithm button reference
        self.algo_button = self.UIComponents[Menu.OPTIONS][2]

    def get_algo_description(self):
        descriptions = {
            'BFS': "● Breadth-First: Explores level by level ●",
            'DFS': "● Depth-First: Goes deep first ●", 
            'IDS': "● Iterative Deepening: Best of both worlds ●",
            'UCS': "● Uniform Cost: Finds optimal path ●"
        }
        return descriptions.get(self.selected_algorithm, "")

    def start_game(self):
        game = Game(self.selected_algorithm)
        game.startGame()
        while game.running:
            game.update()

            self.scene = Menu.HOME

    def cycle_algorithm(self):
        """Đổi thuật toán theo vòng tròn"""
        idx = self._algorithms.index(self.selected_algorithm)
        self.selected_algorithm = self._algorithms[(idx + 1) % len(self._algorithms)]
        
        # Cập nhật nhãn nút
        if self.algo_button is not None:
            self.algo_button.text = f"AI: {self.selected_algorithm}"

    def show_options(self):
        """Chuyển đến màn hình options"""
        self.scene = Menu.OPTIONS

    def back_to_home(self):
        """Quay lại màn hình chính"""
        self.scene = Menu.HOME

    def render(self):
        # Draw full background image without overlay
        self.surface.blit(self.background, (0, 0))
        
        # Update animation time
        self.animation_time += 0.02
        
        # Add subtle Pac-Man style dots floating around
        self.draw_pac_dots()
        
        # Render UI components
        for comp in self.UIComponents[self.scene]:
            comp.render()

    def draw_pac_dots(self):
        """Draw floating Pac-Man style dots"""
        # Classic Pac-Man dots
        dot_colors = [(255, 255, 255), (255, 255, 0), (255, 184, 255), (255, 0, 0)]
        
        for i in range(15):
            # Horizontal movement
            x = (self.animation_time * 50 + i * 200) % (self.app.WIDTH + 100) - 50
            y = 150 + (i * 67) % 400  # Distribute vertically
            
            # Gentle floating
            y += 10 * math.sin(self.animation_time * 3 + i * 0.8)
            
            # Size animation
            base_size = 4 if i % 4 == 0 else 3  # Some larger dots (power pellets)
            size = base_size + int(1 * math.sin(self.animation_time * 4 + i))
            
            color = dot_colors[i % len(dot_colors)]
            
            # Draw dot with glow
            if 0 <= x <= self.app.WIDTH and 0 <= y <= self.app.HEIGHT:
                # Glow effect
                glow_surf = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, 80), (size*2, size*2), size*2)
                self.surface.blit(glow_surf, (int(x-size*2), int(y-size*2)))
                
                # Main dot
                pygame.draw.circle(self.surface, color, (int(x), int(y)), size)

    def update(self):
        """Update all components in current scene"""
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, 'update'):
                comp.update()

    def eventHandling(self, event):
        """Handle events for all components in current scene"""
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, "handle_event"):
                comp.handle_event(event)

    @classmethod
    def quit(cls):
        """Quit the game"""
        pygame.quit()
        sys.exit(0)