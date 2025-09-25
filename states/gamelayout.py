
# =============================================================================
# GAMELAYOUT.PY - LAYOUT UI CHO GAME PAC-MAN
# =============================================================================
# File này chứa GameLayout - quản lý giao diện UI trong game
# Bao gồm control panel, game area, và các hiệu ứng visual

import pygame
import math
from ui.uicomponent import UIComponent
from ui.constants import *
from ui.selectbox import SelectBox


class GameLayout(UIComponent):
    """
    GameLayout - Quản lý layout UI cho game Pac-Man
    - Chia màn hình thành game area và control panel
    - Quản lý thông tin game (score, lives, level, algorithm)
    - Có hiệu ứng visual và animation đẹp mắt
    - Hỗ trợ selectbox để chọn thuật toán AI
    """
    def __init__(self, app):
        """
        Khởi tạo GameLayout
        Args:
            app: Tham chiếu đến App chính
        """
        super().__init__(app)
        # Các rectangle chính
        self.game_area_rect = None      # Khu vực game
        self.control_panel_rect = None  # Panel điều khiển
        self.background_rect = None     # Background chính
        
        # Setup layout dimensions
        self._setup_layout()
        
        # Thông tin game
        self.score = 0          # Điểm số
        self.lives = 55          # Số mạng
        self.level = 1          # Level hiện tại
        self.algorithm = "BFS"  # Thuật toán AI
        self.is_playing = False # Trạng thái play/pause
        
        # Tùy chọn thuật toán cho selectbox
        self.algorithm_options = ["BFS", "DFS", "A*", "UCS", "IDS"]
        
        # Khởi tạo selectbox
        self.algorithm_selectbox = None
        self._setup_selectbox()
        
        # Animation
        self.animation_time = 0
        
    def _setup_layout(self):
        """
        Setup kích thước layout cho game
        - Chia màn hình thành game area và control panel
        - Giữ aspect ratio của game gốc
        - Tối ưu hóa không gian cho game
        """
        # Background chính chiếm toàn bộ màn hình
        self.background_rect = pygame.Rect(0, 0, self.app.WIDTH, self.app.HEIGHT)
        
        panel_width = 300 
        panel_height = self.app.HEIGHT
        panel_x = self.app.WIDTH - panel_width
        panel_y = 0
        
        self.control_panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Game area - giữ aspect ratio đúng cho Pac-Man
        # Tính toán kích thước tối ưu dựa trên kích thước game gốc
        from constants import SCREENSIZE
        original_width, original_height = SCREENSIZE
        
        # Để chỗ cho title và margins
        available_width = self.app.WIDTH - panel_width - 40  # 20px margin mỗi bên
        available_height = self.app.HEIGHT - 120  # Thêm chỗ cho title
        
        # Tính scale để giữ aspect ratio
        scale_x = available_width / original_width
        scale_y = available_height / original_height
        scale = min(scale_x, scale_y)  # Dùng scale nhỏ hơn để giữ aspect ratio
        
        # Tính kích thước game area cuối cùng
        game_width = int(original_width * scale)
        game_height = int(original_height * scale)
        
        # Căn giữa game area - di chuyển xuống nhiều hơn
        game_x = (self.app.WIDTH - panel_width - game_width) // 2
        game_y = 100  # Thêm chỗ cho title
        
        self.game_area_rect = pygame.Rect(game_x, game_y, game_width, game_height)
    
    def _setup_selectbox(self):
        """Setup the algorithm selectbox"""
        selectbox_x = self.control_panel_rect.x + 15
        selectbox_y = 640  
        selectbox_width = self.control_panel_rect.width - 30 
        selectbox_height = 40  
        
        self.algorithm_selectbox = SelectBox(
            selectbox_x, selectbox_y, selectbox_width, selectbox_height,
            self.algorithm_options, font_size=12
        )
        
        # Use game font
        try:
            self.algorithm_selectbox.font = pygame.font.Font(FONT_PATH, 12)
        except:
            self.algorithm_selectbox.font = pygame.font.Font(None, 12)
        
        self.algorithm_selectbox.bg_color = (70, 70, 100) 
        self.algorithm_selectbox.border_color = PAC_YELLOW  
        self.algorithm_selectbox.selected_color = (120, 200, 240) 
        self.algorithm_selectbox.hover_color = (90, 90, 120) 
        self.algorithm_selectbox.text_color = DOT_WHITE  
        
        # Set initial selection based on current algorithm
        if self.algorithm in self.algorithm_options:
            self.algorithm_selectbox.selected_option = self.algorithm_options.index(self.algorithm)
    
    def set_game_info(self, score=0, lives=3, level=1, algorithm="BFS"):
        """
        Cập nhật thông tin game
        Args:
            score: Điểm số hiện tại
            lives: Số mạng còn lại
            level: Level hiện tại
            algorithm: Thuật toán AI đang sử dụng
        """
        self.score = score
        self.lives = lives
        self.level = level
        self.algorithm = algorithm
    
    def render(self):
        """
        Render toàn bộ game layout
        - Vẽ background với hiệu ứng
        - Vẽ game area frame
        - Vẽ control panel
        - Vẽ thông tin game
        """
        # Vẽ background chính
        self._draw_background()
        
        # Vẽ frame cho game area
        self._draw_game_area()
        
        # Vẽ control panel
        self._draw_control_panel()
        
        # Vẽ thông tin game
        self._draw_game_info()
    
    def _draw_background(self):
        """Draw the main background with enhanced transparency effects"""
        # Create a more subtle gradient background
        for y in range(self.app.HEIGHT):
            intensity = int(8 + (y / self.app.HEIGHT) * 15)  # More subtle gradient
            color = (intensity, intensity, intensity + 20)
            pygame.draw.line(self.surface, color, (0, y), (self.app.WIDTH, y))
        
        # Add animated starfield with more transparency
        self.animation_time += 0.02
        for i in range(150):  # More stars for better effect
            x = (i * 37 + self.animation_time * 10) % self.app.WIDTH
            y = (i * 23 + self.animation_time * 5) % self.app.HEIGHT
            alpha = int(30 + 20 * math.sin(self.animation_time * 2 + i * 0.1))  # More transparent
            color = (alpha, alpha, alpha + 30)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.2))
            pygame.draw.circle(self.surface, color, (int(x), int(y)), size)
        
        # Add floating particles with transparency
        for i in range(30):  # More particles
            x = (self.animation_time * 15 + i * 80) % self.app.WIDTH
            y = 100 + 200 * math.sin(self.animation_time * 1.5 + i * 0.3)
            alpha = int(40 + 30 * math.sin(self.animation_time * 2 + i))  # More transparent
            color = (alpha, alpha // 2, alpha + 20)
            pygame.draw.circle(self.surface, color, (int(x), int(y)), 2)
        
        # Add nebula-like effects for more depth
        for i in range(5):
            x = (self.animation_time * 5 + i * 200) % self.app.WIDTH
            y = (self.animation_time * 3 + i * 150) % self.app.HEIGHT
            alpha = int(15 + 10 * math.sin(self.animation_time * 1 + i))
            color = (alpha, alpha // 3, alpha + 15)
            size = 30 + int(20 * math.sin(self.animation_time * 0.5 + i))
            pygame.draw.circle(self.surface, color, (int(x), int(y)), size)
    
    def _draw_game_area(self):
        overlay_surface = pygame.Surface((self.game_area_rect.width, self.game_area_rect.height), pygame.SRCALPHA)
        
        # Semi-transparent background with gradient
        for y in range(self.game_area_rect.height):
            alpha = int(20 + (y / self.game_area_rect.height) * 10)  # Very subtle gradient
            color = (alpha, alpha, alpha + 15, alpha)
            pygame.draw.line(overlay_surface, color, (0, y), (self.game_area_rect.width, y))
        
        # Add subtle animated particles inside game area
        for i in range(20):
            x = (self.animation_time * 8 + i * 50) % self.game_area_rect.width
            y = (self.animation_time * 5 + i * 30) % self.game_area_rect.height
            alpha = int(15 + 10 * math.sin(self.animation_time * 2 + i * 0.3))
            color = (alpha, alpha, alpha + 20, alpha)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.2))
            pygame.draw.circle(overlay_surface, color, (int(x), int(y)), size)
        
        # Blit the overlay to create transparency effect
        self.surface.blit(overlay_surface, self.game_area_rect.topleft)
        
        # Enhanced outer glow effect - more dramatic
        for i in range(6, 0, -1):
            alpha = int(40 - i * 6)
            color = (alpha, alpha + 40, alpha + 80)
            glow_rect = self.game_area_rect.inflate(i * 3, i * 3)
            pygame.draw.rect(self.surface, color, glow_rect, 2)
        
        # Main outer frame with animated glow
        glow_intensity = int(100 + 50 * math.sin(self.animation_time * 2))
        pygame.draw.rect(self.surface, (glow_intensity, glow_intensity + 50, glow_intensity + 100), self.game_area_rect, 4)
        pygame.draw.rect(self.surface, GHOST_BLUE, self.game_area_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), self.game_area_rect, 1)
        
        # Inner frame with enhanced animation
        inner_rect = self.game_area_rect.inflate(-12, -12)
        pulse = int(3 + 2 * math.sin(self.animation_time * 4))
        pulse_r = max(0, min(255, int(255 + 30 * math.sin(self.animation_time * 3))))
        pulse_g = max(0, min(255, int(255 + 30 * math.sin(self.animation_time * 3))))
        pulse_b = max(0, min(255, int(100 + 30 * math.sin(self.animation_time * 3))))
        pulse_color = (pulse_r, pulse_g, pulse_b)
        pygame.draw.rect(self.surface, pulse_color, inner_rect, pulse)
        pygame.draw.rect(self.surface, (255, 255, 150), inner_rect, 1)
        
        # Corner decorations removed for cleaner interface
        
        # Title positioned above game area, centered
        try:
            font_title = pygame.font.Font(FONT_PATH, 32)
            font_subtitle = pygame.font.Font(FONT_PATH, 16)
        except:
            font_title = pygame.font.Font(None, 32)
            font_subtitle = pygame.font.Font(None, 16)
        
        title_text = "PAC-MAN GAME"
        title_surface = font_title.render(title_text, True, (255, 255, 0))
        title_rect = title_surface.get_rect(center=(self.game_area_rect.centerx, 40))
        
        # Simple glow effect - just 2 layers for clean look
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_text = font_title.render(title_text, True, (100, 100, 0))
            self.surface.blit(glow_text, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Main title with subtle pulsing
        pulse_alpha = int(255 + 20 * math.sin(self.animation_time * 3))
        pulse_alpha = max(200, min(255, pulse_alpha))
        title_color = (pulse_alpha, pulse_alpha, 0)
        title_surface = font_title.render(title_text, True, title_color)
        self.surface.blit(title_surface, title_rect)
        
        # Subtitle positioned below title
        subtitle_text = "AI-POWERED CLASSIC"
        subtitle_surface = font_subtitle.render(subtitle_text, True, (200, 200, 255))
        subtitle_rect = subtitle_surface.get_rect(center=(self.game_area_rect.centerx, 70))
        
        # Subtitle with subtle glow
        for offset in [(1, 1), (-1, -1)]:
            subtitle_glow = font_subtitle.render(subtitle_text, True, (50, 50, 100))
            self.surface.blit(subtitle_glow, (subtitle_rect.x + offset[0], subtitle_rect.y + offset[1]))
        
        # Main subtitle
        subtitle_color = (200, 200, 255)
        subtitle_surface = font_subtitle.render(subtitle_text, True, subtitle_color)
        self.surface.blit(subtitle_surface, subtitle_rect)
    
    def _draw_control_panel(self):
        """Draw the control panel with enhanced transparency effects"""
        # Create semi-transparent panel background
        panel_surface = pygame.Surface((self.control_panel_rect.width, self.control_panel_rect.height), pygame.SRCALPHA)
        
        # Enhanced gradient with transparency
        for i in range(self.control_panel_rect.height):
            alpha = int(30 + (i / self.control_panel_rect.height) * 20)
            color = (alpha, alpha, alpha + 25, alpha)
            pygame.draw.line(panel_surface, color, 
                           (0, i), (self.control_panel_rect.width, i))
        
        # Add subtle animated particles
        for i in range(15):
            x = (self.animation_time * 5 + i * 30) % self.control_panel_rect.width
            y = (self.animation_time * 3 + i * 40) % self.control_panel_rect.height
            alpha = int(20 + 15 * math.sin(self.animation_time * 2 + i * 0.5))
            color = (alpha, alpha, alpha + 30, alpha)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.3))
            pygame.draw.circle(panel_surface, color, (int(x), int(y)), size)
        
        # Blit the panel surface
        self.surface.blit(panel_surface, self.control_panel_rect.topleft)
        
        # Enhanced animated border glow
        glow_intensity = max(0, min(255, int(60 + 40 * math.sin(self.animation_time * 3))))
        for i in range(3, 0, -1):
            alpha = max(0, min(255, int(glow_intensity - i * 15)))
            color = (alpha, max(0, min(255, alpha + 30)), max(0, min(255, alpha + 60)))
            glow_rect = self.control_panel_rect.inflate(i * 2, i * 2)
            pygame.draw.rect(self.surface, color, glow_rect, 2)
        
        pygame.draw.rect(self.surface, GHOST_BLUE, self.control_panel_rect, 3)
        pygame.draw.rect(self.surface, (0, 150, 255), self.control_panel_rect, 1)
        
        # Panel title with enhanced neon effect
        try:
            font = pygame.font.Font(FONT_PATH, 20)
        except:
            font = pygame.font.Font(None, 20)
        
        title_text = font.render("CONTROL PANEL", True, PAC_YELLOW)
        title_rect = title_text.get_rect(center=(self.control_panel_rect.centerx, 40))
        
        # Multiple glow layers
        glow_colors = [(80, 80, 0), (120, 120, 0), (160, 160, 0)]
        for i, glow_color in enumerate(glow_colors):
            for offset in [(i+1, i+1), (-i-1, -i-1), (i+1, -i-1), (-i-1, i+1)]:
                glow_text = font.render("CONTROL PANEL", True, glow_color)
                self.surface.blit(glow_text, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Pulsing title
        pulse_alpha = int(255 + 30 * math.sin(self.animation_time * 4))
        pulse_alpha = max(0, min(255, pulse_alpha))
        title_color = (pulse_alpha, pulse_alpha, 0)
        title_text = font.render("CONTROL PANEL", True, title_color)
        self.surface.blit(title_text, title_rect)
        
        # Draw panel sections with better spacing - reordered
        self._draw_score_section()
        self._draw_lives_section()
        self._draw_controls_section()
        self._draw_stats_section()
        self._draw_play_section()  # Play button above algorithm
        self._draw_algorithm_section()  # Algorithm at bottom
    
    def _draw_score_section(self):
        """Draw score section with enhanced design"""
        y_start = 80
        try:
            font_large = pygame.font.Font(FONT_PATH, 16)
            font_medium = pygame.font.Font(FONT_PATH, 14)
            font_small = pygame.font.Font(FONT_PATH, 12)
        except:
            font_large = pygame.font.Font(None, 16)
            font_medium = pygame.font.Font(None, 14)
            font_small = pygame.font.Font(None, 12)
        
        # Section background with enhanced glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 100)  # Taller and wider section
        
        # Enhanced glow effect
        glow_rect = section_rect.inflate(6, 6)
        pygame.draw.rect(self.surface, (80, 80, 120), glow_rect, 3)
        
        # Main background with gradient
        for i in range(section_rect.height):
            alpha = int(50 + (i / section_rect.height) * 20)
            color = (alpha, alpha, alpha + 30)
            pygame.draw.line(self.surface, color, 
                           (section_rect.x, section_rect.y + i),
                           (section_rect.right, section_rect.y + i))
        
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 3)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        # Score section
        score_text = font_large.render("SCORE", True, PAC_YELLOW)
        self.surface.blit(score_text, (self.control_panel_rect.x + 30, y_start))
        
        # Animated score value with better formatting
        score_pulse = int(255 + 40 * math.sin(self.animation_time * 4))
        score_pulse = max(0, min(255, score_pulse))
        score_color = (score_pulse, score_pulse, score_pulse)
        score_value = font_medium.render(f"{self.score:,}", True, score_color)
        self.surface.blit(score_value, (self.control_panel_rect.x + 30, y_start + 25))
        
        # Level section
        level_text = font_large.render("LEVEL", True, PAC_YELLOW)
        self.surface.blit(level_text, (self.control_panel_rect.x + 30, y_start + 55))
        
        # Animated level value (display level + 1 for user-friendly display)
        level_pulse = int(255 + 30 * math.sin(self.animation_time * 3 + 1))
        level_pulse = max(0, min(255, level_pulse))
        level_color = (level_pulse, level_pulse, level_pulse)
        display_level = self.level + 1  # Show level + 1 to user
        level_value = font_medium.render(f"{display_level}", True, level_color)
        self.surface.blit(level_value, (self.control_panel_rect.x + 30, y_start + 80))
    
    def _draw_play_section(self):
        """Draw play/pause button section"""
        y_start = 520  # Above algorithm section
        try:
            font = pygame.font.Font(FONT_PATH, 14)
        except:
            font = pygame.font.Font(None, 14)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 80)
        
        # Enhanced glow effect
        glow_rect = section_rect.inflate(6, 6)
        pygame.draw.rect(self.surface, (80, 80, 120), glow_rect, 3)
        
        # Main background with gradient
        for i in range(section_rect.height):
            alpha = int(50 + (i / section_rect.height) * 20)
            color = (alpha, alpha, alpha + 30)
            pygame.draw.line(self.surface, color, 
                           (section_rect.x, section_rect.y + i),
                           (section_rect.right, section_rect.y + i))
        
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 3)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        # Play/Pause button
        button_rect = pygame.Rect(self.control_panel_rect.x + 30, y_start + 15, 
                                 self.control_panel_rect.width - 60, 50)
        
        # Button glow effect
        button_glow = button_rect.inflate(4, 4)
        pygame.draw.rect(self.surface, (100, 100, 150), button_glow, 2)
        
        # Button background
        pygame.draw.rect(self.surface, (60, 60, 100), button_rect)
        pygame.draw.rect(self.surface, PAC_YELLOW, button_rect, 2)
        
        # Button text - show PLAY or PAUSE based on state
        button_text_str = "PAUSE" if self.is_playing else "PLAY"
        button_text = font.render(button_text_str, True, PAC_YELLOW)
        text_rect = button_text.get_rect(center=button_rect.center)
        self.surface.blit(button_text, text_rect)
        
        # Store button rect for click detection
        self.play_button_rect = button_rect
    
    def _draw_lives_section(self):
        """Draw lives section"""
        y_start = 200  # Moved down to accommodate taller score section
        try:
            font = pygame.font.Font(FONT_PATH, 14)
        except:
            font = pygame.font.Font(None, 14)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 70)  # Taller section
        
        # Glow effect
        glow_rect = section_rect.inflate(4, 4)
        pygame.draw.rect(self.surface, (60, 60, 100), glow_rect, 2)
        
        # Main background
        pygame.draw.rect(self.surface, (45, 45, 70), section_rect)
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        lives_text = font.render("LIVES", True, PAC_YELLOW)
        self.surface.blit(lives_text, (self.control_panel_rect.x + 30, y_start))
        
        # Draw life indicators with enhanced design
        for i in range(self.lives):
            x = self.control_panel_rect.x + 30 + (i * 40)  # More spacing between lives
            y = y_start + 30
            
            # Animated Pac-Man
            pac_size = int(12 + 2 * math.sin(self.animation_time * 4 + i))
            
            # Glow effect
            for j in range(3, 0, -1):
                glow_alpha = int(100 - j * 30)
                glow_color = (glow_alpha, glow_alpha, 0)
                pygame.draw.circle(self.surface, glow_color, (x, y), pac_size + j * 2, 1)
            
            # Pac-Man body
            pygame.draw.circle(self.surface, PAC_YELLOW, (x, y), pac_size)
            
            # Pac-Man mouth (animated)
            mouth_angle = math.pi * 0.2 + self.animation_time * 3 + i * 0.5
            mouth_width = math.pi * 0.8 + 0.3 * math.sin(self.animation_time * 5 + i)
            pygame.draw.arc(self.surface, (0, 0, 0), (x-pac_size, y-pac_size, pac_size*2, pac_size*2), 
                           mouth_angle, mouth_angle + mouth_width, 4)
            
            # Eye
            eye_x = x + int(3 * math.cos(mouth_angle + mouth_width/2))
            eye_y = y + int(3 * math.sin(mouth_angle + mouth_width/2))
            pygame.draw.circle(self.surface, (0, 0, 0), (eye_x, eye_y), 2)
    
    def _draw_algorithm_section(self):
        """Draw algorithm section - now at bottom"""
        y_start = 610  # Below play section
        try:
            font = pygame.font.Font(FONT_PATH, 14)
        except:
            font = pygame.font.Font(None, 14)
        
        # Section background with enhanced glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 80)  # Appropriate height
        
        # Enhanced glow effect
        glow_rect = section_rect.inflate(6, 6)
        pygame.draw.rect(self.surface, (80, 80, 120), glow_rect, 3)
        
        # Main background
        pygame.draw.rect(self.surface, (50, 50, 80), section_rect)
        pygame.draw.rect(self.surface, PAC_YELLOW, section_rect, 3)  # Yellow border for visibility
        pygame.draw.rect(self.surface, (0, 180, 255), section_rect, 1)
        
        algo_text = font.render("AI ALGORITHM", True, PAC_YELLOW)
        self.surface.blit(algo_text, (self.control_panel_rect.x + 30, y_start))
        
        # Draw the selectbox with special highlight
        if self.algorithm_selectbox:
            # Add a pulsing glow around selectbox
            glow_intensity = int(100 + 50 * math.sin(self.animation_time * 6))
            glow_rect = pygame.Rect(
                self.algorithm_selectbox.rect.x - 3,
                self.algorithm_selectbox.rect.y - 3,
                self.algorithm_selectbox.rect.width + 6,
                self.algorithm_selectbox.rect.height + 6
            )
            pygame.draw.rect(self.surface, (glow_intensity, glow_intensity, 0), glow_rect, 2)
            
            # Draw the selectbox
            self.algorithm_selectbox.draw(self.surface)
    
    def _draw_controls_section(self):
        """Draw controls section"""
        y_start = 290  # Moved back up since play is now above algorithm
        try:
            font = pygame.font.Font(FONT_PATH, 12)
        except:
            font = pygame.font.Font(None, 12)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 130)  # Taller section
        
        # Glow effect
        glow_rect = section_rect.inflate(4, 4)
        pygame.draw.rect(self.surface, (60, 60, 100), glow_rect, 2)
        
        # Main background
        pygame.draw.rect(self.surface, (45, 45, 70), section_rect)
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        controls = [
            "CONTROLS",
            "↑↓←→ - Move",
            "SPACE - Pause",
            "ESC - Menu",
            "R - Restart"
        ]
        
        for i, control in enumerate(controls):
            color = PAC_YELLOW if i == 0 else DOT_WHITE
            # Add subtle animation to control text
            if i > 0:
                alpha = int(200 + 30 * math.sin(self.animation_time * 2 + i))
                alpha = max(0, min(255, alpha))
                color = (alpha, alpha, alpha)
            text_surface = font.render(control, True, color)
            self.surface.blit(text_surface, 
                            (self.control_panel_rect.x + 30, y_start + 15 + i * 20))  # Better spacing
    
    def _draw_stats_section(self):
        """Draw additional stats section"""
        y_start = 420  # Moved down to accommodate controls section
        try:
            font = pygame.font.Font(FONT_PATH, 12)
        except:
            font = pygame.font.Font(None, 12)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 100)
        
        # Glow effect
        glow_rect = section_rect.inflate(4, 4)
        pygame.draw.rect(self.surface, (60, 60, 100), glow_rect, 2)
        
        # Main background
        pygame.draw.rect(self.surface, (45, 45, 70), section_rect)
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        # Stats title
        stats_text = font.render("STATS", True, PAC_YELLOW)
        self.surface.blit(stats_text, (self.control_panel_rect.x + 30, y_start))
        
        # Add animated elements with better effects
        for i in range(5):
            x = self.control_panel_rect.x + 30 + i * 60  # More spacing between stats
            y = y_start + 30
            alpha = int(80 + 60 * math.sin(self.animation_time * 2 + i * 0.5))
            alpha = max(0, min(255, alpha))
            size = int(2 + 3 * math.sin(self.animation_time * 3 + i))
            size = max(1, size)
            color = (alpha, alpha, min(255, alpha + 50))
            pygame.draw.circle(self.surface, color, (int(x), int(y)), size)
            
            # Add glow effect
            for j in range(2, 0, -1):
                glow_alpha = int(alpha * 0.5 - j * 20)
                glow_alpha = max(0, min(255, glow_alpha))
                glow_color = (glow_alpha, glow_alpha, min(255, glow_alpha + 30))
                pygame.draw.circle(self.surface, glow_color, (int(x), int(y)), size + j * 2, 1)
    
    def _draw_game_info(self):
        """Draw additional game information"""
        # Draw some floating elements
        for i in range(5):
            x = (self.animation_time * 20 + i * 100) % self.app.WIDTH
            y = 50 + 30 * math.sin(self.animation_time * 2 + i)
            pygame.draw.circle(self.surface, GHOST_PINK, (int(x), int(y)), 3)
    
    def get_game_area_rect(self):
        """
        Lấy rectangle của game area để render game
        Returns:
            pygame.Rect của game area
        """
        return self.game_area_rect
    
    def get_control_panel_rect(self):
        """
        Lấy rectangle của control panel
        Returns:
            pygame.Rect của control panel
        """
        return self.control_panel_rect
    
    def handle_selectbox_event(self, event):
        """
        Xử lý sự kiện selectbox và trả về nếu algorithm thay đổi
        Args:
            event: Pygame event
        Returns:
            True nếu algorithm thay đổi, False nếu không
        """
        if self.algorithm_selectbox:
            # Xử lý mouse hover cho selectbox
            if event.type == pygame.MOUSEMOTION:
                if hasattr(self.algorithm_selectbox, 'rect') and self.algorithm_selectbox.rect.collidepoint(event.pos):
                    if not getattr(self, '_selectbox_hovered', False):
                        self.app.sound_system.play_sound('button_hover')
                        self._selectbox_hovered = True
                else:
                    self._selectbox_hovered = False
            
            if self.algorithm_selectbox.handle_event(event):
                # Kiểm tra xem selection có thay đổi không
                new_algorithm = self.algorithm_selectbox.get_selected_value()
                if new_algorithm and new_algorithm != self.algorithm:
                    self.algorithm = new_algorithm
                    return True
        return False
    
    def handle_play_button_click(self, event):
        """
        Xử lý sự kiện click play button
        Args:
            event: Pygame event
        Returns:
            True nếu play state thay đổi, False nếu không
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            if hasattr(self, 'play_button_rect') and self.play_button_rect.collidepoint(event.pos):
                # Phát âm thanh khi click play/pause
                self.app.sound_system.play_sound('button_click')
                self.is_playing = not self.is_playing
                return True  # Báo hiệu play state đã thay đổi
        elif event.type == pygame.MOUSEMOTION:
            # Xử lý mouse hover cho play button
            if hasattr(self, 'play_button_rect') and self.play_button_rect.collidepoint(event.pos):
                if not getattr(self, '_play_button_hovered', False):
                    self.app.sound_system.play_sound('button_hover')
                    self._play_button_hovered = True
            else:
                self._play_button_hovered = False
        return False
    
    def update(self):
        """
        Cập nhật animation của layout
        - Tăng animation_time mỗi frame
        """
        self.animation_time += 0.02
