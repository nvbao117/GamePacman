# =============================================================================
# CONFIG_MANAGER.PY - HỆ THỐNG QUẢN LÝ CẤU HÌNH CHUYÊN NGHIỆP
# =============================================================================


import json
import os
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ConfigCategory(Enum):
    """Enum cho các category của config"""
    AUDIO = "audio"
    VIDEO = "video"
    GAMEPLAY = "gameplay"
    CONTROLS = "controls"
    UI = "ui"

@dataclass
class ConfigSchema:
    """Schema định nghĩa cấu trúc config và validation rules"""
    key: str
    default_value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    valid_values: Optional[List[Any]] = None
    category: ConfigCategory = ConfigCategory.GAMEPLAY
    description: str = ""
    requires_restart: bool = False

class ConfigManager:
    """
    ConfigManager - Hệ thống quản lý cấu hình chuyên nghiệp
    
    Features:
    - Persistent storage với JSON
    - Schema validation
    - Event notification khi config thay đổi
    - Categorized settings
    - Auto-backup và recovery
    - Type safety
    """
    
    def __init__(self, config_file: str = "config.json", backup_file: str = "config_backup.json"):
        self.config_file = Path(config_file)
        self.backup_file = Path(backup_file)
        self.config: Dict[str, Any] = {}
        self.listeners: Dict[str, List[Callable]] = {}
        self.schemas: Dict[str, ConfigSchema] = {}
        
        # Định nghĩa schema cho tất cả settings
        self._define_schemas()
        
        # Load config
        self._load_config()
        
    
    def _define_schemas(self):
        """Định nghĩa schema cho tất cả config keys"""
        schemas = [
            # Audio Settings
            ConfigSchema("master_volume", 0.7, 0.0, 1.0, category=ConfigCategory.AUDIO, 
                        description="Master volume for all sounds"),
            ConfigSchema("music_volume", 0.5, 0.0, 1.0, category=ConfigCategory.AUDIO,
                        description="Background music volume"),
            ConfigSchema("sfx_volume", 0.8, 0.0, 1.0, category=ConfigCategory.AUDIO,
                        description="Sound effects volume"),
            ConfigSchema("music_enabled", True, category=ConfigCategory.AUDIO,
                        description="Enable/disable music"),
            ConfigSchema("sfx_enabled", True, category=ConfigCategory.AUDIO,
                        description="Enable/disable sound effects"),
            ConfigSchema("background_music_enabled", True, category=ConfigCategory.AUDIO,
                        description="Enable/disable background music"),
            ConfigSchema("ambient_sounds_enabled", True, category=ConfigCategory.AUDIO,
                        description="Enable/disable ambient sounds"),
            
            # Video Settings
            ConfigSchema("fullscreen", True, category=ConfigCategory.VIDEO,
                        description="Fullscreen mode", requires_restart=True),
            ConfigSchema("vsync", True, category=ConfigCategory.VIDEO,
                        description="Vertical sync", requires_restart=True),
            ConfigSchema("resolution", "auto", valid_values=["auto", "1920x1080", "1366x768", "1280x720"],
                        category=ConfigCategory.VIDEO, description="Screen resolution", requires_restart=True),
            ConfigSchema("fps_limit", 60, 30, 144, category=ConfigCategory.VIDEO,
                        description="FPS limit"),
            ConfigSchema("quality", "high", valid_values=["low", "medium", "high", "ultra"],
                        category=ConfigCategory.VIDEO, description="Graphics quality"),
            
            # Gameplay Settings
            ConfigSchema("difficulty", "normal", valid_values=["easy", "normal", "hard", "expert"],
                        category=ConfigCategory.GAMEPLAY, description="Game difficulty"),
            ConfigSchema("ai_speed", 1.0, 0.1, 3.0, category=ConfigCategory.GAMEPLAY,
                        description="AI movement speed multiplier"),
            ConfigSchema("show_path", False, category=ConfigCategory.GAMEPLAY,
                        description="Show AI pathfinding visualization"),
            ConfigSchema("auto_pause", True, category=ConfigCategory.GAMEPLAY,
                        description="Auto pause when window loses focus"),
            
            # Controls Settings
            ConfigSchema("mouse_sensitivity", 1.0, 0.1, 5.0, category=ConfigCategory.CONTROLS,
                        description="Mouse sensitivity"),
            ConfigSchema("keyboard_repeat_rate", 0.1, 0.05, 0.5, category=ConfigCategory.CONTROLS,
                        description="Keyboard repeat rate"),
            
            # UI Settings
            ConfigSchema("ui_scale", 1.0, 0.5, 2.0, category=ConfigCategory.UI,
                        description="UI scale factor"),
            ConfigSchema("show_fps", False, category=ConfigCategory.UI,
                        description="Show FPS counter"),
            ConfigSchema("animations_enabled", True, category=ConfigCategory.UI,
                        description="Enable UI animations"),
            ConfigSchema("particle_effects", True, category=ConfigCategory.UI,
                        description="Enable particle effects"),
            
            # Game Mode Settings
            ConfigSchema("few_pellets_mode", False, category=ConfigCategory.GAMEPLAY,
                        description="Enable few pellets mode (only some pellets instead of all)"),
            ConfigSchema("few_pellets_count", 20, 5, 100, category=ConfigCategory.GAMEPLAY,
                        description="Number of pellets in few pellets mode"),
            
            # AI Algorithm Settings
            ConfigSchema("bfs_heuristic", "NONE", valid_values=["NONE", "MANHATTAN", "EUCLIDEAN"],
                        category=ConfigCategory.GAMEPLAY, description="Heuristic function for BFS algorithm (deprecated)"),
            ConfigSchema("algorithm_heuristic", "NONE", valid_values=["NONE", "MANHATTAN", "EUCLIDEAN"],
                        category=ConfigCategory.GAMEPLAY, description="Heuristic function for all algorithms"),
        ]
        
        for schema in schemas:
            self.schemas[schema.key] = schema
    
    def _load_config(self):
        """Load config từ file, fallback to backup nếu cần"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self._validate_and_merge_config(loaded_config)
            else:
                self._use_default_config()
        except (json.JSONDecodeError, Exception) as e:
            self._try_backup_recovery()
    
    def _try_backup_recovery(self):
        """Thử khôi phục từ backup"""
        try:
            if self.backup_file.exists():
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    backup_config = json.load(f)
                    self._validate_and_merge_config(backup_config)
                    self.save_config()  # Save as main config
            else:
                self._use_default_config()
        except Exception as e:
            self._use_default_config()
    
    def _use_default_config(self):
        """Sử dụng config mặc định"""
        self.config = {}
        for key, schema in self.schemas.items():
            self.config[key] = schema.default_value
    
    def _validate_and_merge_config(self, loaded_config: Dict[str, Any]):
        """Validate và merge config từ file với schema"""
        self.config = {}
        
        for key, schema in self.schemas.items():
            if key in loaded_config:
                value = loaded_config[key]
                if self._validate_value(key, value):
                    self.config[key] = value
                else:
                    self.config[key] = schema.default_value
            else:
                self.config[key] = schema.default_value
    
    def _validate_value(self, key: str, value: Any) -> bool:
        """Validate giá trị theo schema"""
        if key not in self.schemas:
            return False
        
        schema = self.schemas[key]
        
        # Type check
        if not isinstance(value, type(schema.default_value)):
            return False
        
        # Range check
        if schema.min_value is not None and value < schema.min_value:
            return False
        if schema.max_value is not None and value > schema.max_value:
            return False
        
        # Valid values check
        if schema.valid_values is not None and value not in schema.valid_values:
            return False
        
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị config
        Args:
            key: Config key
            default: Default value nếu key không tồn tại
        Returns:
            Config value hoặc default
        """
        if key in self.config:
            return self.config[key]
        elif key in self.schemas:
            return self.schemas[key].default_value
        else:
            return default
    
    def set(self, key: str, value: Any, notify: bool = True) -> bool:
        """
        Đặt giá trị config
        Args:
            key: Config key
            value: New value
            notify: Có notify listeners không
        Returns:
            True nếu thành công, False nếu validation fail
        """
        if not self._validate_value(key, value):
            return False
        
        old_value = self.config.get(key)
        self.config[key] = value
        
        if notify and old_value != value:
            self._notify_listeners(key, value, old_value)
        
        return True
    
    def get_category(self, category: ConfigCategory) -> Dict[str, Any]:
        """Lấy tất cả config trong một category"""
        result = {}
        for key, schema in self.schemas.items():
            if schema.category == category:
                result[key] = self.get(key)
        return result
    
    def add_listener(self, key: str, callback: Callable[[str, Any, Any], None]):
        """
        Thêm listener cho config key
        Args:
            key: Config key để listen
            callback: Function callback (key, new_value, old_value)
        """
        if key not in self.listeners:
            self.listeners[key] = []
        self.listeners[key].append(callback)
    
    def remove_listener(self, key: str, callback: Callable):
        """Remove listener"""
        if key in self.listeners:
            try:
                self.listeners[key].remove(callback)
            except ValueError:
                pass
    
    def _notify_listeners(self, key: str, new_value: Any, old_value: Any):
        """Notify tất cả listeners của key"""
        if key in self.listeners:
            for callback in self.listeners[key]:
                try:
                    callback(key, new_value, old_value)
                except Exception as e:
                    pass

    def save_config(self):
        """Lưu config ra file"""
        try:
            # Backup current config
            if self.config_file.exists():
                import shutil
                shutil.copy2(self.config_file, self.backup_file)
            
            # Save new config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            pass

    def reset_to_defaults(self, category: Optional[ConfigCategory] = None):
        """
        Reset config về mặc định
        Args:
            category: Category để reset, None = reset all
        """
        if category is None:
            # Reset all
            for key, schema in self.schemas.items():
                self.set(key, schema.default_value, notify=False)
        else:
            # Reset specific category
            for key, schema in self.schemas.items():
                if schema.category == category:
                    self.set(key, schema.default_value, notify=False)
        
        # Notify all listeners after batch reset
        for key in self.config:
            self._notify_listeners(key, self.config[key], None)
        
    
    def get_schema(self, key: str) -> Optional[ConfigSchema]:
        """Lấy schema của config key"""
        return self.schemas.get(key)
    
    def get_all_schemas(self) -> Dict[str, ConfigSchema]:
        """Lấy tất cả schemas"""
        return self.schemas.copy()
    
    def export_config(self, file_path: str):
        """Export config ra file khác"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def import_config(self, file_path: str):
        """Import config từ file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                self._validate_and_merge_config(imported_config)
        except Exception as e:
            pass
        
    def get_requires_restart_keys(self) -> List[str]:
        """Lấy danh sách keys cần restart khi thay đổi"""
        return [key for key, schema in self.schemas.items() if schema.requires_restart]
    
    def __del__(self):
        """Destructor - auto save config"""
        try:
            self.save_config()
        except:
            pass
