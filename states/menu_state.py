# =============================================================================
# MENU_STATE.PY - STATE MENU CHÍNH CỦA GAME PAC-MAN
# =============================================================================
# File này chứa MenuState - màn hình menu chính của game
# Quản lý navigation giữa các màn hình khác nhau và cài đặt

import sys
import math
import pygame
from pathlib import Path

from statemachine import State
from ui.button import PacManButton
from ui.neontext import NeonText
from ui.constants import *

class MenuState(State):
    HOME = 'home'           # Màn hình chính
    GAME_MODES = 'game_modes'  # Màn hình chế độ chơi
    SCORES = 'scores'       # Màn hình điểm cao
    STATES = 'states'       # Màn hình thông tin states

    def __init__(self, app, machine):
        super().__init__(app, machine)
        self.scene = MenuState.HOME  
        self.animation_time = 0  # Thời gian animation
        self.current_button_index = 0  

        self._load_background()
        self._init_ui_components()
        
        self._last_button_index = -1
        self._last_hovered_button = -1

    def _load_background(self):
        IMG_PATH = Path("assets/images/pm.jpg")
        if not IMG_PATH.exists():
            raise FileNotFoundError(f"Background image not found at {IMG_PATH}")
        
        bg = pygame.image.load(str(IMG_PATH)).convert()
        self.background = pygame.transform.scale(bg, (self.app.WIDTH, self.app.HEIGHT))

    def _init_ui_components(self):
        """
        Khởi tạo tất cả UI components cho các scene
        - Tạo dictionary chứa components cho từng scene
        - Lưu reference đến algorithm button để update
        """
        center_x = self.app.WIDTH // 2
        center_y = self.app.HEIGHT // 2
        self.UIComponents = {
            MenuState.HOME: self._create_home_components(center_x, center_y),
            MenuState.GAME_MODES: self._create_game_modes_components(center_x, center_y),
            MenuState.SCORES: self._create_scores_components(center_x, center_y),
            MenuState.STATES: self._create_states_components(center_x, center_y)
        }
        
    def _create_home_components(self, center_x, center_y):
        """
        Tạo UI components cho màn hình chính (HOME)
        - Title và subtitle với hiệu ứng neon
        - Các button chính với spacing đẹp
        - Sử dụng emoji và màu sắc Pac-Man theme
        """
        button_spacing = 80 
        start_y = center_y - 100  
        return [
            NeonText(self.app, "PAC-MAN", PAC_YELLOW, center_x, center_y - 220, 80, 
                     glow=True, rainbow=True, outline=True),
            NeonText(self.app, "ARCADE ADVENTURE", GHOST_PINK, center_x, center_y - 160, 22, 
                     glow=True, outline=True),
            PacManButton(self.app, pos=(center_x, start_y), text="🎮 GAME MODES", 
                         onclick=[self.show_game_modes], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing), text="📊 HIGH SCORES", 
                         onclick=[self.show_scores]),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 2), text="ℹ️ STATES", 
                         onclick=[self.show_states]),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 3), text="X EXIT", 
                         onclick=[self.quit]),
        ]

    def _create_game_modes_components(self, center_x, center_y):
        button_spacing = 80
        start_y = center_y - 80
        return [
            NeonText(self.app, "GAME MODES", PAC_YELLOW, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            PacManButton(self.app, pos=(center_x, start_y), text="🤖 AI MODE", 
                         onclick=[self.start_ai_game], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing), text="👤 PLAYER MODE", 
                         onclick=[self.start_player_game], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 2), text="⚔️ COMPARISON", 
                         onclick=[self.start_comparison_game], primary=True),
            PacManButton(self.app, pos=(center_x, center_y + 180), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_scores_components(self, center_x, center_y):
        return [
            NeonText(self.app, "HIGH SCORES", GHOST_ORANGE, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            NeonText(self.app, "1. AI Master - 9999", DOT_WHITE, center_x, center_y - 80, 20, outline=True),
            NeonText(self.app, "2. Player Pro - 8500", DOT_WHITE, center_x, center_y - 50, 20, outline=True),
            NeonText(self.app, "3. Ghost Hunter - 7200", DOT_WHITE, center_x, center_y - 20, 20, outline=True),
            NeonText(self.app, "4. Dot Collector - 6800", DOT_WHITE, center_x, center_y + 10, 20, outline=True),
            NeonText(self.app, "5. Pac Champion - 5500", DOT_WHITE, center_x, center_y + 40, 20, outline=True),
            
            PacManButton(self.app, pos=(center_x, center_y + 140), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_states_components(self, center_x, center_y):
        return [
            NeonText(self.app, "GAME STATES", GHOST_BLUE, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            
            NeonText(self.app, "Current State: Menu", DOT_WHITE, center_x, center_y - 80, 18, outline=True),
            NeonText(self.app, "Available States:", DOT_WHITE, center_x, center_y - 50, 16, outline=True),
            NeonText(self.app, "• Menu State", GHOST_PINK, center_x, center_y - 20, 14, outline=True),
            NeonText(self.app, "• Game State", GHOST_PINK, center_x, center_y + 5, 14, outline=True),
            NeonText(self.app, "• Pause State", GHOST_PINK, center_x, center_y + 30, 14, outline=True),
            NeonText(self.app, "• Game Over State", GHOST_PINK, center_x, center_y + 55, 14, outline=True),
            NeonText(self.app, "• Statistics State", GHOST_PINK, center_x, center_y + 80, 14, outline=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 140), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def start_ai_game(self):
        self.app.sound_system.play_sound('button_click')
        self.app.sound_system.play_music('background_music')
        
        from states.game_state import GameState
        game_state = GameState(self.app, self.machine)
        game_state.game.set_ai_mode(True)
        self.replace_state(game_state)

    def start_player_game(self):
        self.app.sound_system.play_sound('button_click')
        self.app.sound_system.play_music('background_music')
        
        from states.game_state import GameState
        game_state = GameState(self.app, self.machine)
        game_state.game.set_ai_mode(False)
        game_state.game.set_ghost_mode(True)
        self.replace_state(game_state)

    def start_comparison_game(self):
        self.app.sound_system.play_sound('button_click')
        self.app.sound_system.play_music('background_music')
        
        from states.comparison_state import ComparisonState
        comparison_state = ComparisonState(self.app, self.machine)
        self.replace_state(comparison_state)

    def show_game_modes(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.GAME_MODES
        self.current_button_index = 0
        self._last_button_index = -1 
        self._update_scene_focus()

    def show_scores(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.SCORES
        self.current_button_index = 0
        self._last_button_index = -1 
        self._update_scene_focus()

    def show_states(self):
        self.app.sound_system.play_sound('button_click')
        # Chuyển sang StatsState thay vì hiển thị trong menu
        from states.stats_state import StatsState
        stats_state = StatsState(self.app, self.machine, self.app.current_game)
        self.replace_state(stats_state)
    
    def back_to_home(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.HOME
        self.current_button_index = 0
        self._last_button_index = -1
        self._update_scene_focus()
    
    def _update_scene_focus(self):
        buttons = [comp for comp in self.UIComponents[self.scene] if isinstance(comp, PacManButton)]
        self._update_button_focus(buttons)

    def draw(self, _screen=None):
        screen = self.app.screen
        
        screen.fill((0, 0, 0))
        
        if hasattr(self, 'background') and self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((20, 20, 40))
        
        self.animation_time += 0.02
        self._draw_pac_dots(screen)
        
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, 'render'):
                comp.render()  
        
        # Vẽ banner sinh viên
        self._draw_student_banner(screen)
        
    def _draw_student_banner(self, screen):
        """Vẽ banner thông tin sinh viên ở góc trái màn hình"""
        # Font cho banner - sử dụng Times New Roman hoặc font hệ thống
        try:
            font = pygame.font.SysFont("Times New Roman", 18, bold=True)
        except:
            try:
                font = pygame.font.SysFont("Arial", 18, bold=True)
            except:
                try:
                    font = pygame.font.SysFont("Calibri", 18, bold=True)
                except:
                    try:
                        font = pygame.font.SysFont("Tahoma", 18, bold=True)
                    except:
                        # Fallback cuối cùng - font mặc định với kích thước lớn
                        font = pygame.font.Font(None, 20)
        
        # Màu sắc - tất cả màu trắng
        name_color = (255, 255, 255)    # Trắng
        mssv_color = (255, 255, 255)    # Trắng
        border_color = (150, 150, 150)  # Xám sáng hơn
        
        # Vị trí góc trái
        start_x = 10
        start_y = 10
        
        # Thông tin sinh viên
        student1_name = "Nguyễn Vũ Bảo"
        student1_mssv = "MSSV: 23110079"
        student2_name = "Trần Hoàng Phúc Quân"
        student2_mssv = "MSSV: 23110146"
        
        # Vẽ background cho banner
        banner_rect = pygame.Rect(start_x - 5, start_y - 5, 250, 95)
        pygame.draw.rect(screen, (0, 0, 0, 180), banner_rect)  # Nền đen trong suốt
        pygame.draw.rect(screen, border_color, banner_rect, 2)  # Viền
        
        # Vẽ text
        texts = [
            (student1_name, name_color, start_x, start_y),
            (student1_mssv, mssv_color, start_x, start_y + 20),
            (student2_name, name_color, start_x, start_y + 50),
            (student2_mssv, mssv_color, start_x, start_y + 70)
        ]
        
        for text, color, x, y in texts:
            text_surface = font.render(text, True, color)
            screen.blit(text_surface, (x, y))
        
    def _draw_pac_dots(self, screen):
        dot_colors = [DOT_WHITE, PAC_YELLOW, GHOST_PINK, GHOST_RED]
        
        for i in range(15):
            x = (self.animation_time * 50 + i * 200) % (self.app.WIDTH + 100) - 50
            y = 150 + (i * 67) % 400 + 10 * math.sin(self.animation_time * 3 + i * 0.8)
            
            base_size = 4 if i % 4 == 0 else 3
            size = base_size + int(1 * math.sin(self.animation_time * 4 + i))
            color = dot_colors[i % len(dot_colors)]
            
            if 0 <= x <= self.app.WIDTH and 0 <= y <= self.app.HEIGHT:
                glow_surf = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, 80), (size*2, size*2), size*2)
                screen.blit(glow_surf, (int(x-size*2), int(y-size*2)))
                
                pygame.draw.circle(screen, color, (int(x), int(y)), size)

    def logic(self):
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, 'update'):
                comp.update()
        
    def handle_events(self, event):        
        if event.type == pygame.KEYDOWN:
            self._handle_keyboard_navigation(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for comp in self.UIComponents[self.scene]:
                if hasattr(comp, "handle_event"):
                    comp.handle_event(event)
        elif event.type == pygame.MOUSEMOTION:
            # Xử lý mouse hover để phát âm thanh
            self._handle_mouse_hover(event)
        
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, "handle_event"):
                comp.handle_event(event)
    
    def _handle_mouse_hover(self, event):
        """Xử lý mouse hover để phát âm thanh"""
        buttons = [comp for comp in self.UIComponents[self.scene] if isinstance(comp, PacManButton)]
        mouse_pos = event.pos
        
        # Tìm button đang được hover
        hovered_button_index = -1
        for i, button in enumerate(buttons):
            if hasattr(button, 'rect') and button.rect.collidepoint(mouse_pos):
                hovered_button_index = i
                break
        
        # Phát âm thanh hover nếu button thay đổi
        if hovered_button_index != -1 and hovered_button_index != getattr(self, '_last_hovered_button', -1):
            self.app.sound_system.play_sound('button_hover')
            self._last_hovered_button = hovered_button_index
        elif hovered_button_index == -1:
            self._last_hovered_button = -1
    
    def _handle_keyboard_navigation(self, event):
        buttons = [comp for comp in self.UIComponents[self.scene] if isinstance(comp, PacManButton)]        
        if event.key == pygame.K_TAB:
            self.current_button_index = (self.current_button_index + 1) % len(buttons)
            self._update_button_focus(buttons)
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            if event.key == pygame.K_UP:
                self.current_button_index = (self.current_button_index - 1) % len(buttons)
            else:
                self.current_button_index = (self.current_button_index + 1) % len(buttons)
            self._update_button_focus(buttons)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if buttons:
                buttons[self.current_button_index]._trigger_click()
        elif event.key == pygame.K_ESCAPE:
            if self.scene == MenuState.HOME:
                self.quit()
            else:
                self.back_to_home()
    
    def _update_button_focus(self, buttons):
        old_index = getattr(self, '_last_button_index', -1)
        for i, button in enumerate(buttons):
            button.set_focus(False) 
        buttons[self.current_button_index].set_focus(True)
        
        # Phát âm thanh hover nếu button thay đổi
        if old_index != self.current_button_index and old_index != -1:
            self.app.sound_system.play_sound('button_hover')
        
        self._last_button_index = self.current_button_index
            
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
    
    def on_settings_changed(self, settings):
        """
        Được gọi khi settings thay đổi
        """
        if hasattr(self.app, 'sfx_volume'):
            self.app.sfx_volume = settings.get('sfx_volume', 0.8)
        
        if 'music_volume' in settings:
            pygame.mixer.music.set_volume(settings['music_volume'])
        
    @classmethod
    def quit(cls):
        pygame.quit()
        sys.exit(0)
