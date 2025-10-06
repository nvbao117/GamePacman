# =============================================================================
# MAIN.PY - FILE CHÍNH CỦA GAME PAC-MAN
# =============================================================================
# File này chứa class App chính - điểm khởi đầu của toàn bộ game
# Quản lý vòng lặp chính, khởi tạo các hệ thống, và điều phối các state

import pygame 
import logging
from statemachine import StateMachine
from states.menu_state import MenuState
from states.game_init_state import GameInitState
from ui.setting_modal import SettingModal
from sound_system import SoundSystem,SilentSoundSystem
from config_manager import ConfigManager, ConfigCategory
import sys

logger = logging.getLogger(__name__)
class App: 
    def __init__(self):
        """
        Khởi tạo ứng dụng Pac-Man
        - Thiết lập config system
        - Khởi tạo pygame và các hệ thống con
        - Tạo state machine với GameInitState làm state đầu tiên
        """
        
        # Khởi tạo ConfigManager - quản lý cấu hình game
        try:
            self.config = ConfigManager()
        except Exception as e:
            pygame.quit()
            sys.exit(1)
        
        # Khởi tạo pygame
        pygame.init()
        
        # Khởi tạo mixer cho âm thanh với cấu hình chất lượng cao
        # pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        
        # Thiết lập màn hình dựa trên cấu hình
        self._setup_display()
        
        # Khởi tạo clock để kiểm soát FPS
        self.clock = pygame.time.Clock()
        self.running = True  # Flag để kiểm soát vòng lặp chính

        # Backward compatibility - thuộc tính settings để tương thích ngược
        self.settings = self.config.config
        
        # Tạo hệ thống âm thanh sau khi config được tạo
        # self.sound_system = SoundSystem(self)
        self.sound_system = None
        self._initialize_audio_system()
        # Lưu reference đến game object hiện tại (nếu có)
        self.current_game = None
                
        # Backward compatibility for sfx_volume
        self.sfx_volume = self.config.get('sfx_volume', 0.8)

        # Tạo state machine với GameInitState làm state đầu tiên
        self.state_machine = StateMachine(MenuState, self)
        
        # Thiết lập các listener cho config changes
        self._setup_config_listeners()
            
    def _setup_display(self):
        """
        Thiết lập màn hình dựa trên cấu hình
        - Lấy thông tin màn hình hiện tại
        - Áp dụng cài đặt f
        ullscreen và vsync
        - Tạo surface để vẽ
        """
        info = pygame.display.Info()
        self.WIDTH, self.HEIGHT = info.current_w, info.current_h
        
        # Lấy cài đặt hiển thị từ config
        fullscreen = self.config.get('fullscreen', True)
        vsync = self.config.get('vsync', True)
        
        # Thiết lập flags cho pygame display
        flags = pygame.FULLSCREEN if fullscreen else 0
        if vsync:
            flags |= pygame.SCALED
        
        # Tạo màn hình với cài đặt đã chọn
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), flags)
        pygame.display.set_caption("Pac-Man Arcade - Professional Edition")
    def _initialize_audio_system(self):
        """Initialize pygame mixer and fall back to a silent sound system if needed."""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as exc:
            logger.warning("Unable to initialize audio mixer: %s", exc)
            self.sound_system = SilentSoundSystem(self)
            return

        try:
            self.sound_system = SoundSystem(self)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error("Sound system initialization failed: %s", exc)
            pygame.mixer.quit()
            self.sound_system = SilentSoundSystem(self)
    def _setup_config_listeners(self):
        """
        Thiết lập các listener cho thay đổi cấu hình
        - Audio listeners: phản ứng ngay lập tức với thay đổi âm thanh
        - Video listeners: yêu cầu restart để có hiệu lực
        """
        # Audio listeners - cập nhật ngay lập tức
        self.config.add_listener('master_volume', self._on_audio_config_changed)
        self.config.add_listener('music_volume', self._on_audio_config_changed)
        self.config.add_listener('sfx_volume', self._on_audio_config_changed)
        self.config.add_listener('music_enabled', self._on_audio_config_changed)
        self.config.add_listener('sfx_enabled', self._on_audio_config_changed)
        
        # Video listeners - yêu cầu restart để có hiệu lực
        self.config.add_listener('fullscreen', self._on_video_config_changed)
        self.config.add_listener('vsync', self._on_video_config_changed)
        
    
    def _on_audio_config_changed(self, key: str, new_value, old_value):
        """
        Xử lý thay đổi cấu hình âm thanh
        - Cập nhật volume của sound system
        - Cập nhật backward compatibility
        """
        if hasattr(self, 'sound_system'):
            self.sound_system.update_volume()
        
        # Cập nhật tương thích ngược
        self.settings[key] = new_value
        if key == 'sfx_volume':
            self.sfx_volume = new_value
    
    def _on_video_config_changed(self, key: str, new_value, old_value):
        """
        Xử lý thay đổi cấu hình video (yêu cầu restart)
        - Cập nhật settings cho hiệu ứng tức thì nếu có thể
        """
        # Cập nhật settings cho hiệu ứng tức thì nếu có thể
        self.settings[key] = new_value
    
    def run(self): 
        fps_limit = self.config.get('fps_limit', 30)
        
        while self.running:
            dt = self.clock.tick(fps_limit) / 1000
            
            # Xử lý events từ pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                
                # Xử lý events của state hiện tại
                if self.state_machine.current_state:
                    self.state_machine.current_state.handle_events(event)

            # Cập nhật các hệ thống
            self.state_machine.update()  # Cập nhật state machine
            
            # Cập nhật logic game
            if self.state_machine.current_state:
                self.state_machine.current_state.logic()
            
            # Render
            if self.state_machine.current_state:
                self.state_machine.current_state.draw(self.screen)
            else:
                # Nếu không có state nào, vẽ màn hình đen
                self.screen.fill((0, 0, 0))

            # Cập nhật màn hình
            pygame.display.flip()

        # Tự động lưu config và dọn dẹp trước khi thoát
        if hasattr(self, 'sound_system'):
            self.sound_system.cleanup()
        
        # Lưu cấu hình
        if hasattr(self, 'config'):
            self.config.save_config()
        
        # Thoát pygame và ứng dụng
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.run()