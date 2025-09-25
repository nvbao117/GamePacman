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
# from ui.advanced_settings import AdvancedSettingsModal  # Removed - not needed
from ui.constants import *

class MenuState(State):
    """
    MenuState - State menu chính của game Pac-Man
    - Quản lý navigation giữa các scene khác nhau
    - Có animation và hiệu ứng visual đẹp mắt
    - Hỗ trợ keyboard navigation
    """
    # Các scene constants
    HOME = 'home'           # Màn hình chính
    OPTIONS = 'option'      # Màn hình cài đặt
    GAME_MODES = 'game_modes'  # Màn hình chế độ chơi
    SCORES = 'scores'       # Màn hình điểm cao
    STATES = 'states'       # Màn hình thông tin states

    def __init__(self, app, machine):
        """
        Khởi tạo MenuState
        Args:
            app: Tham chiếu đến App chính
            machine: StateMachine quản lý states
        """
        super().__init__(app, machine)
        self.scene = MenuState.HOME  # Scene hiện tại
        self.animation_time = 0  # Thời gian animation
        self.selected_algorithm = 'BFS'  # Thuật toán AI được chọn
        self._algorithms = ['BFS', 'DFS', 'IDS', 'UCS']  # Danh sách thuật toán
        self.current_button_index = 0  # Index button hiện tại (cho keyboard nav)

        # Khởi tạo background và UI components
        self._load_background()
        self._init_ui_components()
        
        # Khởi tạo biến để theo dõi button focus
        self._last_button_index = -1
        self._last_hovered_button = -1
        
        # Advanced Settings removed - use enhanced basic settings instead

    def _load_background(self):
        """
        Load background image cho menu
        - Load hình ảnh từ assets/images/pm.jpg
        - Scale để fit với kích thước màn hình
        - Throw error nếu không tìm thấy file
        """
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
        
        # Tạo dictionary chứa UI components cho từng scene
        self.UIComponents = {
            MenuState.HOME: self._create_home_components(center_x, center_y),
            MenuState.OPTIONS: self._create_options_components(center_x, center_y),
            MenuState.GAME_MODES: self._create_game_modes_components(center_x, center_y),
            MenuState.SCORES: self._create_scores_components(center_x, center_y),
            MenuState.STATES: self._create_states_components(center_x, center_y)
        }
        
        # Lưu reference đến algorithm button để update text
        self.algo_button = self.UIComponents[MenuState.OPTIONS][2]

    def _create_home_components(self, center_x, center_y):
        """
        Tạo UI components cho màn hình chính (HOME)
        - Title và subtitle với hiệu ứng neon
        - Các button chính với spacing đẹp
        - Sử dụng emoji và màu sắc Pac-Man theme
        
        Args:
            center_x, center_y: Tọa độ trung tâm màn hình
        Returns:
            List các UI components cho HOME scene
        """
        # Spacing và alignment tốt hơn cho buttons
        button_spacing = 80  # Khoảng cách giữa các buttons
        start_y = center_y - 100  # Vị trí bắt đầu cho button đầu tiên
        
        return [
            # Title chính với hiệu ứng neon và rainbow
            NeonText(self.app, "PAC-MAN", PAC_YELLOW, center_x, center_y - 220, 80, 
                     glow=True, rainbow=True, outline=True),
            # Subtitle
            NeonText(self.app, "ARCADE ADVENTURE", GHOST_PINK, center_x, center_y - 160, 22, 
                     glow=True, outline=True),
            
            # Main menu buttons với spacing tốt hơn
            PacManButton(self.app, pos=(center_x, start_y), text="🎮 GAME MODES", 
                         onclick=[self.show_game_modes], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing), text="📊 HIGH SCORES", 
                         onclick=[self.show_scores]),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 2), text="🔧 SETTINGS", 
                         onclick=[self.show_settings]),
            # Advanced Settings button removed - enhanced basic settings instead
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 3), text="ℹ️ STATES", 
                         onclick=[self.show_states]),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 4), text="X EXIT", 
                         onclick=[self.quit]),
        ]

    def _create_options_components(self, center_x, center_y):
        return [
            NeonText(self.app, "SETTINGS", GHOST_PINK, center_x, center_y - 120, 60, 
                     glow=True, outline=True),
            NeonText(self.app, "Choose AI Algorithm:", DOT_WHITE, center_x, center_y - 60, 18, outline=True),
            
            # Algorithm selection button
            PacManButton(self.app, pos=(center_x, center_y - 10), text=f"AI: {self.selected_algorithm}", 
                         onclick=[self.cycle_algorithm], primary=True),
                       
            # Algorithm description
            NeonText(self.app, lambda: self.get_algo_description(), (255, 255, 255), 
                     center_x, center_y + 40, 14, outline=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 120), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_game_modes_components(self, center_x, center_y):
        button_spacing = 80
        start_y = center_y - 80
        
        return [
            NeonText(self.app, "GAME MODES", PAC_YELLOW, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            
            # Game mode buttons with better spacing
            PacManButton(self.app, pos=(center_x, start_y), text="🤖 AI MODE", 
                         onclick=[self.start_ai_game], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing), text="👤 PLAYER MODE", 
                         onclick=[self.start_player_game], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 2), text="⚔️ COMPARISON", 
                         onclick=[self.start_comparison_game], primary=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 180), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_scores_components(self, center_x, center_y):
        return [
            NeonText(self.app, "HIGH SCORES", GHOST_ORANGE, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            
            # Placeholder scores with better spacing
            NeonText(self.app, "1. AI Master - 9999", DOT_WHITE, center_x, center_y - 80, 20, outline=True),
            NeonText(self.app, "2. Player Pro - 8500", DOT_WHITE, center_x, center_y - 50, 20, outline=True),
            NeonText(self.app, "3. Ghost Hunter - 7200", DOT_WHITE, center_x, center_y - 20, 20, outline=True),
            NeonText(self.app, "4. Dot Collector - 6800", DOT_WHITE, center_x, center_y + 10, 20, outline=True),
            NeonText(self.app, "5. Pac Champion - 5500", DOT_WHITE, center_x, center_y + 40, 20, outline=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 140), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_states_components(self, center_x, center_y):
        return [
            NeonText(self.app, "GAME STATES", GHOST_BLUE, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            
            # State information with better spacing
            NeonText(self.app, "Current State: Menu", DOT_WHITE, center_x, center_y - 80, 18, outline=True),
            NeonText(self.app, "Available States:", DOT_WHITE, center_x, center_y - 50, 16, outline=True),
            NeonText(self.app, "• Menu State", GHOST_PINK, center_x, center_y - 20, 14, outline=True),
            NeonText(self.app, "• Game State", GHOST_PINK, center_x, center_y + 5, 14, outline=True),
            NeonText(self.app, "• Pause State", GHOST_PINK, center_x, center_y + 30, 14, outline=True),
            NeonText(self.app, "• Game Over State", GHOST_PINK, center_x, center_y + 55, 14, outline=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 140), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def get_algo_description(self):
        """
        Lấy mô tả của thuật toán AI hiện tại
        Returns:
            String mô tả thuật toán
        """
        descriptions = {
            'BFS': "● Breadth-First: Explores level by level ●",
            'DFS': "● Depth-First: Goes deep first ●", 
            'IDS': "● Iterative Deepening: Best of both worlds ●",
            'UCS': "● Uniform Cost: Finds optimal path ●"
        }
        return descriptions.get(self.selected_algorithm, "")

    def start_game(self):
        """
        Bắt đầu game với thuật toán đã chọn
        """
        print(f"Starting game with algorithm: {self.selected_algorithm}")
        # TODO: Implement game start logic

    def start_ai_game(self):
        """
        Bắt đầu game AI mode
        """
        print(f"Starting AI game with algorithm: {self.selected_algorithm}")
        # Phát âm thanh bắt đầu game
        self.app.sound_system.play_sound('button_click')
        # Bắt đầu nhạc nền
        self.app.sound_system.play_music('background_music')
        
        from states.game_state import GameState
        game_state = GameState(self.app, self.machine, self.selected_algorithm)
        self.replace_state(game_state)

    def start_player_game(self):
        """
        Bắt đầu game player mode (không AI)
        """
        print("Starting player game")
        # Phát âm thanh bắt đầu game
        self.app.sound_system.play_sound('button_click')
        # Bắt đầu nhạc nền
        self.app.sound_system.play_music('background_music')
        
        from states.game_state import GameState
        game_state = GameState(self.app, self.machine, "MANUAL")
        self.replace_state(game_state)

    def start_comparison_game(self):
        """
        Bắt đầu game comparison mode
        """
        print("Starting comparison game")
        from states.comparison_state import ComparisonState
        comparison_state = ComparisonState(self.app, self.machine)
        self.replace_state(comparison_state)

    def cycle_algorithm(self):
        """
        Chuyển đổi thuật toán AI
        - Cycle qua danh sách algorithms
        - Cập nhật text của algorithm button
        """
        self.app.sound_system.play_sound('button_click')
        idx = self._algorithms.index(self.selected_algorithm)
        self.selected_algorithm = self._algorithms[(idx + 1) % len(self._algorithms)]
        
        if self.algo_button is not None:
            self.algo_button.text = f"AI: {self.selected_algorithm}"

    def show_game_modes(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.GAME_MODES
        self.current_button_index = 0
        self._last_button_index = -1  # Reset để không phát hover sound
        self._update_scene_focus()

    def show_scores(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.SCORES
        self.current_button_index = 0
        self._last_button_index = -1  # Reset để không phát hover sound
        self._update_scene_focus()

    def show_states(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.STATES
        self.current_button_index = 0
        self._last_button_index = -1  # Reset để không phát hover sound
        self._update_scene_focus()

    def show_options(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.OPTIONS
        self.current_button_index = 0
        self._last_button_index = -1  # Reset để không phát hover sound
        self._update_scene_focus()
    
    def show_settings(self):
        """Hiển thị setting modal"""
        self.app.sound_system.play_sound('button_click')
        self.app.setting_modal.show()
    
    # Advanced settings method removed - not needed anymore

    def back_to_home(self):
        self.app.sound_system.play_sound('button_click')
        self.scene = MenuState.HOME
        self.current_button_index = 0
        self._last_button_index = -1  # Reset để không phát hover sound
        self._update_scene_focus()
    
    def _update_scene_focus(self):
        buttons = [comp for comp in self.UIComponents[self.scene] if isinstance(comp, PacManButton)]
        self._update_button_focus(buttons)

    def draw(self, _screen=None):
        """Vẽ menu lên app.screen (bỏ qua screen truyền vào để thống nhất)"""
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
                comp.render()   # các component tự vẽ vào app.screen
        
        # Advanced settings removed - only basic settings modal

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
        
        # Advanced settings removed - only basic settings

    def handle_events(self, event):
        # Advanced settings removed - only basic settings now
        
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
        # Lưu index cũ để phát hiện thay đổi
        old_index = getattr(self, '_last_button_index', -1)
        
        for i, button in enumerate(buttons):
            button.set_focus(False)  # Xóa tiêu điểm của tất cả nút
        buttons[self.current_button_index].set_focus(True)
        
        # Phát âm thanh hover nếu button thay đổi
        if old_index != self.current_button_index and old_index != -1:
            self.app.sound_system.play_sound('button_hover')
        
        # Lưu index hiện tại
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
        # Cập nhật volume cho menu state nếu cần
        if hasattr(self.app, 'sfx_volume'):
            self.app.sfx_volume = settings.get('sfx_volume', 0.8)
        
        # Cập nhật music volume nếu có
        if 'music_volume' in settings:
            pygame.mixer.music.set_volume(settings['music_volume'])
        
        print("Menu state: Settings updated")
    
    @classmethod
    def quit(cls):
        pygame.quit()
        sys.exit(0)
