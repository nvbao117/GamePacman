# =============================================================================
# SETTING_MODAL.PY - MODAL WINDOW CÀI ĐẶT DÙNG CHUNG
# =============================================================================
# File này chứa SettingModal - cửa sổ popup cài đặt có thể dùng từ bất kỳ state nào
# Không phải là state riêng biệt, chỉ là UI component

import pygame
import math
import numpy as np
from pathlib import Path

from ui.button import PacManButton
from ui.neontext import NeonText
from ui.slider import Slider
from ui.checkbox import CheckBox
from ui.constants import *

class SettingModal:
    """
    SettingModal - Modal window cài đặt dùng chung
    - Có thể mở từ bất kỳ state nào
    - Không phải là state riêng biệt
    - Quản lý âm thanh, nhạc nền, và các settings
    """
    
    def __init__(self, app):
        self.app = app
        self.visible = False
        
        # Settings values
        self.master_volume = 0.7
        self.music_volume = 0.5
        self.sfx_volume = 0.8
        self.music_enabled = True
        self.sfx_enabled = True
        self.fullscreen = False
        self.vsync = True
        self.background_music_enabled = True
        self.ambient_sounds_enabled = True
        
        # Modal dialog properties - kích thước lớn hơn và đẹp hơn
        self.dialog_width = 600
        self.dialog_height = 500
        self.dialog_x = (self.app.WIDTH - self.dialog_width) // 2
        self.dialog_y = (self.app.HEIGHT - self.dialog_height) // 2
        
        
        # UI Components
        self.title = None
        self.back_button = None
        self.sliders = []
        self.checkboxes = []
        
        # Animation
        self.animation_time = 0
        
        # Load settings
        self._load_settings()
        self._setup_ui()
    
    def _load_settings(self):
        """Load settings từ ConfigManager"""
        if hasattr(self.app, 'config'):
            config = self.app.config
            self.master_volume = config.get('master_volume', 0.7)
            self.music_volume = config.get('music_volume', 0.5)
            self.sfx_volume = config.get('sfx_volume', 0.8)
            self.music_enabled = config.get('music_enabled', True)
            self.sfx_enabled = config.get('sfx_enabled', True)
            self.fullscreen = config.get('fullscreen', True)
            self.vsync = config.get('vsync', True)
            self.background_music_enabled = config.get('background_music_enabled', True)
            self.ambient_sounds_enabled = config.get('ambient_sounds_enabled', True)
            
            # Additional settings - enhanced
            self.show_fps = config.get('show_fps', False)
            self.quality = config.get('quality', 'high')
            self.difficulty = config.get('difficulty', 'normal')
            self.ui_scale = config.get('ui_scale', 1.0)
            self.animations_enabled = config.get('animations_enabled', True)
            self.particle_effects = config.get('particle_effects', True)
            self.ai_speed = config.get('ai_speed', 1.0)
            self.show_path = config.get('show_path', False)
            self.auto_pause = config.get('auto_pause', True)
            self.few_pellets_mode = config.get('few_pellets_mode', False)
            self.few_pellets_count = config.get('few_pellets_count', 20)
        else:
            # Default values
            self.master_volume = 0.7
            self.music_volume = 0.5
            self.sfx_volume = 0.8
            self.music_enabled = True
            self.sfx_enabled = True
            self.fullscreen = True
            self.vsync = True
            self.background_music_enabled = True
            self.ambient_sounds_enabled = True
            self.show_fps = False
            self.quality = 'high'
            self.difficulty = 'normal'
            self.ui_scale = 1.0
            self.animations_enabled = True
            self.particle_effects = True
            self.ai_speed = 1.0
            self.show_path = False
            self.auto_pause = True
            self.few_pellets_mode = False
            self.few_pellets_count = 20
    
    def _save_settings(self):
        """Lưu settings vào ConfigManager"""
        if hasattr(self.app, 'config'):
            config = self.app.config
            config.set('master_volume', self.master_volume)
            config.set('music_volume', self.music_volume)
            config.set('sfx_volume', self.sfx_volume)
            config.set('music_enabled', self.music_enabled)
            config.set('sfx_enabled', self.sfx_enabled)
            config.set('fullscreen', self.fullscreen)
            config.set('vsync', self.vsync)
            config.set('background_music_enabled', self.background_music_enabled)
            config.set('ambient_sounds_enabled', self.ambient_sounds_enabled)
            config.set('show_fps', self.show_fps)
            config.set('quality', self.quality)
            config.set('difficulty', self.difficulty)
            config.set('ui_scale', self.ui_scale)
            config.set('animations_enabled', self.animations_enabled)
            config.set('particle_effects', self.particle_effects)
            config.set('ai_speed', self.ai_speed)
            config.set('show_path', self.show_path)
            config.set('auto_pause', self.auto_pause)
            config.set('few_pellets_mode', self.few_pellets_mode)
            config.set('few_pellets_count', self.few_pellets_count)
            
            # Save to file
            config.save_config()
        
        # Backward compatibility
        if not hasattr(self.app, 'settings'):
            self.app.settings = {}
        
        self.app.settings.update({
            'master_volume': self.master_volume,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'music_enabled': self.music_enabled,
            'sfx_enabled': self.sfx_enabled,
            'fullscreen': self.fullscreen,
            'vsync': self.vsync,
            'background_music_enabled': self.background_music_enabled,
            'ambient_sounds_enabled': self.ambient_sounds_enabled,
            'show_fps': self.show_fps,
            'quality': self.quality,
            'difficulty': self.difficulty,
            'ui_scale': self.ui_scale,
            'animations_enabled': self.animations_enabled,
            'particle_effects': self.particle_effects,
            'ai_speed': self.ai_speed,
            'show_path': self.show_path,
            'auto_pause': self.auto_pause
        })
    
    def _setup_ui(self):
        """Thiết lập giao diện UI cho modal dialog"""
        # Title với hiệu ứng đẹp hơn
        self.title = NeonText(
            self.app,
            "⚙️ GAME SETTINGS",
            PAC_YELLOW,
            self.dialog_x + self.dialog_width // 2,
            self.dialog_y + 30,
            32,
            glow=True,
            outline=True
        )
        
        # Subtitle
        self.subtitle = NeonText(
            self.app,
            "Customize your gaming experience",
            GHOST_PINK,
            self.dialog_x + self.dialog_width // 2,
            self.dialog_y + 55,
            16,
            outline=True
        )
        
        # Close button với icon
        self.close_button = PacManButton(
            self.app,
            (self.dialog_x + self.dialog_width - 60, self.dialog_y + 20),
            "✕",
            onclick=[self.close]
        )
        
        # Apply button
        self.apply_button = PacManButton(
            self.app,
            (self.dialog_x + self.dialog_width - 100, self.dialog_y + self.dialog_height - 40),
            "APPLY",
            onclick=[self._apply_settings]
        )
        
        # Reset button
        self.reset_button = PacManButton(
            self.app,
            (self.dialog_x + 20, self.dialog_y + self.dialog_height - 40),
            "RESET",
            onclick=[self._reset_settings]
        )
        
        # Volume section
        self._setup_volume_section()
        
        # Display section
        self._setup_display_section()
        
        # Gameplay section
        self._setup_gameplay_section()
        
        # Additional sections integrated directly in draw methods
        
        # Collect all interactive elements
        self.sliders = [self.master_slider, self.music_slider, self.sfx_slider, self.few_pellets_slider]
        self.checkboxes = [self.music_checkbox, self.sfx_checkbox, self.background_music_checkbox, 
                          self.ambient_sounds_checkbox, self.fullscreen_checkbox, self.vsync_checkbox,
                          self.few_pellets_checkbox]
    
    def _setup_volume_section(self):
        """Thiết lập phần Volume"""
        section_y = self.dialog_y + 60
        
        # Volume title
        self.volume_title = NeonText(
            self.app,
            "🔊 AUDIO",
            GHOST_BLUE,
            self.dialog_x + 20,
            section_y,
            16,
            outline=True
        )
        
        # Volume sliders với layout nhỏ gọn hơn
        slider_y_start = section_y + 25
        slider_spacing = 35  # Giảm khoảng cách giữa các slider
        slider_width = 200  # Giảm chiều rộng slider
        
        # Master Volume
        self.master_slider = Slider(
            self.dialog_x + 30,
            slider_y_start,
            slider_width,
            30,
            min_value=0.0,
            max_value=1.0,
            initial_value=self.master_volume
        )
        
        # Music Volume
        self.music_slider = Slider(
            self.dialog_x + 30,
            slider_y_start + slider_spacing,
            slider_width,
            30,
            min_value=0.0,
            max_value=1.0,
            initial_value=self.music_volume
        )
        
        # SFX Volume
        self.sfx_slider = Slider(
            self.dialog_x + 30,
            slider_y_start + slider_spacing * 2,
            slider_width,
            30,
            min_value=0.0,
            max_value=1.0,
            initial_value=self.sfx_volume
        )
        
        # Test Sound button
        self.test_sound_button = PacManButton(
            self.app,
            (self.dialog_x + 300, slider_y_start + slider_spacing * 2),
            "🔊 TEST",
            onclick=[self._play_test_sound]
        )
        
        # Volume checkboxes - di chuyển xuống dưới để tránh chồng lên slider
        checkbox_y = slider_y_start + 180  # Di chuyển xuống dưới
        self.music_checkbox = CheckBox(
            self.dialog_x + 30,
            checkbox_y,
            20,
            "Music",
            18,
            self.music_enabled
        )
        
        self.sfx_checkbox = CheckBox(
            self.dialog_x + 30,
            checkbox_y + 40,
            20,
            "SFX",
            18,
            self.sfx_enabled
        )
        
        self.background_music_checkbox = CheckBox(
            self.dialog_x + 30,
            checkbox_y + 80,
            20,
            "Background Music",
            18,
            self.background_music_enabled
        )
        
        self.ambient_sounds_checkbox = CheckBox(
            self.dialog_x + 30,
            checkbox_y + 120,
            20,
            "Ambient Sounds",
            18,
            self.ambient_sounds_enabled
        )
    
    def _setup_display_section(self):
        """Thiết lập phần Display"""
        section_y = self.dialog_y + 200  # Di chuyển lên gần hơn
        
        # Display title
        self.display_title = NeonText(
            self.app,
            "🖥️ DISPLAY",
            GHOST_ORANGE,
            self.dialog_x + 20,
            section_y,
            16,
            outline=True
        )
        
        # Display checkboxes
        checkbox_y = section_y + 25
        self.fullscreen_checkbox = CheckBox(
            self.dialog_x + 30,
            checkbox_y,
            20,
            "Fullscreen Mode",
            18,
            self.fullscreen
        )
        
        self.vsync_checkbox = CheckBox(
            self.dialog_x + 30,
            checkbox_y + 35,
            20,
            "Vertical Sync",
            18,
            self.vsync
        )
    
    def _setup_gameplay_section(self):
        """Thiết lập phần Gameplay"""
        section_y = self.dialog_y + 320  # Di chuyển xuống dưới
        
        # Gameplay title
        self.gameplay_title = NeonText(
            self.app,
            "🎮 GAMEPLAY",
            GHOST_BLUE,
            self.dialog_x + 20,
            section_y,
            16,
            outline=True
        )
        
        # Few pellets mode checkbox
        checkbox_y = section_y + 25
        self.few_pellets_checkbox = CheckBox(
            self.dialog_x + 30,
            checkbox_y,
            20,
            "Few Pellets Mode",
            18,
            self.few_pellets_mode
        )
        
        # Few pellets count slider
        self.few_pellets_slider = Slider(
            self.dialog_x + 30,
            checkbox_y + 40,
            200,
            30,
            min_value=5,
            max_value=100,
            initial_value=self.few_pellets_count
        )
        
        # Few pellets count label
        self.few_pellets_label = NeonText(
            self.app,
            f"Pellets Count: {int(self.few_pellets_count)}",
            DOT_WHITE,
            self.dialog_x + 250,
            checkbox_y + 50,
            14,
            outline=True
        )
    
    def show(self):
        """Hiển thị modal"""
        self.visible = True
        self._load_settings()
        self._update_ui_components()
    
    def close(self):
        """Đóng modal"""
        self.app.sound_system.play_sound('button_click')
        self.visible = False
        self._save_settings()
    
    def _apply_settings(self):
        """Áp dụng settings"""
        self.app.sound_system.play_sound('button_click')
        self._update_settings()
    
    def _reset_settings(self):
        """Reset settings về mặc định"""
        self.master_volume = 0.7
        self.music_volume = 0.5
        self.sfx_volume = 0.8
        self.music_enabled = True
        self.sfx_enabled = True
        self.background_music_enabled = True
        self.ambient_sounds_enabled = True
        self.fullscreen = True
        self.vsync = True
        self.show_fps = False
        self.quality = 'high'
        self.difficulty = 'normal'
        self.ui_scale = 1.0
        self.animations_enabled = True
        self.particle_effects = True
        self.ai_speed = 1.0
        self.show_path = False
        self.auto_pause = True
        
        self._update_ui_components()
        self._apply_audio_settings()
        self._apply_display_settings()
        self._save_settings()
    
    def handle_events(self, event):
        """Xử lý sự kiện - chỉ khi modal đang hiển thị"""
        if not self.visible:
            return False
            
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
        
        # Handle mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Check close button
            close_rect = pygame.Rect(self.dialog_x + self.dialog_width - 50, self.dialog_y + 10, 40, 30)
            if close_rect.collidepoint(mouse_x, mouse_y):
                self.close()
                return True
            
            # Check volume sliders - chỉ cập nhật khi click
            y_start = self.dialog_y + 100
            slider_rect = pygame.Rect(self.dialog_x + 50, y_start, 200, 18)
            if slider_rect.collidepoint(mouse_x, mouse_y):
                self.master_volume = (mouse_x - (self.dialog_x + 50)) / 200
                self.master_volume = max(0, min(1, self.master_volume))
                self._update_settings(apply_immediately=True)
                return True
            
            slider_rect = pygame.Rect(self.dialog_x + 50, y_start + 50, 200, 18)
            if slider_rect.collidepoint(mouse_x, mouse_y):
                self.music_volume = (mouse_x - (self.dialog_x + 50)) / 200
                self.music_volume = max(0, min(1, self.music_volume))
                self._update_settings(apply_immediately=True)
                return True
            
            slider_rect = pygame.Rect(self.dialog_x + 50, y_start + 100, 200, 18)
            if slider_rect.collidepoint(mouse_x, mouse_y):
                self.sfx_volume = (mouse_x - (self.dialog_x + 50)) / 200
                self.sfx_volume = max(0, min(1, self.sfx_volume))
                self._update_settings(apply_immediately=True)
                return True
            
            # Check checkboxes - không áp dụng ngay lập tức
            checkbox_y = y_start + 150
            music_checkbox_rect = pygame.Rect(self.dialog_x + 50, checkbox_y, 20, 20)
            if music_checkbox_rect.collidepoint(mouse_x, mouse_y):
                self.music_enabled = not self.music_enabled
                self._update_settings()
                return True
        
            sfx_checkbox_rect = pygame.Rect(self.dialog_x + 50, checkbox_y + 30, 20, 20)
            if sfx_checkbox_rect.collidepoint(mouse_x, mouse_y):
                self.sfx_enabled = not self.sfx_enabled
                self._update_settings()
                return True
            
            # Check display checkboxes
            display_y = self.dialog_y + 250
            fullscreen_checkbox_rect = pygame.Rect(self.dialog_x + 50, display_y, 20, 20)
            if fullscreen_checkbox_rect.collidepoint(mouse_x, mouse_y):
                self.fullscreen = not self.fullscreen
                self._update_settings()
                return True
            
            vsync_checkbox_rect = pygame.Rect(self.dialog_x + 50, display_y + 30, 20, 20)
            if vsync_checkbox_rect.collidepoint(mouse_x, mouse_y):
                self.vsync = not self.vsync
                self._update_settings()
                return True
            
            # Check buttons
            button_y = self.dialog_y + 350
            apply_rect = pygame.Rect(self.dialog_x + 50, button_y, 100, 40)
            if apply_rect.collidepoint(mouse_x, mouse_y):
                self._apply_settings()
                return True
            
            # Check additional controls
            additional_y = self.dialog_y + 280
            
            # Show FPS checkbox
            fps_rect = pygame.Rect(self.dialog_x + 50, additional_y + 20, 18, 18)
            if fps_rect.collidepoint(mouse_x, mouse_y):
                self.show_fps = not self.show_fps
                self._update_settings(apply_immediately=False)
                return True
            
            # Animations checkbox
            anim_rect = pygame.Rect(self.dialog_x + 180, additional_y + 20, 18, 18)
            if anim_rect.collidepoint(mouse_x, mouse_y):
                self.animations_enabled = not self.animations_enabled
                self._update_settings(apply_immediately=False)
                return True
            
            # Particle Effects checkbox
            particle_rect = pygame.Rect(self.dialog_x + 320, additional_y + 20, 18, 18)
            if particle_rect.collidepoint(mouse_x, mouse_y):
                self.particle_effects = not self.particle_effects
                self._update_settings(apply_immediately=False)
                return True
            
            # Few Pellets Mode checkbox
            few_pellets_rect = pygame.Rect(self.dialog_x + 50, additional_y + 50, 18, 18)
            if few_pellets_rect.collidepoint(mouse_x, mouse_y):
                self.few_pellets_mode = not self.few_pellets_mode
                self._update_settings(apply_immediately=False)
                return True
            
            # Few Pellets Count slider
            if self.few_pellets_mode:
                few_pellets_slider_rect = pygame.Rect(self.dialog_x + 50, additional_y + 75, 200, 20)
                if few_pellets_slider_rect.collidepoint(mouse_x, mouse_y):
                    self.few_pellets_count = int(5 + ((mouse_x - (self.dialog_x + 50)) / 200) * 95)
                    self.few_pellets_count = max(5, min(100, self.few_pellets_count))
                    self._update_settings(apply_immediately=False)
                    return True
            
            # AI Speed slider
            ai_speed_y = additional_y + 55
            ai_slider_rect = pygame.Rect(self.dialog_x + 130, ai_speed_y + 5, 150, 15)
            if ai_slider_rect.collidepoint(mouse_x, mouse_y):
                self.ai_speed = ((mouse_x - (self.dialog_x + 130)) / 150) * 3.0
                self.ai_speed = max(0.1, min(3.0, self.ai_speed))
                self._update_settings(apply_immediately=True)
                return True
            
            reset_rect = pygame.Rect(self.dialog_x + 200, button_y, 100, 40)
            if reset_rect.collidepoint(mouse_x, mouse_y):
                self._reset_settings()
                return True
        
        return False
    
    def _update_settings(self, apply_immediately=False):
        """Cập nhật settings từ UI components"""
        # Update values từ UI components
        self.master_volume = self.master_slider.get_value()
        self.music_volume = self.music_slider.get_value()
        self.sfx_volume = self.sfx_slider.get_value()
        self.music_enabled = self.music_checkbox.is_checked()
        self.sfx_enabled = self.sfx_checkbox.is_checked()
        self.background_music_enabled = self.background_music_checkbox.is_checked()
        self.ambient_sounds_enabled = self.ambient_sounds_checkbox.is_checked()
        self.fullscreen = self.fullscreen_checkbox.is_checked()
        self.vsync = self.vsync_checkbox.is_checked()
        self.few_pellets_mode = self.few_pellets_checkbox.is_checked()
        self.few_pellets_count = int(self.few_pellets_slider.get_value())
        
        # Validate settings
        self._validate_settings()
        
        # Chỉ áp dụng ngay lập tức nếu được yêu cầu (cho sliders)
        if apply_immediately:
            self._apply_audio_settings()
            self._apply_display_settings()
        
        # Lưu settings
        self._save_settings()
    
    def _validate_settings(self):
        """Validate tất cả settings"""
        self.master_volume = max(0.0, min(1.0, self.master_volume))
        self.music_volume = max(0.0, min(1.0, self.music_volume))
        self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))
        self.music_enabled = bool(self.music_enabled)
        self.sfx_enabled = bool(self.sfx_enabled)
        self.background_music_enabled = bool(self.background_music_enabled)
        self.ambient_sounds_enabled = bool(self.ambient_sounds_enabled)
        self.fullscreen = bool(self.fullscreen)
        self.vsync = bool(self.vsync)
    
    def _apply_audio_settings(self):
        """Áp dụng cài đặt âm thanh với hệ thống âm thanh nâng cao"""
        try:
            # Tính toán volume cuối cùng
            final_music_volume = self.master_volume * self.music_volume if self.music_enabled else 0
            final_sfx_volume = self.master_volume * self.sfx_volume if self.sfx_enabled else 0
            
            # Áp dụng music volume
            pygame.mixer.music.set_volume(final_music_volume)
            
            # Cập nhật SFX volume trong app
            if hasattr(self.app, 'sfx_volume'):
                self.app.sfx_volume = final_sfx_volume
            
            # Cập nhật settings trong app
            if hasattr(self.app, 'settings'):
                self.app.settings.update({
                    'master_volume': self.master_volume,
                    'music_volume': self.music_volume,
                    'sfx_volume': self.sfx_volume,
                    'music_enabled': self.music_enabled,
                    'sfx_enabled': self.sfx_enabled,
                    'background_music_enabled': self.background_music_enabled,
                    'ambient_sounds_enabled': self.ambient_sounds_enabled,
                    'fullscreen': self.fullscreen,
                    'vsync': self.vsync
                })
            
            # Thông báo cho tất cả states về việc thay đổi settings
            self._notify_settings_changed()
            
            # Phát âm thanh test nếu SFX được bật
            if self.sfx_enabled and final_sfx_volume > 0:
                self._play_test_sound()
                
        except Exception as e:
            pass
    def _notify_settings_changed(self):
        """Thông báo cho tất cả states về việc thay đổi settings"""
        try:
            # Thông báo cho state machine hiện tại
            if hasattr(self.app, 'state_machine') and self.app.state_machine.current_state:
                current_state = self.app.state_machine.current_state
                if hasattr(current_state, 'on_settings_changed'):
                    current_state.on_settings_changed(self.app.settings)
            
            # Thông báo cho tất cả states khác nếu cần
        except Exception as e:
            pass
    def _play_test_sound(self):
        """Phát âm thanh test để người dùng nghe thấy volume"""
        try:
            # Sử dụng âm thanh pellet để test
            self.app.sound_system.play_sound('pellet')
        except Exception as e:
            pass
    def _apply_display_settings(self):
        """Áp dụng cài đặt hiển thị"""
        try:
            if self.fullscreen:
                self.app.screen = pygame.display.set_mode((self.app.WIDTH, self.app.HEIGHT), pygame.FULLSCREEN)
            else:
                self.app.screen = pygame.display.set_mode((self.app.WIDTH, self.app.HEIGHT))
            
            # Cập nhật VSync nếu có thể
            if hasattr(self.app, 'clock'):
                self.app.clock = pygame.time.Clock()
                
        except Exception as e:
            pass
    def _update_ui_components(self):
        """Cập nhật UI components"""
        if not hasattr(self, 'master_slider'):
            return
            
        self.master_slider.set_value(max(0.0, min(1.0, self.master_volume)))
        self.music_slider.set_value(max(0.0, min(1.0, self.music_volume)))
        self.sfx_slider.set_value(max(0.0, min(1.0, self.sfx_volume)))
        self.music_checkbox.set_checked(bool(self.music_enabled))
        self.sfx_checkbox.set_checked(bool(self.sfx_enabled))
        self.background_music_checkbox.set_checked(bool(self.background_music_enabled))
        self.ambient_sounds_checkbox.set_checked(bool(self.ambient_sounds_enabled))
        self.fullscreen_checkbox.set_checked(bool(self.fullscreen))
        self.vsync_checkbox.set_checked(bool(self.vsync))
        self.few_pellets_checkbox.set_checked(bool(self.few_pellets_mode))
        self.few_pellets_slider.set_value(max(5, min(100, self.few_pellets_count)))
    
    def update(self, dt):
        """Cập nhật logic"""
        if not self.visible:
            return
        self.animation_time += dt
    
    def draw(self, screen):
        """Vẽ modal dialog với giao diện đẹp"""
        if not self.visible:
            return
        
        # Vẽ overlay mờ đẹp mắt với hiệu ứng vignette
        overlay = pygame.Surface((self.app.WIDTH, self.app.HEIGHT), pygame.SRCALPHA)
        
        # Tạo hiệu ứng vignette (tối dần từ trong ra ngoài)
        center_x, center_y = self.app.WIDTH // 2, self.app.HEIGHT // 2
        max_radius = max(self.app.WIDTH, self.app.HEIGHT) // 2
        
        # Vẽ gradient mờ từ trong ra ngoài với độ trong suốt vừa phải
        for radius in range(max_radius, 0, -3):  # Giảm step để mượt hơn
            alpha = int(100 * (1 - radius / max_radius))  # Tăng alpha để vừa phải
            alpha = max(0, min(100, alpha))
            color = (0, 0, 0, alpha)
            pygame.draw.circle(overlay, color, (center_x, center_y), radius)
        
        # Thêm hiệu ứng blur nhẹ hơn
        for i in range(1):  # Chỉ 1 layer blur
            blur_overlay = pygame.Surface((self.app.WIDTH, self.app.HEIGHT), pygame.SRCALPHA)
            blur_alpha = 25  # Alpha vừa phải
            blur_overlay.fill((0, 0, 0, blur_alpha))
            screen.blit(blur_overlay, (0, 0))
        
        screen.blit(overlay, (0, 0))
        
        # Vẽ dialog window với hiệu ứng đẹp hơn
        dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        
        # Vẽ shadow cho dialog với hiệu ứng đẹp hơn
        shadow_rect = pygame.Rect(self.dialog_x + 5, self.dialog_y + 5, self.dialog_width, self.dialog_height)
        shadow_surface = pygame.Surface((self.dialog_width, self.dialog_height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 80), (0, 0, self.dialog_width, self.dialog_height), border_radius=12)
        screen.blit(shadow_surface, (self.dialog_x + 5, self.dialog_y + 5))
        
        # Vẽ background dialog với gradient đẹp hơn
        dialog_surface = pygame.Surface((self.dialog_width, self.dialog_height), pygame.SRCALPHA)
        
        # Background gradient
        for y in range(self.dialog_height):
            alpha = int(180 - (y / self.dialog_height) * 40)  # Gradient từ trên xuống
            color = (15, 20, 30, alpha)
            pygame.draw.line(dialog_surface, color, (0, y), (self.dialog_width, y))
        
        # Border với hiệu ứng neon
        pygame.draw.rect(dialog_surface, (50, 100, 200, 120), (0, 0, self.dialog_width, self.dialog_height), 3, border_radius=12)
        pygame.draw.rect(dialog_surface, (100, 150, 255, 80), (0, 0, self.dialog_width, self.dialog_height), 1, border_radius=12)
        
        screen.blit(dialog_surface, (self.dialog_x, self.dialog_y))
        
        # Vẽ title với hiệu ứng đẹp hơn
        font = pygame.font.Font(None, 32)
        title_text = font.render("⚙️ SETTINGS", True, (100, 200, 255))
        title_rect = title_text.get_rect(center=(self.dialog_x + self.dialog_width // 2, self.dialog_y + 35))
        
        # Vẽ title với glow effect
        for i in range(3):
            glow_color = (100 + i*20, 200 + i*10, 255, 100 - i*30)
            glow_text = font.render("⚙️ SETTINGS", True, glow_color)
            glow_rect = glow_text.get_rect(center=(title_rect.centerx + i, title_rect.centery + i))
            screen.blit(glow_text, glow_rect)
        
        screen.blit(title_text, title_rect)
        
        # Vẽ nút đóng với hiệu ứng đẹp hơn
        close_rect = pygame.Rect(self.dialog_x + self.dialog_width - 45, self.dialog_y + 15, 30, 25)
        close_surface = pygame.Surface((30, 25), pygame.SRCALPHA)
        pygame.draw.rect(close_surface, (200, 50, 50, 180), (0, 0, 30, 25), border_radius=5)
        pygame.draw.rect(close_surface, (255, 100, 100, 200), (0, 0, 30, 25), 2, border_radius=5)
        screen.blit(close_surface, (self.dialog_x + self.dialog_width - 45, self.dialog_y + 15))
        
        close_font = pygame.font.Font(None, 20)
        close_text = close_font.render("✕", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        screen.blit(close_text, close_text_rect)
        
        # Vẽ các controls bên trong
        self._draw_volume_controls(screen)
        self._draw_display_controls(screen)
        self._draw_additional_controls(screen)
        self._draw_buttons(screen)
    
    # Additional callback methods for new settings
    def _on_ai_speed_change(self, value):
        """Callback khi AI Speed thay đổi"""
        self.ai_speed = value * 3.0  # Convert 0-1 to 0-3
        self._update_settings(apply_immediately=True)
    
    def _on_show_path_change(self, checked):
        """Callback khi Show Path thay đổi"""
        self.show_path = checked
        self._update_settings(apply_immediately=False)
    
    def _on_auto_pause_change(self, checked):
        """Callback khi Auto Pause thay đổi"""
        self.auto_pause = checked
        self._update_settings(apply_immediately=False)
    
    def _on_show_fps_change(self, checked):
        """Callback khi Show FPS thay đổi"""
        self.show_fps = checked
        self._update_settings(apply_immediately=False)
    
    def _on_animations_change(self, checked):
        """Callback khi Animations thay đổi"""
        self.animations_enabled = checked
        self._update_settings(apply_immediately=False)
    
    def _on_particle_effects_change(self, checked):
        """Callback khi Particle Effects thay đổi"""
        self.particle_effects = checked
        self._update_settings(apply_immediately=False)
    
    def _on_ui_scale_change(self, value):
        """Callback khi UI Scale thay đổi"""
        self.ui_scale = 0.5 + value * 1.5  # Convert 0-1 to 0.5-2.0
        self._update_settings(apply_immediately=True)
    
    def _draw_volume_controls(self, screen):
        """Vẽ volume controls với hiệu ứng đẹp hơn"""
        font = pygame.font.Font(None, 18)
        y_start = self.dialog_y + 80
        
        # Vẽ section title
        title_font = pygame.font.Font(None, 20)
        title_text = title_font.render("🔊 AUDIO SETTINGS", True, (100, 200, 255))
        screen.blit(title_text, (self.dialog_x + 30, y_start - 5))
        
        # Master Volume với hiệu ứng đẹp hơn
        slider_bg = pygame.Rect(self.dialog_x + 50, y_start + 20, 200, 18)
        slider_fill = pygame.Rect(self.dialog_x + 50, y_start + 20, int(200 * self.master_volume), 18)
        
        # Background slider với shadow
        shadow_rect = pygame.Rect(self.dialog_x + 51, y_start + 21, 200, 18)
        pygame.draw.rect(screen, (20, 20, 30), shadow_rect, border_radius=9)
        pygame.draw.rect(screen, (50, 50, 70), slider_bg, border_radius=9)
        
        # Fill slider với gradient đẹp hơn
        if int(200 * self.master_volume) > 0:
            for x in range(int(200 * self.master_volume)):
                color_intensity = int(80 + (x / 200) * 175)
                glow_intensity = int(50 + (x / 200) * 100)
                # Vẽ glow effect
                pygame.draw.line(screen, (0, glow_intensity, 255, 100), 
                               (self.dialog_x + 50 + x, y_start + 20), 
                               (self.dialog_x + 50 + x, y_start + 38))
                # Vẽ main color
                pygame.draw.line(screen, (0, color_intensity, 255), 
                               (self.dialog_x + 50 + x, y_start + 22), 
                               (self.dialog_x + 50 + x, y_start + 36))
        
        # Vẽ slider handle
        handle_x = self.dialog_x + 50 + int(200 * self.master_volume) - 6
        handle_rect = pygame.Rect(handle_x, y_start + 18, 12, 20)
        pygame.draw.rect(screen, (100, 200, 255), handle_rect, border_radius=6)
        pygame.draw.rect(screen, (150, 250, 255), handle_rect, 2, border_radius=6)
        
        # Label và value
        label_text = font.render("Master Volume", True, (200, 200, 200))
        screen.blit(label_text, (self.dialog_x + 30, y_start + 5))
        value_text = font.render(f"{int(self.master_volume * 100)}%", True, (100, 200, 255))
        screen.blit(value_text, (self.dialog_x + 260, y_start + 22))
        
        # Music Volume với hiệu ứng đẹp hơn
        slider_bg = pygame.Rect(self.dialog_x + 50, y_start + 50, 200, 18)
        slider_fill = pygame.Rect(self.dialog_x + 50, y_start + 50, int(200 * self.music_volume), 18)
        
        # Background slider với shadow
        shadow_rect = pygame.Rect(self.dialog_x + 51, y_start + 51, 200, 18)
        pygame.draw.rect(screen, (30, 20, 30), shadow_rect, border_radius=9)
        pygame.draw.rect(screen, (70, 50, 70), slider_bg, border_radius=9)
        
        # Fill slider với gradient đẹp hơn
        if int(200 * self.music_volume) > 0:
            for x in range(int(200 * self.music_volume)):
                color_intensity = int(80 + (x / 200) * 175)
                glow_intensity = int(50 + (x / 200) * 100)
                # Vẽ glow effect
                pygame.draw.line(screen, (255, glow_intensity, 200, 100), 
                               (self.dialog_x + 50 + x, y_start + 50), 
                               (self.dialog_x + 50 + x, y_start + 68))
                # Vẽ main color
                pygame.draw.line(screen, (255, color_intensity, 200), 
                               (self.dialog_x + 50 + x, y_start + 52), 
                               (self.dialog_x + 50 + x, y_start + 66))
        
        # Vẽ slider handle
        handle_x = self.dialog_x + 50 + int(200 * self.music_volume) - 6
        handle_rect = pygame.Rect(handle_x, y_start + 48, 12, 20)
        pygame.draw.rect(screen, (255, 100, 200), handle_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 150, 250), handle_rect, 2, border_radius=6)
        
        label_text = font.render("Music Volume", True, (200, 200, 200))
        screen.blit(label_text, (self.dialog_x + 30, y_start + 35))
        value_text = font.render(f"{int(self.music_volume * 100)}%", True, (255, 100, 200))
        screen.blit(value_text, (self.dialog_x + 260, y_start + 52))
        
        # SFX Volume với hiệu ứng đẹp hơn
        slider_bg = pygame.Rect(self.dialog_x + 50, y_start + 80, 200, 18)
        slider_fill = pygame.Rect(self.dialog_x + 50, y_start + 80, int(200 * self.sfx_volume), 18)
        
        # Background slider với shadow
        shadow_rect = pygame.Rect(self.dialog_x + 51, y_start + 81, 200, 18)
        pygame.draw.rect(screen, (30, 30, 20), shadow_rect, border_radius=9)
        pygame.draw.rect(screen, (70, 70, 50), slider_bg, border_radius=9)
        
        # Fill slider với gradient đẹp hơn
        if int(200 * self.sfx_volume) > 0:
            for x in range(int(200 * self.sfx_volume)):
                color_intensity = int(80 + (x / 200) * 175)
                glow_intensity = int(50 + (x / 200) * 100)
                # Vẽ glow effect
                pygame.draw.line(screen, (255, glow_intensity, 0, 100), 
                               (self.dialog_x + 50 + x, y_start + 80), 
                               (self.dialog_x + 50 + x, y_start + 98))
                # Vẽ main color
                pygame.draw.line(screen, (255, color_intensity, 0), 
                               (self.dialog_x + 50 + x, y_start + 82), 
                               (self.dialog_x + 50 + x, y_start + 96))
        
        # Vẽ slider handle
        handle_x = self.dialog_x + 50 + int(200 * self.sfx_volume) - 6
        handle_rect = pygame.Rect(handle_x, y_start + 78, 12, 20)
        pygame.draw.rect(screen, (255, 200, 0), handle_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 250, 100), handle_rect, 2, border_radius=6)
        
        label_text = font.render("SFX Volume", True, (200, 200, 200))
        screen.blit(label_text, (self.dialog_x + 30, y_start + 65))
        value_text = font.render(f"{int(self.sfx_volume * 100)}%", True, (255, 200, 0))
        screen.blit(value_text, (self.dialog_x + 260, y_start + 82))
        
        # Checkboxes với hiệu ứng đẹp hơn
        checkbox_y = y_start + 110
        # Music checkbox
        checkbox_rect = pygame.Rect(self.dialog_x + 50, checkbox_y, 18, 18)
        if self.music_enabled:
            pygame.draw.rect(screen, (0, 255, 100), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), checkbox_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 53, checkbox_y + 9), 
                           (self.dialog_x + 58, checkbox_y + 14), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 58, checkbox_y + 14), 
                           (self.dialog_x + 65, checkbox_y + 7), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), checkbox_rect, 2, border_radius=3)
        
        music_text = font.render("Music", True, (200, 200, 200))
        screen.blit(music_text, (self.dialog_x + 75, checkbox_y + 2))
        
        # SFX checkbox
        checkbox_rect = pygame.Rect(self.dialog_x + 50, checkbox_y + 25, 18, 18)
        if self.sfx_enabled:
            pygame.draw.rect(screen, (0, 255, 100), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), checkbox_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 53, checkbox_y + 34), 
                           (self.dialog_x + 58, checkbox_y + 39), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 58, checkbox_y + 39), 
                           (self.dialog_x + 65, checkbox_y + 32), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), checkbox_rect, 2, border_radius=3)
        
        sfx_text = font.render("SFX", True, (200, 200, 200))
        screen.blit(sfx_text, (self.dialog_x + 75, checkbox_y + 27))
    
    def _draw_display_controls(self, screen):
        """Vẽ display controls với hiệu ứng đẹp hơn"""
        font = pygame.font.Font(None, 18)
        y_start = self.dialog_y + 220
        
        # Vẽ section title
        title_font = pygame.font.Font(None, 20)
        title_text = title_font.render("🖥️ DISPLAY SETTINGS", True, (255, 150, 100))
        screen.blit(title_text, (self.dialog_x + 30, y_start - 5))
        
        # Fullscreen checkbox với hiệu ứng đẹp hơn
        checkbox_rect = pygame.Rect(self.dialog_x + 50, y_start + 10, 18, 18)
        if self.fullscreen:
            pygame.draw.rect(screen, (0, 255, 100), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), checkbox_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 53, y_start + 19), 
                           (self.dialog_x + 58, y_start + 24), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 58, y_start + 24), 
                           (self.dialog_x + 65, y_start + 17), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), checkbox_rect, 2, border_radius=3)
        
        fullscreen_text = font.render("Fullscreen Mode", True, (200, 200, 200))
        screen.blit(fullscreen_text, (self.dialog_x + 75, y_start + 12))
        
        # VSync checkbox với hiệu ứng đẹp hơn
        checkbox_rect = pygame.Rect(self.dialog_x + 50, y_start + 35, 18, 18)
        if self.vsync:
            pygame.draw.rect(screen, (0, 255, 100), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), checkbox_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 53, y_start + 44), 
                           (self.dialog_x + 58, y_start + 49), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (self.dialog_x + 58, y_start + 49), 
                           (self.dialog_x + 65, y_start + 42), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), checkbox_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), checkbox_rect, 2, border_radius=3)
        
        vsync_text = font.render("Vertical Sync", True, (200, 200, 200))
        screen.blit(vsync_text, (self.dialog_x + 75, y_start + 37))
    
    def _draw_buttons(self, screen):
        """Vẽ các buttons với hiệu ứng đẹp hơn"""
        font = pygame.font.Font(None, 18)
        y_start = self.dialog_y + 340
        
        # Apply button với hiệu ứng đẹp hơn
        apply_rect = pygame.Rect(self.dialog_x + 50, y_start, 90, 35)
        apply_surface = pygame.Surface((90, 35), pygame.SRCALPHA)
        
        # Gradient background
        for y in range(35):
            color_intensity = int(50 + (y / 35) * 100)
            pygame.draw.line(apply_surface, (0, color_intensity, 0), (0, y), (90, y))
        
        pygame.draw.rect(apply_surface, (0, 200, 0, 200), (0, 0, 90, 35), border_radius=8)
        pygame.draw.rect(apply_surface, (100, 255, 100, 255), (0, 0, 90, 35), 2, border_radius=8)
        screen.blit(apply_surface, (self.dialog_x + 50, y_start))
        
        apply_text = font.render("✓ APPLY", True, (255, 255, 255))
        apply_text_rect = apply_text.get_rect(center=apply_rect.center)
        screen.blit(apply_text, apply_text_rect)
        
        # Reset button với hiệu ứng đẹp hơn
        reset_rect = pygame.Rect(self.dialog_x + 160, y_start, 90, 35)
        reset_surface = pygame.Surface((90, 35), pygame.SRCALPHA)
        
        # Gradient background
        for y in range(35):
            color_intensity = int(50 + (y / 35) * 100)
            pygame.draw.line(reset_surface, (color_intensity, 0, 0), (0, y), (90, y))
        
        pygame.draw.rect(reset_surface, (200, 0, 0, 200), (0, 0, 90, 35), border_radius=8)
        pygame.draw.rect(reset_surface, (255, 100, 100, 255), (0, 0, 90, 35), 2, border_radius=8)
        screen.blit(reset_surface, (self.dialog_x + 160, y_start))
        
        reset_text = font.render("↻ RESET", True, (255, 255, 255))
        reset_text_rect = reset_text.get_rect(center=reset_rect.center)
        screen.blit(reset_text, reset_text_rect)
    
    def _draw_additional_controls(self, screen):
        """Vẽ additional controls - gameplay và advanced settings"""
        font = pygame.font.Font(None, 18)
        y_start = self.dialog_y + 280
        
        # Section title
        title_font = pygame.font.Font(None, 20)
        title_text = title_font.render("🎮 ADDITIONAL SETTINGS", True, (255, 200, 100))
        screen.blit(title_text, (self.dialog_x + 30, y_start - 5))
        
        # Show FPS checkbox
        fps_rect = pygame.Rect(self.dialog_x + 50, y_start + 20, 18, 18)
        if self.show_fps:
            pygame.draw.rect(screen, (0, 255, 100), fps_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), fps_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (fps_rect.x + 3, fps_rect.y + 9), 
                           (fps_rect.x + 8, fps_rect.y + 14), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (fps_rect.x + 8, fps_rect.y + 14), 
                           (fps_rect.x + 15, fps_rect.y + 7), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), fps_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), fps_rect, 2, border_radius=3)
        
        fps_text = font.render("Show FPS", True, (200, 200, 200))
        screen.blit(fps_text, (self.dialog_x + 75, y_start + 22))
        
        # Few Pellets Mode checkbox
        few_pellets_rect = pygame.Rect(self.dialog_x + 50, y_start + 50, 18, 18)
        if self.few_pellets_mode:
            pygame.draw.rect(screen, (0, 255, 100), few_pellets_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), few_pellets_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (few_pellets_rect.x + 3, few_pellets_rect.y + 9), 
                           (few_pellets_rect.x + 8, few_pellets_rect.y + 14), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (few_pellets_rect.x + 8, few_pellets_rect.y + 14), 
                           (few_pellets_rect.x + 15, few_pellets_rect.y + 7), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), few_pellets_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), few_pellets_rect, 2, border_radius=3)
        
        few_pellets_text = font.render("Few Pellets Mode", True, (200, 200, 200))
        screen.blit(few_pellets_text, (self.dialog_x + 75, y_start + 52))
        
        # Few Pellets Count slider
        if self.few_pellets_mode:
            slider_rect = pygame.Rect(self.dialog_x + 50, y_start + 75, 200, 20)
            pygame.draw.rect(screen, (40, 40, 60), slider_rect, border_radius=10)
            pygame.draw.rect(screen, (100, 100, 150), slider_rect, 2, border_radius=10)
            
            # Slider handle
            handle_x = self.dialog_x + 50 + int((self.few_pellets_count - 5) / 95 * 200)
            handle_rect = pygame.Rect(handle_x - 8, y_start + 75, 16, 20)
            pygame.draw.rect(screen, (0, 200, 255), handle_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), handle_rect, 2, border_radius=8)
            
            # Count label
            count_text = font.render(f"Count: {int(self.few_pellets_count)}", True, (200, 200, 200))
            screen.blit(count_text, (self.dialog_x + 260, y_start + 78))
        
        # Animations checkbox
        anim_rect = pygame.Rect(self.dialog_x + 180, y_start + 20, 18, 18)
        if self.animations_enabled:
            pygame.draw.rect(screen, (0, 255, 100), anim_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), anim_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (anim_rect.x + 3, anim_rect.y + 9), 
                           (anim_rect.x + 8, anim_rect.y + 14), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (anim_rect.x + 8, anim_rect.y + 14), 
                           (anim_rect.x + 15, anim_rect.y + 7), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), anim_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), anim_rect, 2, border_radius=3)
        
        anim_text = font.render("Animations", True, (200, 200, 200))
        screen.blit(anim_text, (self.dialog_x + 205, y_start + 22))
        
        # Particle Effects checkbox
        particle_rect = pygame.Rect(self.dialog_x + 320, y_start + 20, 18, 18)
        if self.particle_effects:
            pygame.draw.rect(screen, (0, 255, 100), particle_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), particle_rect, 2, border_radius=3)
            # Checkmark
            pygame.draw.line(screen, (255, 255, 255), 
                           (particle_rect.x + 3, particle_rect.y + 9), 
                           (particle_rect.x + 8, particle_rect.y + 14), 3)
            pygame.draw.line(screen, (255, 255, 255), 
                           (particle_rect.x + 8, particle_rect.y + 14), 
                           (particle_rect.x + 15, particle_rect.y + 7), 3)
        else:
            pygame.draw.rect(screen, (60, 60, 80), particle_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 120), particle_rect, 2, border_radius=3)
        
        particle_text = font.render("Particles", True, (200, 200, 200))
        screen.blit(particle_text, (self.dialog_x + 345, y_start + 22))
        
        # AI Speed slider
        ai_speed_y = y_start + 55
        ai_speed_label = font.render("AI Speed:", True, (255, 255, 255))
        screen.blit(ai_speed_label, (self.dialog_x + 50, ai_speed_y))
        
        # AI Speed slider với hiệu ứng đẹp
        slider_bg = pygame.Rect(self.dialog_x + 130, ai_speed_y + 5, 150, 15)
        slider_fill_width = int(150 * (self.ai_speed / 3.0))
        
        # Background slider với shadow
        shadow_rect = pygame.Rect(self.dialog_x + 131, ai_speed_y + 6, 150, 15)
        pygame.draw.rect(screen, (20, 20, 30), shadow_rect, border_radius=7)
        pygame.draw.rect(screen, (50, 50, 70), slider_bg, border_radius=7)
        
        # Fill slider với gradient
        if slider_fill_width > 0:
            for x in range(slider_fill_width):
                color_intensity = int(80 + (x / 150) * 175)
                pygame.draw.line(screen, (255, color_intensity, 0), 
                               (self.dialog_x + 130 + x, ai_speed_y + 5), 
                               (self.dialog_x + 130 + x, ai_speed_y + 20))
        
        # Slider handle
        handle_x = self.dialog_x + 130 + slider_fill_width - 6
        handle_rect = pygame.Rect(handle_x, ai_speed_y + 3, 12, 19)
        pygame.draw.rect(screen, (255, 200, 100), handle_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 150), handle_rect, 2, border_radius=6)
        
        # AI Speed value
        ai_value_text = font.render(f"{self.ai_speed:.1f}x", True, (255, 200, 100))
        screen.blit(ai_value_text, (self.dialog_x + 290, ai_speed_y))
    
