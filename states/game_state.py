# =============================================================================
# GAME_STATE.PY - STATE CHÍNH CỦA GAME PAC-MAN
# =============================================================================
import pygame
from pathlib import Path

from statemachine import State
from ui.constants import *
from states.gamelayout import GameLayout
from engine.game import Game
from states.menu_state import MenuState

class GameState(State):
    HOME = 'home'
    OPTIONS = 'option'

    def __init__(self, app, machine, algorithm="BFS"):
        super().__init__(app, machine)  
        self.algorithm = algorithm  
        self.is_pause = True  
        self.game_running = True  
        
        self.layout = GameLayout(app)
        self.game = Game(algorithm)  
        
        # Khởi tạo game nếu có method initialize_game
        if hasattr(self.game, 'initialize_game'):
            self.game.initialize_game()
        
        self.score = getattr(self.game, 'score', 0)  
        self.lives = getattr(self.game, 'lives', 5)  # Số mạng (bắt đầu với 5)
        self.level = getattr(self.game, 'level', 0)  # Level hiện tại (bắt đầu với 0)

        self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
        
        self.game.set_ai_mode(True)  # Bắt đầu với AI mode
        
        # Load few pellets mode configuration
        if hasattr(app, 'config'):
            few_pellets_mode = app.config.get('few_pellets_mode', False)
            few_pellets_count = app.config.get('few_pellets_count', 20)
            self.game.set_few_pellets_mode(few_pellets_mode, few_pellets_count)
            
            # Load heuristic configuration
            self.game.load_heuristic_from_config(app.config)
            # Sync với layout
            heuristic_setting = app.config.get('algorithm_heuristic', app.config.get('bfs_heuristic', 'NONE'))
            if hasattr(self.layout, 'heuristic_options'):
                if heuristic_setting in self.layout.heuristic_options:
                    self.layout.current_heuristic = self.layout.heuristic_options.index(heuristic_setting)
        
    def _render_scaled_game(self, game_surface, game_rect):
        """
        Render game content với scaling phù hợp để giữ tỷ lệ khung hình
        - Tính toán scale factor để fit vào game area
        - Giữ nguyên aspect ratio của game gốc
        - Render game lên surface tạm rồi scale xuống
        """
        # Lấy kích thước game gốc từ constants
        from constants import SCREENSIZE
        original_width, original_height = SCREENSIZE
        
        # Tính toán scale factors để giữ aspect ratio
        scale_x = game_rect.width / original_width
        scale_y = game_rect.height / original_height
        
        # Sử dụng scale nhỏ hơn để giữ aspect ratio và fit đúng
        scale = min(scale_x, scale_y)
        
        # Tính toán kích thước sau khi scale
        scaled_width = int(original_width * scale)
        scaled_height = int(original_height * scale)
        
        # Tạo surface tạm để render game ở kích thước gốc
        temp_surface = pygame.Surface((original_width, original_height))
        
        # Vẽ background rất nhẹ
        for y in range(original_height):
            intensity = int(2 + (y / original_height) * 3)  # Rất nhẹ
            color = (intensity, intensity + 2, intensity + 8)
            pygame.draw.line(temp_surface, color, (0, y), (original_width, y))
        
        # Render game lên surface tạm ở kích thước gốc
        self.game.render(temp_surface)
        
        # Scale surface tạm để fit vào game area với smooth scaling
        scaled_surface = pygame.transform.smoothscale(temp_surface, (scaled_width, scaled_height))
        
        # Căn giữa game đã scale trong game area
        x_offset = (game_rect.width - scaled_width) // 2
        y_offset = (game_rect.height - scaled_height) // 2
        
        game_surface.fill((0, 0, 0, 0))
        
        game_surface.blit(scaled_surface, (x_offset, y_offset))
        
    def draw(self, _screen=None):
        """
        Vẽ GameState lên màn hình
        - Render UI layout trước
        - Render game với scaling phù hợp
        - Không sử dụng _screen parameter để thống nhất
        """
        # Render UI layout (control panel, buttons, v.v.)
        self.layout.render()
        
        # Render game lên subsurface của khu vực game
        game_rect = self.layout.get_game_area_rect()
        game_surface = self.layout.surface.subsurface(game_rect)
        
        # Scale game content để fit vào game area đúng cách
        self._render_scaled_game(game_surface, game_rect)
        
    def logic(self):
        """
        Cập nhật logic của GameState mỗi frame
        - Cập nhật layout animations
        - Đồng bộ trạng thái play/pause
        - Cập nhật game engine nếu không pause
        - Kiểm tra game over
        - Xử lý âm thanh
        """
        # Luôn cập nhật layout animations
        self.layout.update()
        
        # Cập nhật AI Mode Selector
        if hasattr(self.layout, 'ai_mode_selector') and self.layout.ai_mode_selector:
            self.layout.ai_mode_selector.update(0.016)  
        
        # Đồng bộ trạng thái play giữa layout và game state
        self.layout.is_playing = not self.is_pause
        
        if not self.is_pause and self.game_running:
            # Lưu score cũ để phát hiện thay đổi
            old_score = self.score
            
            # Cập nhật game engine nếu có
            if hasattr(self.game, 'update'):
                self.game.update()
            
            # Cập nhật giá trị game từ game engine thực tế
            self.score = getattr(self.game, 'score', self.score)
            self.lives = getattr(self.game, 'lives', self.lives)
            self.level = getattr(self.game, 'level', self.level)
            
            # Phát âm thanh khi score thay đổi (ăn pellet)
            if self.score > old_score:
                score_diff = self.score - old_score
                if score_diff == 10:  # Ăn pellet thường
                    self.app.sound_system.play_sound('pellet')
                elif score_diff == 50:  # Ăn power pellet
                    self.app.sound_system.play_sound('power_pellet')
                elif score_diff >= 100:  # Ăn fruit
                    self.app.sound_system.play_sound('fruit')
            
            # Kiểm tra game over hoặc level complete
            if hasattr(self.game, 'game_over') and self.game.game_over:
                self.app.sound_system.play_sound('game_over')
                self.app.sound_system.stop_music()
            elif hasattr(self.game, 'level_complete') and self.game.level_complete:
                self.app.sound_system.play_sound('level_complete')
            
            # Cập nhật layout với giá trị game hiện tại
            game_time = getattr(self.game, 'get_formatted_time', lambda: "00:00")()
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm, self.layout.ghost_mode, game_time, self.game)
            
            # Cập nhật step info liên tục
            if hasattr(self.game, 'get_step_info'):
                self.layout.step_info = self.game.get_step_info()
        else:
            game_time = getattr(self.game, 'get_formatted_time', lambda: "00:00")()
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm, self.layout.ghost_mode, game_time, self.game)
            
            # Cập nhật step info ngay cả khi pause
            if hasattr(self.game, 'get_step_info'):
                self.layout.step_info = self.game.get_step_info()

        if self.lives <= 0:
            self.game_over()
    
    def handle_events(self, event):
        """
        Xử lý sự kiện input cho GameState
        - Xử lý click play/pause button
        - Xử lý thay đổi algorithm
        - Xử lý keyboard shortcuts
        - Chuyển tiếp events cho game engine
        """
        # Xử lý click play button trước
        if self.layout.handle_play_button_click(event):
            # Trạng thái play đã thay đổi, cập nhật game pause state
            self.is_pause = not self.layout.is_playing
            if hasattr(self.game, 'pause'):
                if self.layout.is_playing:
                    self.game.pause.setPause(pauseTime=0)  
                else:
                    self.game.pause.setPause(playerPaused=True)  
        
        # Xử lý sự kiện selectbox (thay đổi algorithm, ghost mode, AI mode và few pellets)
        algorithm_changed, ghost_mode_changed, ai_mode_changed, few_pellets_changed, heuristic_changed = self.layout.handle_selectbox_event(event)
        
        if algorithm_changed:
            # Phát âm thanh khi thay đổi algorithm
            self.app.sound_system.play_sound('button_click')
            # Algorithm đã thay đổi, cập nhật game
            self.algorithm = self.layout.algorithm
            # Chỉ thay đổi algorithm, không tạo game mới
            self.game.set_algorithm(self.algorithm)
        
        if ghost_mode_changed:
            self.app.sound_system.play_sound('button_click')
            self.game.set_ghost_mode(self.layout.ghost_mode)
        
        if ai_mode_changed:
            # Phát âm thanh khi thay đổi AI mode
            self.app.sound_system.play_sound('button_click')
            # AI mode đã thay đổi, cập nhật Pacman
            new_ai_mode = self.layout.ai_mode_selector.get_current_mode()
            self._apply_ai_mode_change(new_ai_mode)
        
        if few_pellets_changed:
            # Phát âm thanh khi thay đổi few pellets mode
            self.app.sound_system.play_sound('button_click')
            # Few pellets mode đã thay đổi, cập nhật game
            self.game.set_few_pellets_mode(
                self.layout.few_pellets_mode, 
                self.layout.few_pellets_count
            )
            # Restart game để áp dụng thay đổi pellets
            self.restart_game()
        
        if heuristic_changed:
            # Phát âm thanh khi thay đổi heuristic
            self.app.sound_system.play_sound('button_click')
            # Heuristic đã thay đổi, cập nhật game
            new_heuristic = self.layout.heuristic_options[self.layout.current_heuristic]
            self._apply_heuristic_change(new_heuristic)
        
        # Cập nhật thông tin lên layout (bao gồm step info)
        if algorithm_changed or ghost_mode_changed or ai_mode_changed or few_pellets_changed or heuristic_changed:
            game_time = getattr(self.game, 'get_formatted_time', lambda: "00:00")()
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm, self.layout.ghost_mode, game_time, self.game)
        else:
            # Cập nhật step info liên tục
            if hasattr(self.game, 'get_step_info'):
                self.layout.step_info = self.game.get_step_info()
        
        # Chuyển tiếp events cho game engine
        if hasattr(self.game, 'handle_event'):
            self.game.handle_event(event)
        
        # Xử lý keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.start_game()  # Bắt đầu game với SPACE
            elif event.key == pygame.K_ESCAPE:
                self.return_to_menu()  # Quay lại menu với ESC
            elif event.key == pygame.K_r:
                self.restart_game()  # Restart với R
            elif event.key == pygame.K_m:
                # Chỉ cho phép toggle mode khi ở AI mode
                if hasattr(self.game, 'ai_mode') and self.game.ai_mode:
                    self.toggle_ai_mode()  # Toggle AI/Player mode với M
            # Analytics keys removed
    
    def _apply_ai_mode_change(self, new_ai_mode):
        """
        Áp dụng thay đổi AI mode cho Pacman
        """
        if not hasattr(self.game, 'pacman') or not self.game.pacman:
            return
        
        pacman = self.game.pacman
        
        if new_ai_mode == "TRADITIONAL":
            if hasattr(pacman, 'disable_hybrid_ai'):
                pacman.disable_hybrid_ai()
            
        elif new_ai_mode == "HYBRID":
            # Bật Hybrid AI (mặc định)
            if hasattr(pacman, 'enable_hybrid_ai'):
                pacman.enable_hybrid_ai()
            
        elif new_ai_mode == "ONLINE":
            # Chỉ sử dụng online decision-making
            if hasattr(pacman, 'hybrid_ai'):
                pacman.hybrid_ai.current_mode = "ONLINE"
            
        elif new_ai_mode == "OFFLINE":
            # Chỉ sử dụng offline planning
            if hasattr(pacman, 'hybrid_ai'):
                pacman.hybrid_ai.current_mode = "OFFLINE"
    
    def toggle_pause(self):
        """
        Chuyển đổi trạng thái pause
        - Toggle giữa pause và resume
        """
        self.is_pause = not self.is_pause
    
    def pause_game(self):
        """
        Pause game
        - Đặt trạng thái pause = True
        """
        self.is_pause = True
    
    def restart_game(self):
        """
        Restart game với algorithm hiện tại
        - Tạo game engine mới
        - Reset tất cả giá trị về ban đầu
        - Bắt đầu ở trạng thái pause
        """
        self.game = Game(self.algorithm)  # Tạo game mới với algorithm hiện tại
        
        # Áp dụng cài đặt few pellets mode nếu có
        if hasattr(self.layout, 'few_pellets_mode') and hasattr(self.layout, 'few_pellets_count'):
            self.game.set_few_pellets_mode(
                self.layout.few_pellets_mode, 
                self.layout.few_pellets_count
            )
        
        if hasattr(self.game, 'initialize_game'):
            self.game.initialize_game()
        # Reset tất cả giá trị game về ban đầu
        self.score = getattr(self.game, 'score', 0)
        self.lives = getattr(self.game, 'lives', 5)  # Game bắt đầu với 5 mạng
        self.level = getattr(self.game, 'level', 0)  # Game bắt đầu với level 0
        self.game_running = True
        self.is_pause = True  # Bắt đầu ở trạng thái pause
        self.layout.is_playing = False  # Reset trạng thái play
        self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
    
    def game_over(self):
        """
        Xử lý game over
        - Đặt game_running = False
        - Có thể thêm logic game over ở đây
        """
        self.game_running = False
        # Có thể thêm logic game over ở đây
    
    def on_resume(self):
        """
        Được gọi khi state được resume
        - Hiện tại không có logic đặc biệt
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
        # Cập nhật volume cho game state
        if hasattr(self.app, 'sfx_volume'):
            self.app.sfx_volume = settings.get('sfx_volume', 0.8)
        
        # Cập nhật music volume nếu có
        if 'music_volume' in settings:
            pygame.mixer.music.set_volume(settings['music_volume'])
        
        # Cập nhật fullscreen nếu cần
        if 'fullscreen' in settings and settings['fullscreen']:
            self.app.screen = pygame.display.set_mode((self.app.WIDTH, self.app.HEIGHT), pygame.FULLSCREEN)
        else:
            self.app.screen = pygame.display.set_mode((self.app.WIDTH, self.app.HEIGHT))
    
    def start_game(self):
        """
        Bắt đầu game
        - Unpause game nếu đang pause
        - Phát âm thanh start
        - Bắt đầu timer khi user thực sự start
        """
        if self.is_pause:
            self.is_pause = False
            self.layout.is_playing = True
            if hasattr(self.game, 'pause'):
                self.game.pause.setPause(pauseTime=0)  # Unpause game
            
            # Bắt đầu timer ngay khi user nhấn SPACE
            if hasattr(self.game, 'start_timer'):
                self.game.start_timer()
            
            # Reset step counters khi bắt đầu game mới
            if hasattr(self.game, 'reset_steps'):
                self.game.reset_steps()
            
            # Phát âm thanh start
            if hasattr(self.app, 'sound_system'):
                self.app.sound_system.play_sound('button_click')
    
    def _apply_heuristic_change(self, new_heuristic):

        # Lưu setting vào config
        if hasattr(self.app, 'config'):
            self.app.config.set('algorithm_heuristic', new_heuristic)
        
        # Cập nhật game engine cho thuật toán hiện tại
        if hasattr(self.game, 'set_algorithm_heuristic'):
            self.game.set_algorithm_heuristic(new_heuristic)
            
            # Đảm bảo Pacman sử dụng heuristic mới ngay lập tức
            if hasattr(self.game, 'pacman') and self.game.pacman:
                self.game.pacman.path = []
                self.game.pacman.locked_target_node = None
                self.game.pacman.previous_node = None
                self.game.pacman.path_computed = False
                
                # Force recompute path với heuristic mới
                if hasattr(self.game.pacman, 'force_recompute_path'):
                    self.game.pacman.force_recompute_path()
                    
    def return_to_menu(self):
        """
        Quay lại menu chính
        - Dừng game hiện tại
        - Chuyển về menu state
        """
        self.game_running = False
        if hasattr(self.game, 'pause'):
            self.game.pause.setPause(playerPaused=True)
        
        if hasattr(self.app, 'sound_system'):
            self.app.sound_system.stop_music()
        
        menu_state = MenuState(self.app, self.machine)
        self.replace_state(menu_state)
    
    def toggle_ai_mode(self):
        if hasattr(self.game, 'ai_mode'):
            self.game.set_ai_mode(not self.game.ai_mode)
            mode_text = "AI" if self.game.ai_mode else "Player"
