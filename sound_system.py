# =============================================================================
# SOUND_SYSTEM.PY - HỆ THỐNG ÂM THANH CHO GAME PAC-MAN (ENHANCED)
# =============================================================================
# File này chứa SoundSystem - quản lý tất cả âm thanh trong game
# Bao gồm nhạc nền, hiệu ứng âm thanh, và âm thanh UI
# 
# Enhanced Features:
# - Sound caching và lazy loading
# - Memory management cho large sounds
# - Advanced procedural sound generation
# - Dynamic volume mixing
# - Performance optimization

import pygame
import numpy as np
import math
import threading
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SilentSoundSystem:
    """Fallback sound system used when pygame.mixer fails to initialize."""

    def __init__(self, app):
        self.app = app
        self.enabled = False
        self.music_playing = False
        logger.warning("Sound disabled. Using silent sound system fallback.")

    # ------------------------------------------------------------------
    # API compatibility helpers – these methods intentionally do nothing
    # so that the rest of the application can call them safely even when
    # audio support is unavailable.
    # ------------------------------------------------------------------
    def play_sound(self, *_args, **_kwargs):
        return None

    def play_music(self, *_args, **_kwargs):
        self.music_playing = False
        return None

    def stop_music(self):
        self.music_playing = False

    def update_volume(self):
        return None

    def apply_initial_settings(self):
        return None

    def cleanup(self):
        return None

class SoundType(Enum):
    """Enum cho các loại âm thanh"""
    SFX = "sfx"
    MUSIC = "music"
    UI = "ui"
    AMBIENT = "ambient"

@dataclass
class SoundConfig:
    """Configuration cho sound generation"""
    duration: float
    base_frequency: float
    secondary_frequency: Optional[float] = None
    envelope_attack: float = 0.1
    envelope_decay: float = 0.1
    envelope_sustain: float = 0.7
    envelope_release: float = 0.2
    sound_type: SoundType = SoundType.SFX
    cache_priority: int = 1  # 1=low, 5=high

