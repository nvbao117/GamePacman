# =============================================================================
# GAME_INIT_STATE.PY - STATE KHỞI TẠO GAME
# =============================================================================
# File này chứa GameInitState - state khởi tạo game với loading screen
# Hiển thị animation loading và khởi tạo game engine

import sys
import math
import pygame
import time
from pathlib import Path

from statemachine import State
from ui.button import PacManButton
from ui.neontext import NeonText
from ui.constants import *

class GameInitState(State):
    """
    GameInitState - State khởi tạo game
    - Hiển thị loading screen với animation
    - Khởi tạo game engine trong background
    - Chuyển sang game state khi hoàn thành
    """
    def __init__(self, app, machine, algorithm="BFS"):
        """
        Khởi tạo GameInitState
        Args:
            app: Tham chiếu đến App chính
            machine: StateMachine quản lý states
            algorithm: Thuật toán AI sử dụng
        """
        super().__init__(app, machine)
        self.algorithm = algorithm
        self.animation_time = 0
        self.loading_progress = 0
        self.loading_text = "Initializing Game..."
        self.loading_steps = [
            "Loading Assets...",
            "Initializing AI Engine...",
            "Setting up Game Board...",
            "Preparing Graphics...",
            "Almost Ready..."
        ]
        self.current_step = 0
        self.step_start_time = 0
        self.step_duration = 0.2  # 1 giây mỗi step
        
        # Khởi tạo game engine trong background
        self.game_engine = None
        self.init_complete = False
        self.init_start_time = time.time()
        
    def draw(self, _screen=None):
        """
        Vẽ loading screen với animation
        """
        screen = self.app.screen
        
        # Background gradient
        for y in range(self.app.HEIGHT):
            intensity = int(10 + (y / self.app.HEIGHT) * 20)
            color = (intensity, intensity, intensity + 30)
            pygame.draw.line(screen, color, (0, y), (self.app.WIDTH, y))
        
        # Animated stars
        self.animation_time += 0.05
        for i in range(100):
            x = (i * 37 + self.animation_time * 20) % self.app.WIDTH
            y = (i * 23 + self.animation_time * 10) % self.app.HEIGHT
            alpha = int(50 + 50 * math.sin(self.animation_time * 2 + i * 0.1))
            color = (alpha, alpha, alpha + 50)
            size = 1 + int(2 * math.sin(self.animation_time * 3 + i * 0.2))
            pygame.draw.circle(screen, color, (int(x), int(y)), size)
        
        # Title
        try:
            font_title = pygame.font.Font(FONT_PATH, 48)
            font_subtitle = pygame.font.Font(FONT_PATH, 24)
            font_loading = pygame.font.Font(FONT_PATH, 18)
        except:
            font_title = pygame.font.Font(None, 48)
            font_subtitle = pygame.font.Font(None, 24)
            font_loading = pygame.font.Font(None, 18)
        
        # Main title với hiệu ứng
        title_text = "PAC-MAN"
        title_surface = font_title.render(title_text, True, PAC_YELLOW)
        title_rect = title_surface.get_rect(center=(self.app.WIDTH // 2, self.app.HEIGHT // 2 - 100))
        
        # Glow effect
        for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
            glow_text = font_title.render(title_text, True, (100, 100, 0))
            screen.blit(glow_text, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Pulsing title
        pulse_alpha = int(255 + 30 * math.sin(self.animation_time * 4))
        pulse_alpha = max(200, min(255, pulse_alpha))
        title_color = (pulse_alpha, pulse_alpha, 0)
        title_surface = font_title.render(title_text, True, title_color)
        screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_text = "AI-POWERED CLASSIC"
        subtitle_surface = font_subtitle.render(subtitle_text, True, GHOST_BLUE)
        subtitle_rect = subtitle_surface.get_rect(center=(self.app.WIDTH // 2, self.app.HEIGHT // 2 - 50))
        screen.blit(subtitle_surface, subtitle_rect)
        
        # Loading text
        loading_surface = font_loading.render(self.loading_text, True, DOT_WHITE)
        loading_rect = loading_surface.get_rect(center=(self.app.WIDTH // 2, self.app.HEIGHT // 2 + 50))
        screen.blit(loading_surface, loading_rect)
        
        # Progress bar
        bar_width = 400
        bar_height = 20
        bar_x = (self.app.WIDTH - bar_width) // 2
        bar_y = self.app.HEIGHT // 2 + 100
        
        # Progress bar background
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GHOST_BLUE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Progress bar fill
        fill_width = int(bar_width * (self.loading_progress / 100))
        if fill_width > 0:
            # Gradient fill
            for i in range(fill_width):
                alpha = int(100 + (i / bar_width) * 155)
                alpha = max(0, min(255, alpha))  # Đảm bảo trong khoảng 0-255
                blue_component = alpha + 100
                blue_component = max(0, min(255, blue_component))
                color = (int(alpha), int(alpha), int(blue_component))
                pygame.draw.line(screen, color, (bar_x + i, bar_y + 2), (bar_x + i, bar_y + bar_height - 2))
        
        # Progress percentage
        progress_text = f"{int(self.loading_progress)}%"
        progress_surface = font_loading.render(progress_text, True, PAC_YELLOW)
        progress_rect = progress_surface.get_rect(center=(self.app.WIDTH // 2, bar_y + bar_height + 20))
        screen.blit(progress_surface, progress_rect)
        
        # Animated Pac-Man loading
        pac_x = bar_x + fill_width - 20
        pac_y = bar_y + bar_height // 2
        
        # Pac-Man animation
        pac_size = 8
        mouth_angle = math.pi * 0.2 + self.animation_time * 6
        mouth_width = math.pi * 0.8 + 0.3 * math.sin(self.animation_time * 8)
        
        # Draw Pac-Man
        pygame.draw.circle(screen, PAC_YELLOW, (int(pac_x), int(pac_y)), pac_size)
        pygame.draw.arc(screen, (0, 0, 0), (pac_x - pac_size, pac_y - pac_size, pac_size * 2, pac_size * 2), 
                       mouth_angle, mouth_angle + mouth_width, 3)
        
        # Eye
        eye_x = pac_x + int(3 * math.cos(mouth_angle + mouth_width/2))
        eye_y = pac_y + int(3 * math.sin(mouth_angle + mouth_width/2))
        pygame.draw.circle(screen, (0, 0, 0), (int(eye_x), int(eye_y)), 2)
        
        # Loading dots animation
        dots_y = self.app.HEIGHT // 2 + 150
        for i in range(3):
            dot_x = self.app.WIDTH // 2 - 30 + i * 20
            dot_alpha = int(100 + 155 * math.sin(self.animation_time * 3 + i * 0.5))
            dot_alpha = max(0, min(255, dot_alpha))  # Đảm bảo trong khoảng 0-255
            dot_color = (int(dot_alpha), int(dot_alpha), int(dot_alpha))  # Đảm bảo là integers
            dot_size = 3 + int(2 * math.sin(self.animation_time * 4 + i * 0.3))
            pygame.draw.circle(screen, dot_color, (int(dot_x), int(dots_y)), dot_size)
    
    def logic(self):
        """
        Cập nhật logic loading
        """
        current_time = time.time()
        
        # Cập nhật loading progress
        if not self.init_complete:
            # Tính progress dựa trên thời gian
            elapsed = current_time - self.init_start_time
            total_time = len(self.loading_steps) * self.step_duration
            self.loading_progress = min(100, (elapsed / total_time) * 100)
            
            # Cập nhật loading text theo step
            step_index = int(elapsed / self.step_duration)
            if step_index < len(self.loading_steps):
                self.loading_text = self.loading_steps[step_index]
            else:
                self.loading_text = "Ready!"
                self.init_complete = True
        else:
            # Khởi tạo game engine
            if self.game_engine is None:
                self._initialize_game_engine()
            
            # Chuyển sang game state
            if self.game_engine is not None:
                self._transition_to_game()
    
    def _initialize_game_engine(self):
        """
        Khởi tạo game engine - chỉ khởi tạo game
        """
        try:
            from engine.game import Game
            self.game_engine = Game(self.algorithm)
            if hasattr(self.game_engine, 'initialize_game'):
                self.game_engine.initialize_game()
        except Exception as e:
            self.game_engine = None
    
    def _transition_to_game(self):
        """
        Chuyển sang menu state sau khi khởi tạo xong
        """
        # Luôn chuyển sang menu state sau khi khởi tạo xong
        from states.menu_state import MenuState
        menu_state = MenuState(self.app, self.machine)
        self.replace_state(menu_state)
    
    def handle_events(self, event):
        """
        Xử lý sự kiện (có thể skip loading)
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Skip loading
                self.loading_progress = 100
                self.init_complete = True
            elif event.key == pygame.K_ESCAPE:
                # Quay về menu
                from states.menu_state import MenuState
                menu_state = MenuState(self.app, self.machine)
                self.replace_state(menu_state)
    
    def on_resume(self):
        """
        Được gọi khi state được resume
        """
        pass
    
    def on_exit(self):
        """
        Được gọi khi state bị exit
        """
        pass