class SoundSystem:
    """
    Enhanced SoundSystem - Hệ thống quản lý âm thanh chuyên nghiệp
    
    Features:
    - Procedural sound generation with advanced algorithms
    - Intelligent caching system with memory management
    - Dynamic volume mixing and real-time effects
    - Multi-threaded sound processing
    - Performance optimized for large soundscapes
    - Lazy loading and unloading of unused sounds
    """
    
    def __init__(self, app):
        self.app = app
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.sound_configs: Dict[str, SoundConfig] = {}
        self.sound_cache_usage: Dict[str, float] = {}  # Last used timestamp
        self.music_playing = False
        self.current_music = None
        
        # Enhanced audio configuration
        self.sample_rate = 44100  # Higher quality
        self.channels = 2
        self.bit_depth = 16
        self.buffer_size = 1024
        
        # Advanced channel management
        self.music_channel = None
        self.sfx_channels: List[pygame.mixer.Channel] = []
        self.ui_channel = pygame.mixer.Channel(0)
        self.ambient_channel = pygame.mixer.Channel(1)
        
        # Performance settings
        self.max_cached_sounds = 50
        self.cache_cleanup_interval = 30.0  # seconds
        self.lazy_loading = True
        
        # Threading for background operations
        self.background_thread = None
        self.shutdown_event = threading.Event()
        
        # Initialize sound configurations
        self._define_sound_configs()
        
        # Initialize channels pool
        self._init_channel_pool()
        
        # Create essential sounds immediately
        self._create_essential_sounds()
        
        # Start background thread for cache management
        if self.lazy_loading:
            self._start_background_thread()
        
        # Apply initial settings
        self.apply_initial_settings()
        
        logger.info("Enhanced SoundSystem initialized successfully")
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
    def _define_sound_configs(self):
        """Define configurations for all sounds"""
        configs = {
            # Game sounds - high priority
            'pellet': SoundConfig(0.1, 880, cache_priority=5, sound_type=SoundType.SFX),
            'power_pellet': SoundConfig(0.3, 440, 220, cache_priority=5, sound_type=SoundType.SFX),
            'fruit': SoundConfig(0.2, 1000, 1500, cache_priority=4, sound_type=SoundType.SFX),
            'ghost_eaten': SoundConfig(0.5, 800, cache_priority=4, sound_type=SoundType.SFX),
            'game_over': SoundConfig(1.0, 400, cache_priority=3, sound_type=SoundType.SFX),
            'level_complete': SoundConfig(0.8, 523, cache_priority=3, sound_type=SoundType.SFX),
            
            # UI sounds - medium priority
            'button_click': SoundConfig(0.05, 1000, cache_priority=3, sound_type=SoundType.UI),
            'button_hover': SoundConfig(0.03, 800, cache_priority=2, sound_type=SoundType.UI),
            
            # Ghost sounds - medium priority
            'ghost_chase': SoundConfig(0.5, 200, cache_priority=2, sound_type=SoundType.AMBIENT),
            'ghost_scared': SoundConfig(0.3, 300, cache_priority=2, sound_type=SoundType.AMBIENT),
            
            # Music - low priority (generated on demand)
            'background_music': SoundConfig(10.0, 523, cache_priority=1, sound_type=SoundType.MUSIC),
        }
        
        self.sound_configs.update(configs)
    
    def _init_channel_pool(self):
        """Initialize pool of channels for different sound types"""
        # Create multiple SFX channels for overlapping sounds
        for i in range(2, 8):  # Channels 2-7 for SFX
            try:
                channel = pygame.mixer.Channel(i)
                self.sfx_channels.append(channel)
            except pygame.error:
                break  # No more channels available
        
        logger.info(f"Initialized {len(self.sfx_channels)} SFX channels")
    
    def _create_essential_sounds(self):
        """Create essential sounds immediately (non-lazy)"""
        essential_sounds = ['pellet', 'power_pellet', 'button_click', 'button_hover']
        
        logger.info("Creating essential sounds...")
        for sound_name in essential_sounds:
            if sound_name in self.sound_configs:
                self._generate_sound(sound_name)
        
        logger.info(f"Created {len(essential_sounds)} essential sounds")
    
    def _start_background_thread(self):
        """Start background thread for cache management"""
        self.background_thread = threading.Thread(
            target=self._background_cache_manager,
            daemon=True,
            name="SoundCacheManager"
        )
        self.background_thread.start()
        logger.info("Background cache manager started")
    
    def _background_cache_manager(self):
        """Background thread for managing sound cache"""
        while not self.shutdown_event.is_set():
            try:
                # Clean up unused sounds
                self._cleanup_unused_sounds()
                
                # Wait for next cleanup cycle
                self.shutdown_event.wait(self.cache_cleanup_interval)
                
            except Exception as e:
                logger.error(f"Error in background cache manager: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _cleanup_unused_sounds(self):
        """Remove unused sounds from cache to free memory"""
        if len(self.sounds) <= self.max_cached_sounds:
            return
        
        current_time = time.time()
        sounds_to_remove = []
        
        # Find sounds that haven't been used recently
        for sound_name, last_used in self.sound_cache_usage.items():
            if current_time - last_used > 60.0:  # 1 minute
                config = self.sound_configs.get(sound_name)
                if config and config.cache_priority <= 2:  # Only remove low priority sounds
                    sounds_to_remove.append(sound_name)
        
        # Remove oldest sounds first
        sounds_to_remove.sort(key=lambda x: self.sound_cache_usage[x])
        
        removed_count = 0
        for sound_name in sounds_to_remove:
            if len(self.sounds) <= self.max_cached_sounds // 2:
                break
            
            if sound_name in self.sounds:
                del self.sounds[sound_name]
                del self.sound_cache_usage[sound_name]
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} unused sounds from cache")
    
    def _get_or_create_sound(self, sound_name: str) -> Optional[pygame.mixer.Sound]:
        """Get sound from cache or create it if not exists"""
        # Update usage timestamp
        self.sound_cache_usage[sound_name] = time.time()
        
        # Return from cache if exists
        if sound_name in self.sounds:
            return self.sounds[sound_name]
        
        # Generate new sound
        return self._generate_sound(sound_name)
    
    def _generate_sound(self, sound_name: str) -> Optional[pygame.mixer.Sound]:
        """Generate a sound using advanced procedural algorithms"""
        if sound_name not in self.sound_configs:
            logger.warning(f"No config found for sound: {sound_name}")
            return None
        
        config = self.sound_configs[sound_name]
        
        try:
            # Use specialized generators for different sound types
            if sound_name == 'background_music':
                sound = self._generate_background_music(config)
            elif 'ghost' in sound_name:
                sound = self._generate_ghost_sound(sound_name, config)
            elif sound_name in ['pellet', 'power_pellet', 'fruit']:
                sound = self._generate_game_sound(sound_name, config)
            else:
                sound = self._generate_basic_sound(config)
            
            if sound:
                self.sounds[sound_name] = sound
                self.sound_cache_usage[sound_name] = time.time()
                logger.debug(f"Generated sound: {sound_name}")
            
            return sound
            
        except Exception as e:
            logger.error(f"Error generating sound {sound_name}: {e}")
            return None
    
    def _generate_basic_sound(self, config: SoundConfig) -> pygame.mixer.Sound:
        """Generate basic sound with ADSR envelope"""
        frames = int(config.duration * self.sample_rate)
        t = np.linspace(0, config.duration, frames, False)
        
        # Generate wave
        wave = np.sin(2 * np.pi * config.base_frequency * t)
        
        if config.secondary_frequency:
            wave += 0.3 * np.sin(2 * np.pi * config.secondary_frequency * t)
        
        # Apply ADSR envelope
        envelope = self._create_adsr_envelope(frames, config)
        wave *= envelope
        
        # Convert to stereo and pygame format
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _generate_game_sound(self, sound_name: str, config: SoundConfig) -> pygame.mixer.Sound:
        """Generate specialized game sounds with unique characteristics"""
        frames = int(config.duration * self.sample_rate)
        t = np.linspace(0, config.duration, frames, False)
        
        if sound_name == 'pellet':
            # Classic Pac-Man "waka" sound
            freq_mod = 1 + 0.1 * np.sin(2 * np.pi * 10 * t)
            wave = np.sin(2 * np.pi * config.base_frequency * freq_mod * t)
            envelope = np.exp(-t * 8) * (1 - np.exp(-t * 20))
            
        elif sound_name == 'power_pellet':
            # Deeper, more resonant sound
            wave1 = np.sin(2 * np.pi * config.base_frequency * t)
            wave2 = np.sin(2 * np.pi * config.secondary_frequency * t)
            wave = wave1 * 0.7 + wave2 * 0.3
            envelope = np.exp(-t * 3) * (1 - np.exp(-t * 10))
            
        elif sound_name == 'fruit':
            # Bright, cheerful sound with harmonics
            harmonics = [1, 1.5, 2, 2.5, 3]
            wave = np.zeros_like(t)
            for i, harmonic in enumerate(harmonics):
                amplitude = 0.3 / (i + 1)
                wave += amplitude * np.sin(2 * np.pi * config.base_frequency * harmonic * t)
            envelope = np.exp(-t * 5) * (1 - np.exp(-t * 15))
        
        else:
            # Fallback to basic sound
            return self._generate_basic_sound(config)
        
        wave *= envelope
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _generate_ghost_sound(self, sound_name: str, config: SoundConfig) -> pygame.mixer.Sound:
        """Generate atmospheric ghost sounds"""
        frames = int(config.duration * self.sample_rate)
        t = np.linspace(0, config.duration, frames, False)
        
        if 'chase' in sound_name:
            # Menacing, pulsating sound
            freq_mod = config.base_frequency + 50 * np.sin(2 * np.pi * 3 * t)
            wave = np.sin(2 * np.pi * freq_mod * t)
            # Add some noise for texture
            noise = np.random.normal(0, 0.1, frames)
            wave = 0.8 * wave + 0.2 * noise
            
        elif 'scared' in sound_name:
            # Trembling, fearful sound
            freq_mod = config.base_frequency + 100 * np.sin(2 * np.pi * 8 * t)
            wave = np.sin(2 * np.pi * freq_mod * t)
            # Add tremolo effect
            tremolo = 1 + 0.3 * np.sin(2 * np.pi * 12 * t)
            wave *= tremolo
        
        else:
            return self._generate_basic_sound(config)
        
        envelope = np.exp(-t * 2)
        wave *= envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _generate_background_music(self, config: SoundConfig) -> pygame.mixer.Sound:
        """Generate complex background music with multiple layers"""
        frames = int(config.duration * self.sample_rate)
        t = np.linspace(0, config.duration, frames, False)
        
        # Main melody line
        melody_notes = [523, 659, 784, 659, 523, 440, 523, 698, 784, 880]  # Extended melody
        melody_wave = np.zeros(frames)
        
        note_duration = config.duration / len(melody_notes)
        for i, freq in enumerate(melody_notes):
            start_idx = int(i * frames / len(melody_notes))
            end_idx = int((i + 1) * frames / len(melody_notes))
            note_t = t[start_idx:end_idx] - t[start_idx]
            
            # Create note with vibrato
            vibrato = 1 + 0.02 * np.sin(2 * np.pi * 5 * note_t)
            note_wave = np.sin(2 * np.pi * freq * vibrato * note_t)
            
            # Note envelope
            note_envelope = np.exp(-note_t * 1) * (1 - np.exp(-note_t * 5))
            melody_wave[start_idx:end_idx] = note_wave * note_envelope * 0.4
        
        # Bass line (one octave lower)
        bass_notes = [freq // 2 for freq in melody_notes]
        bass_wave = np.zeros(frames)
        
        for i, freq in enumerate(bass_notes):
            start_idx = int(i * frames / len(bass_notes))
            end_idx = int((i + 1) * frames / len(bass_notes))
            note_t = t[start_idx:end_idx] - t[start_idx]
            
            note_wave = np.sin(2 * np.pi * freq * note_t)
            note_envelope = np.exp(-note_t * 0.5) * (1 - np.exp(-note_t * 3))
            bass_wave[start_idx:end_idx] = note_wave * note_envelope * 0.2
        
        # Combine layers
        final_wave = melody_wave + bass_wave
        
        # Add subtle reverb effect
        reverb_delay = int(0.1 * self.sample_rate)  # 100ms delay
        if reverb_delay < len(final_wave):
            reverb_wave = np.zeros_like(final_wave)
            reverb_wave[reverb_delay:] = final_wave[:-reverb_delay] * 0.3
            final_wave += reverb_wave
        
        stereo_wave = np.array([final_wave, final_wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_adsr_envelope(self, frames: int, config: SoundConfig) -> np.ndarray:
        """Create ADSR (Attack, Decay, Sustain, Release) envelope"""
        attack_frames = int(frames * config.envelope_attack)
        decay_frames = int(frames * config.envelope_decay)
        release_frames = int(frames * config.envelope_release)
        sustain_frames = frames - attack_frames - decay_frames - release_frames
        
        # Ensure we have valid frame counts
        if sustain_frames < 0:
            sustain_frames = 0
            # Adjust other phases proportionally
            total_other = attack_frames + decay_frames + release_frames
            if total_other > frames:
                scale = frames / total_other
                attack_frames = int(attack_frames * scale)
                decay_frames = int(decay_frames * scale)
                release_frames = frames - attack_frames - decay_frames
        
        envelope = np.zeros(frames)
        
        # Attack phase
        if attack_frames > 0:
            envelope[:attack_frames] = np.linspace(0, 1, attack_frames)
        
        # Decay phase
        if decay_frames > 0:
            start_idx = attack_frames
            end_idx = attack_frames + decay_frames
            envelope[start_idx:end_idx] = np.linspace(1, config.envelope_sustain, decay_frames)
        
        # Sustain phase
        if sustain_frames > 0:
            start_idx = attack_frames + decay_frames
            end_idx = start_idx + sustain_frames
            envelope[start_idx:end_idx] = config.envelope_sustain
        
        # Release phase
        if release_frames > 0:
            start_idx = frames - release_frames
            envelope[start_idx:] = np.linspace(config.envelope_sustain, 0, release_frames)
        
        return envelope
    
    # Legacy method for backward compatibility
    def _create_sounds(self):
        """Legacy method - now handled by lazy loading"""
        logger.info("Using enhanced sound system with lazy loading")
        
        # Âm thanh ăn pellet
        self.sounds['pellet'] = self._create_pellet_sound()
        
        # Âm thanh ăn power pellet
        self.sounds['power_pellet'] = self._create_power_pellet_sound()
        
        # Âm thanh ăn fruit
        self.sounds['fruit'] = self._create_fruit_sound()
        
        # Âm thanh ghost bị ăn
        self.sounds['ghost_eaten'] = self._create_ghost_eaten_sound()
        
        # Âm thanh game over
        self.sounds['game_over'] = self._create_game_over_sound()
        
        # Âm thanh level complete
        self.sounds['level_complete'] = self._create_level_complete_sound()
        
        # Âm thanh UI
        self.sounds['button_click'] = self._create_button_click_sound()
        self.sounds['button_hover'] = self._create_button_hover_sound()
        
        # Âm thanh ghost
        self.sounds['ghost_chase'] = self._create_ghost_chase_sound()
        self.sounds['ghost_scared'] = self._create_ghost_scared_sound()
        
        # Nhạc nền
        self.sounds['background_music'] = self.create_background_music()
        
        print("All sounds created successfully!")
    
    def _create_pellet_sound(self):
        """Tạo âm thanh khi ăn pellet"""
        duration = 0.1
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        # Tạo âm thanh "waka" đặc trưng của Pac-Man
        t = np.linspace(0, duration, frames, False)
        
        # Tần số chính
        freq1 = 800
        freq2 = 1200
        
        # Tạo wave với envelope
        wave1 = np.sin(2 * np.pi * freq1 * t)
        wave2 = np.sin(2 * np.pi * freq2 * t)
        
        # Envelope để tạo âm thanh "waka"
        envelope = np.exp(-t * 8) * (1 - np.exp(-t * 20))
        
        # Kết hợp các wave
        wave = (wave1 * 0.6 + wave2 * 0.4) * envelope
        
        # Tạo stereo
        stereo_wave = np.array([wave, wave]).T
        
        # Chuyển đổi sang định dạng pygame
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_power_pellet_sound(self):
        """Tạo âm thanh khi ăn power pellet"""
        duration = 0.3
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Tần số thấp hơn và dài hơn
        freq1 = 400
        freq2 = 600
        
        wave1 = np.sin(2 * np.pi * freq1 * t)
        wave2 = np.sin(2 * np.pi * freq2 * t)
        
        # Envelope dài hơn
        envelope = np.exp(-t * 3) * (1 - np.exp(-t * 10))
        
        wave = (wave1 * 0.7 + wave2 * 0.3) * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_fruit_sound(self):
        """Tạo âm thanh khi ăn fruit"""
        duration = 0.2
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Tần số cao và vui vẻ
        freq1 = 1000
        freq2 = 1500
        freq3 = 2000
        
        wave1 = np.sin(2 * np.pi * freq1 * t)
        wave2 = np.sin(2 * np.pi * freq2 * t)
        wave3 = np.sin(2 * np.pi * freq3 * t)
        
        envelope = np.exp(-t * 5) * (1 - np.exp(-t * 15))
        
        wave = (wave1 * 0.4 + wave2 * 0.4 + wave3 * 0.2) * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_ghost_eaten_sound(self):
        """Tạo âm thanh khi ăn ghost"""
        duration = 0.5
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Tần số giảm dần
        freq = 800 * np.exp(-t * 2)
        
        wave = np.sin(2 * np.pi * freq * t)
        
        # Envelope đặc biệt
        envelope = np.exp(-t * 1.5) * (1 - np.exp(-t * 5))
        
        wave = wave * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_game_over_sound(self):
        """Tạo âm thanh game over"""
        duration = 1.0
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Tần số giảm dần tạo cảm giác buồn
        freq = 400 * np.exp(-t * 1.5)
        
        wave = np.sin(2 * np.pi * freq * t)
        
        # Envelope dài
        envelope = np.exp(-t * 0.8)
        
        wave = wave * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_level_complete_sound(self):
        """Tạo âm thanh hoàn thành level"""
        duration = 0.8
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Melody vui vẻ
        melody = [523, 659, 784, 1047]  # C, E, G, C
        wave = np.zeros(frames)
        
        for i, freq in enumerate(melody):
            start = int(i * frames / len(melody))
            end = int((i + 1) * frames / len(melody))
            note_t = t[start:end] - t[start]
            note_wave = np.sin(2 * np.pi * freq * note_t)
            envelope = np.exp(-note_t * 3) * (1 - np.exp(-note_t * 10))
            wave[start:end] = note_wave * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_button_click_sound(self):
        """Tạo âm thanh click button"""
        duration = 0.05
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Click sound
        freq = 1000
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-t * 20)
        
        wave = wave * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_button_hover_sound(self):
        """Tạo âm thanh hover button"""
        duration = 0.03
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Hover sound
        freq = 800
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-t * 15)
        
        wave = wave * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_ghost_chase_sound(self):
        """Tạo âm thanh ghost đuổi"""
        duration = 0.5
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Âm thanh đe dọa
        freq = 200 + 100 * np.sin(2 * np.pi * 2 * t)
        wave = np.sin(2 * np.pi * freq * t)
        
        envelope = np.exp(-t * 2)
        wave = wave * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def _create_ghost_scared_sound(self):
        """Tạo âm thanh ghost sợ hãi"""
        duration = 0.3
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Âm thanh run sợ
        freq = 300 + 200 * np.sin(2 * np.pi * 5 * t)
        wave = np.sin(2 * np.pi * freq * t)
        
        envelope = np.exp(-t * 3)
        wave = wave * envelope
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def play_sound(self, sound_name: str, volume: float = 1.0):
        """
        Play sound with intelligent channel management
        Args:
            sound_name: Name of sound to play
            volume: Volume multiplier (0.0 to 1.0)
        """
        sound = self._get_or_create_sound(sound_name)
        if not sound:
            logger.warning(f"Could not create sound: {sound_name}")
            return
        
        # Get sound type for appropriate channel selection
        config = self.sound_configs.get(sound_name)
        sound_type = config.sound_type if config else SoundType.SFX
        
        # Calculate final volume based on settings
        master_volume = self.app.config.get('master_volume', 0.7)
        
        if sound_type == SoundType.UI:
            type_volume = self.app.config.get('sfx_volume', 0.8)
            channel = self.ui_channel
        elif sound_type == SoundType.AMBIENT:
            type_volume = self.app.config.get('sfx_volume', 0.8) * 0.5  # Ambient sounds quieter
            channel = self.ambient_channel
        else:  # SFX
            type_volume = self.app.config.get('sfx_volume', 0.8)
            channel = self._get_available_sfx_channel()
        
        # Check if sound effects are enabled
        if not self.app.config.get('sfx_enabled', True):
            return
        
        final_volume = master_volume * type_volume * volume
        
        # Play sound on appropriate channel
        if channel and not channel.get_busy():
            channel.set_volume(final_volume)
            channel.play(sound)
        else:
            # Fallback to any available channel
            sound.set_volume(final_volume)
            sound.play()
    
    def _get_available_sfx_channel(self) -> Optional[pygame.mixer.Channel]:
        """Get an available SFX channel"""
        for channel in self.sfx_channels:
            if not channel.get_busy():
                return channel
        # If all busy, return the first one (will interrupt)
        return self.sfx_channels[0] if self.sfx_channels else None
    
    def play_music(self, music_name: str, loop: int = -1):
        """
        Play background music with enhanced features
        Args:
            music_name: Name of music to play
            loop: Number of loops (-1 = infinite)
        """
        # Check if music is enabled
        if not self.app.config.get('music_enabled', True) or not self.app.config.get('background_music_enabled', True):
            logger.info("Music is disabled in settings")
            return
        
        # Stop current music if playing
        if self.music_playing:
            self.stop_music()
        
        # Get or create music
        sound = self._get_or_create_sound(music_name)
        if not sound:
            logger.warning(f"Could not create music: {music_name}")
            return
        
        # Setup music channel
        if self.music_channel is None:
            try:
                self.music_channel = pygame.mixer.Channel(7)  # Use highest channel for music
            except pygame.error:
                logger.error("Could not allocate music channel")
                return
        
        # Calculate volume
        master_volume = self.app.config.get('master_volume', 0.7)
        music_volume = self.app.config.get('music_volume', 0.5)
        final_volume = master_volume * music_volume
        
        # Play music
        self.music_channel.set_volume(final_volume)
        self.music_channel.play(sound, loops=loop)
        self.music_playing = True
        self.current_music = music_name
        
        logger.info(f"Playing music: {music_name} (volume: {final_volume:.2f})")
    
    def stop_music(self):
        """Dừng nhạc nền"""
        if self.music_channel and self.music_channel.get_busy():
            self.music_channel.stop()
        self.music_playing = False
        self.current_music = None
    
    def update_volume(self):
        """Cập nhật volume theo settings"""
        if self.music_playing and self.music_channel:
            master_volume = self.app.settings.get('master_volume', 0.7)
            music_volume = self.app.settings.get('music_volume', 0.5)
            final_volume = master_volume * music_volume
            self.music_channel.set_volume(final_volume)
    
    def create_background_music(self):
        """Tạo nhạc nền cho game"""
        duration = 10.0  # 10 giây, sẽ loop
        sample_rate = self.sample_rate
        frames = int(duration * sample_rate)
        
        t = np.linspace(0, duration, frames, False)
        
        # Tạo melody đơn giản
        melody = [523, 659, 784, 659, 523, 440, 523]  # C-E-G-E-C-A-C
        wave = np.zeros(frames)
        
        for i, freq in enumerate(melody):
            start = int(i * frames / len(melody))
            end = int((i + 1) * frames / len(melody))
            note_t = t[start:end] - t[start]
            note_wave = np.sin(2 * np.pi * freq * note_t)
            envelope = np.exp(-note_t * 0.5) * (1 - np.exp(-note_t * 2))
            wave[start:end] = note_wave * envelope * 0.3
        
        stereo_wave = np.array([wave, wave]).T
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)
    
    def apply_initial_settings(self):
        """Áp dụng cài đặt âm thanh ban đầu từ app.settings"""
        master_volume = self.app.settings.get('master_volume', 0.7)
        music_volume = self.app.settings.get('music_volume', 0.5)
        sfx_volume = self.app.settings.get('sfx_volume', 0.8)
        music_enabled = self.app.settings.get('music_enabled', True)
        sfx_enabled = self.app.settings.get('sfx_enabled', True)
        background_music_enabled = self.app.settings.get('background_music_enabled', True)

        final_music_volume = master_volume * music_volume if music_enabled and background_music_enabled else 0
        final_sfx_volume = master_volume * sfx_volume if sfx_enabled else 0

        if self.music_channel:
            self.music_channel.set_volume(final_music_volume)
        
        # Update all SFX channels
        for channel in self.sfx_channels:
            channel.set_volume(final_sfx_volume)
        
        self.ui_channel.set_volume(final_sfx_volume)
        self.ambient_channel.set_volume(final_sfx_volume * 0.5)  # Ambient quieter
    
    def cleanup(self):
        """Cleanup resources and stop background thread"""
        logger.info("Cleaning up SoundSystem...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Stop all sounds
        self.stop_music()
        for channel in self.sfx_channels:
            if channel.get_busy():
                channel.stop()
        
        if self.ui_channel.get_busy():
            self.ui_channel.stop()
        if self.ambient_channel.get_busy():
            self.ambient_channel.stop()
        
        # Wait for background thread to finish
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=2.0)
        
        # Clear caches
        self.sounds.clear()
        self.sound_cache_usage.clear()
        
        logger.info("SoundSystem cleanup completed")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for debugging"""
        return {
            'cached_sounds': len(self.sounds),
            'max_cache_size': self.max_cached_sounds,
            'sfx_channels': len(self.sfx_channels),
            'cache_usage_entries': len(self.sound_cache_usage)
        }
    
    def preload_sounds(self, sound_names: List[str]):
        """Preload specific sounds for better performance"""
        logger.info(f"Preloading {len(sound_names)} sounds...")
        for sound_name in sound_names:
            self._get_or_create_sound(sound_name)
        logger.info("Preloading completed")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass
