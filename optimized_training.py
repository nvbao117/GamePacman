#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPTIMIZED Q-LEARNING TRAINING SCRIPT FOR PACMAN
===============================================

Script training tối ưu với:
- Hệ thống reward cân bằng và hiệu quả
- State representation chi tiết hơn
- Tham số Q-learning được tối ưu
- Adaptive learning rate
- Performance monitoring và visualization

Author: AI Assistant
Date: 2024
"""
import os
import sys

# CRITICAL: Set environment variables BEFORE importing pygame
# This must be done FIRST for headless mode to work
if '--headless' in sys.argv or os.environ.get('SDL_VIDEODRIVER') == 'dummy':
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import time
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless
import matplotlib.pyplot as plt
from datetime import datetime
from collections import deque
from engine.game import Game
from constants import *
from simple_reward_plot import SimpleRewardPlotter

class OptimizedQLearningTrainer:
    def __init__(self, 
                 max_episodes=3000,
                 save_interval=50,
                 max_steps_per_episode=2500,
                 render=True,
                 few_pellets_mode=False,
                 few_pellets_count=30,
                 adaptive_learning=True,
                 performance_window=100):
        """
        Optimized Q-Learning Trainer với các cải tiến:
        - Adaptive learning rate
        - Performance monitoring
        - Better reward system
        - Improved state representation
        """
        self.max_episodes = max_episodes
        self.save_interval = save_interval
        self.max_steps_per_episode = max_steps_per_episode
        self.render = render
        self.few_pellets_mode = few_pellets_mode
        self.few_pellets_count = few_pellets_count
        self.adaptive_learning = adaptive_learning
        self.performance_window = performance_window

        # Performance tracking
        self.episode_rewards = []
        self.episode_steps = []
        self.episode_scores = []
        self.episode_epsilons = []
        self.episode_deaths = []
        self.episode_wins = []
        self.episode_timeouts = []
        
        # Adaptive learning tracking
        self.recent_performance = deque(maxlen=performance_window)
        self.learning_rate_history = []
        self.convergence_threshold = 0.1
        
        # Best performance tracking
        self.best_score = 0
        self.best_reward = float('-inf')
        self.best_episode = 0
        
        # Statistics
        self.total_wins = 0
        self.total_deaths = 0
        self.total_timeouts = 0
        self.start_time = time.time()
        
        # Reward plotting
        self.reward_plotter = SimpleRewardPlotter(window_size=100)

        # Setup pygame display
        pygame.init()
        
        if self.render:
            # Normal mode with display
            self.screen = pygame.display.set_mode(SCREENSIZE)
            pygame.display.set_caption("Optimized Q-Learning Training")
            self.clock = pygame.time.Clock()
        else:
            # Headless mode - use virtual surface
            self.screen = pygame.Surface(SCREENSIZE)
            self.clock = None
            print("✓ Headless mode activated")

    def print_config(self):
        """In cấu hình training"""
        print("=" * 80)
        print("OPTIMIZED Q-LEARNING TRAINING CONFIGURATION")
        print("=" * 80)
        print(f"Max Episodes: {self.max_episodes}")
        print(f"Max Steps per Episode: {self.max_steps_per_episode}")
        print(f"Save Interval: {self.save_interval}")
        print(f"Render: {self.render}")
        print(f"Few Pellets Mode: {self.few_pellets_mode}")
        if self.few_pellets_mode:
            print(f"Pellet Count: {self.few_pellets_count}")
        print(f"Adaptive Learning: {self.adaptive_learning}")
        print(f"Performance Window: {self.performance_window}")
        print("=" * 80)
        print("OPTIMIZATIONS APPLIED:")
        print("✓ Enhanced reward system with 10 components")
        print("✓ Improved state representation (11 features)")
        print("✓ Optimized Q-learning parameters")
        print("✓ Adaptive learning rate")
        print("✓ Performance monitoring")
        print("✓ Convergence detection")
        print("=" * 80)
    
    def train(self):        
        for episode in range(1, self.max_episodes + 1):
            print(f"\n{'='*80}")
            print(f"EPISODE {episode}/{self.max_episodes}")
            print(f"{'='*80}")
            
            # Adaptive learning rate adjustment
            if self.adaptive_learning and episode > self.performance_window:
                self._adjust_learning_rate(episode)
            
            # Run episode
            episode_reward, episode_step, final_score, episode_result, current_epsilon = self.run_episode(episode)
            
            # Track performance
            self._track_performance(episode_reward, episode_step, final_score, episode_result, current_epsilon, episode)
            
            # Add to reward plotter
            self.reward_plotter.add_episode(episode, episode_reward, final_score)
            
            
            if episode % self.save_interval == 0:
                img_dir = "reward_images"
                os.makedirs(img_dir, exist_ok=True)
                img_path = os.path.join(img_dir, f'reward_curves_ep{episode}.png')
                self.reward_plotter.plot_rewards(save_path=img_path, show_plot=False)
            
            # Save model periodically
            if episode % self.save_interval == 0:
                self.save_model(episode)
    
        
        print("\n" + "=" * 80)
        print("TRAINING COMPLETED!")
        print("=" * 80)
        self.save_model(self.max_episodes, final=True)
        
        # Final reward plots
        self.reward_plotter.plot_rewards(save_path='final_reward_curves.png', show_plot=True)
        self.reward_plotter.plot_reward_distribution(save_path='final_reward_distribution.png', show_plot=True)
        self.reward_plotter.save_data('training_data.json')
        
        self._plot_training_results()
        
        pygame.quit()

    def run_episode(self, episode_num):
        game = Game(algorithm='Q-Learning')
        game.screen = self.screen if self.render else None

        game.ai_mode = True
        game.ghost_mode = True  
        game.few_pellets_mode = self.few_pellets_mode
        game.few_pellets_count = self.few_pellets_count
        game.initialize_game()

        # Setup Q-learning
        game.pacman.set_q_learning(True)
        game.pacman.hybrid_ai.set_training_mode(True)
        game.pacman.hybrid_ai.init_q_learning()
        

        game.pacman.hybrid_ai.q_agent.load('q_table.json')

        
        self._set_adaptive_epsilon(game, episode_num)
        
        self.last_game = game
        total_reward = 0
        steps = 0
        episode_result = 'timeout'  
        current_epsilon = 0.0
        
        if hasattr(game.pacman, 'hybrid_ai') and hasattr(game.pacman.hybrid_ai, 'q_agent'):
            current_epsilon = game.pacman.hybrid_ai.q_agent.epsilon
        
        game.pause.paused = False
        
        prev_pellet_count = len([p for p in game.pellets.pelletList if p.visible])
        
        # Main game loop
        while game.running and steps < self.max_steps_per_episode:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            game.update()

            if game.ai_mode and hasattr(game.pacman, 'hybrid_ai'):
                if hasattr(game.pacman.hybrid_ai, 'q_learning_get_direction'):
                    action, step_reward = game.pacman.hybrid_ai.q_learning_get_direction(game.pellets, game.ghosts)
                    total_reward += step_reward

            if self.render:
                game.render(self.screen)
                pygame.display.update()
                if self.clock:
                    self.clock.tick(60)

            steps += 1
            
            # Check termination conditions
            if not game.pacman.alive:
                episode_result = 'death'
                break
            
            pellets_left = len([p for p in game.pellets.pelletList if p.visible])
            if pellets_left == 0:
                episode_result = 'win'
                break
        
        if steps >= self.max_steps_per_episode:
            episode_result = 'timeout'
            
        final_score = game.score
        return total_reward, steps, final_score, episode_result, current_epsilon

    def _set_adaptive_epsilon(self, game, episode_num):
        if not hasattr(game.pacman, 'hybrid_ai') or not hasattr(game.pacman.hybrid_ai, 'q_agent'):
            return

        q_agent = game.pacman.hybrid_ai.q_agent

        # EPSILON FIXED THEO PHASES - KHÔNG DECAY DẦN DẦN
        # Học nhanh bằng cách nhảy phases rõ ràng
        max_ep = self.max_episodes
        
        if max_ep <= 100:
            # Quick test (50-100 episodes): 3 phases rõ ràng
            if episode_num < int(max_ep * 0.3):
                epsilon = 0.9    # 30% đầu: Explore mạnh
            elif episode_num < int(max_ep * 0.7):
                epsilon = 0.5    # 40% giữa: Balanced
            else:
                epsilon = 0.1    # 30% cuối: Exploit mạnh
                
        elif max_ep <= 1500:
            # Curriculum stage 1 & 2 (1000-1500): Learn fast
            if episode_num < int(max_ep * 0.25):
                epsilon = 0.7    # 25% đầu: Explore
            elif episode_num < int(max_ep * 0.6):
                epsilon = 0.3    # 35% giữa: Balanced
            elif episode_num < int(max_ep * 0.85):
                epsilon = 0.12   # 25% sau: Exploit
            else:
                epsilon = 0.05   # 15% cuối: Exploit max
                
        else:
            # Long training (20k): 5 phases cho smooth learning
            if episode_num < int(max_ep * 0.15):
                epsilon = 0.8    # 15% đầu (0-3k): Explore mạnh
            elif episode_num < int(max_ep * 0.35):
                epsilon = 0.5    # 20% giữa (3k-7k): Balanced
            elif episode_num < int(max_ep * 0.6):
                epsilon = 0.25   # 25% (7k-12k): Exploit nhiều
            elif episode_num < int(max_ep * 0.85):
                epsilon = 0.1    # 25% (12k-17k): Exploit mạnh
            else:
                epsilon = 0.03   # 15% cuối (17k-20k): Exploit max
        
        # Set epsilon (no adaptive adjustment for fast learning)
        print(epsilon)
        q_agent.epsilon = epsilon

    def _adjust_learning_rate(self, episode):
        """Adaptive learning rate cho ultra long training"""
        if not hasattr(self, 'last_game') or not hasattr(self.last_game.pacman, 'hybrid_ai'):
            return
        
        q_agent = self.last_game.pacman.hybrid_ai.q_agent
        
        # Phân phases cho 10k episodes
        if episode < 1000:
            alpha = 0.3      # Phase 1: Học nhanh, khám phá nhiều
        elif episode < 3000:
            alpha = 0.2      # Phase 2: Học vừa, bắt đầu exploit
        elif episode < 6000:
            alpha = 0.1      # Phase 3: Học chậm, focus vào exploitation
        elif episode < 9000:
            alpha = 0.05     # Phase 4: Fine-tuning
        else:
            alpha = 0.02     # Phase 5: Polish final policy
        
        # Adaptive adjustment dựa trên convergence
        if len(self.recent_performance) >= 200:
            recent_std = np.std(list(self.recent_performance)[-200:])
            if recent_std > 20:  # High variance = chưa converge
                alpha *= 1.2  # Tăng learning rate
            elif recent_std < 5:  # Low variance = converged
                alpha *= 0.8  # Giảm learning rate
        
        q_agent.alpha = alpha
        self.learning_rate_history.append(alpha)

    def _track_performance(self, reward, steps, score, result, epsilon, episode):
        """Track performance metrics"""
        self.episode_rewards.append(reward)
        self.episode_steps.append(steps)
        self.episode_scores.append(score)
        self.episode_epsilons.append(epsilon)
        self.episode_deaths.append(1 if result == 'death' else 0)
        self.episode_wins.append(1 if result == 'win' else 0)
        self.episode_timeouts.append(1 if result == 'timeout' else 0)
        
        self.recent_performance.append(reward)
        
        # Update best performance
        if score > self.best_score:
            self.best_score = score
            self.best_episode = episode
            
        if reward > self.best_reward:
            self.best_reward = reward
            
        # Update counters
        if result == 'win':
            self.total_wins += 1
        elif result == 'death':
            self.total_deaths += 1
        elif result == 'timeout':
            self.total_timeouts += 1

  

    def save_model(self, episode, final=False):
        """Lưu model và training data"""
        if not hasattr(self, 'last_game'):
            return
            
        game = self.last_game
        filename = 'q_table.json'
        game.pacman.hybrid_ai.q_agent.save(filename)
        
        stats_dir = "training_stats"
        os.makedirs(stats_dir, exist_ok=True)
        stats_filename = os.path.join(stats_dir, f'training_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        stats = {
            'episode': episode,
            'total_episodes': len(self.episode_rewards),
            'best_score': self.best_score,
            'best_reward': self.best_reward,
            'win_rate': self.total_wins / len(self.episode_rewards) if self.episode_rewards else 0,
            'death_rate': self.total_deaths / len(self.episode_rewards) if self.episode_rewards else 0,
            'timeout_rate': self.total_timeouts / len(self.episode_rewards) if self.episode_rewards else 0,
            'average_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0,
            'average_score': np.mean(self.episode_scores) if self.episode_scores else 0,
            'average_steps': np.mean(self.episode_steps) if self.episode_steps else 0,
            'episode_rewards': self.episode_rewards,
            'episode_scores': self.episode_scores,
            'episode_steps': self.episode_steps,
            'episode_epsilons': self.episode_epsilons,
            'learning_rate_history': self.learning_rate_history
        }
        
        with open(stats_filename, 'w') as f:
            json.dump(stats, f, indent=2)

    def _plot_training_results(self):
        """Vẽ biểu đồ kết quả training"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Q-Learning Training Results', fontsize=16)
        
        # Plot 1: Episode Rewards
        axes[0, 0].plot(self.episode_rewards, alpha=0.6)
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Reward')
        
        # Plot 2: Episode Scores
        axes[0, 1].plot(self.episode_scores, alpha=0.6)
        axes[0, 1].set_title('Episode Scores')
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Score')
        
        # Plot 3: Epsilon Decay
        axes[1, 0].plot(self.episode_epsilons, alpha=0.6)
        axes[1, 0].set_title('Epsilon Decay')
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Epsilon')
        
        # Plot 4: Win/Death/Timeout Rates
        episodes = range(1, len(self.episode_wins) + 1)
        win_rates = np.cumsum(self.episode_wins) / episodes
        death_rates = np.cumsum(self.episode_deaths) / episodes
        timeout_rates = np.cumsum(self.episode_timeouts) / episodes
        
        axes[1, 1].plot(episodes, win_rates, label='Win Rate', alpha=0.8)
        axes[1, 1].plot(episodes, death_rates, label='Death Rate', alpha=0.8)
        axes[1, 1].plot(episodes, timeout_rates, label='Timeout Rate', alpha=0.8)
        axes[1, 1].set_title('Success Rates Over Time')
        axes[1, 1].set_xlabel('Episode')
        axes[1, 1].set_ylabel('Rate')
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('training_results.png', dpi=300, bbox_inches='tight')
            

if __name__ == "__main__":
    # ==========================================================
    # CẤU HÌNH TRAINING - CHỌN PHÙ HỢP VỚI MỤC ĐÍCH
    # ==========================================================
    
    # QUICK TEST (5-10 phút) - Test fix Q-learning
    quick_test_config = {
        'max_episodes': 50,              # 50 episodes để test nhanh
        'save_interval': 5,              # Lưu mỗi 5 episodes
        'max_steps_per_episode': 1000,   # 1000 steps
        'render': False,                 # TẮT RENDER để tăng tốc 10-20x
        'few_pellets_mode': False,       # Full maze
        'few_pellets_count': 20,         # 20 pellets
        'adaptive_learning': False,      # TẮT adaptive
        'performance_window': 20         # Cửa sổ nhỏ
    }
    
    # FAST LEARNING (30-60 phút) - 500 episodes học nhanh
    fast_learning_config = {
        'max_episodes': 500,             # 500 episodes
        'save_interval': 50,             # Lưu mỗi 50 episodes
        'max_steps_per_episode': 1500,   # 1500 steps
        'render': False,                 # Tắt render để nhanh
        'few_pellets_mode': False,       # Full maze
        'few_pellets_count': 30,         
        'adaptive_learning': False,      # TẮT adaptive, dùng epsilon fixed
        'performance_window': 100
    }
    
    # MEDIUM LEARNING (1-2 giờ) - 1000 episodes
    medium_learning_config = {
        'max_episodes': 1000,            # 1000 episodes
        'save_interval': 100,            # Lưu mỗi 100 episodes
        'max_steps_per_episode': 2000,   # 2000 steps
        'render': False,                 # Tắt render
        'few_pellets_mode': False,       # Full maze
        'few_pellets_count': 30,
        'adaptive_learning': False,      # TẮT adaptive
        'performance_window': 200
    }
    
    ultra_long_training_config = {
        'max_episodes': 10000,           # 10,000 episodes (5-8 giờ)
        'save_interval': 100,            # Lưu mỗi 100 episodes
        'max_steps_per_episode': 3000,   # 3000 steps cho phép explore đầy đủ
        'render': False,                 # Tắt render cho tốc độ tối đa
        'few_pellets_mode': False,       # Full maze để học đầy đủ
        'few_pellets_count': 30,         # Không dùng
        'adaptive_learning': True,       # Bật adaptive learning rate & epsilon
        'performance_window': 300        # Cửa sổ vừa phải cho 10k episodes
    }
    
    # PRODUCTION (2-4 giờ)
    production_config = {
        'max_episodes': 8000,            # Training đầy đủ
        'save_interval': 50,            # Lưu mỗi 100 episodes
        'max_steps_per_episode': 1250,   # Steps đầy đủ
        'render': True,                 # Tắt render để nhanh hơn
        'few_pellets_mode': False,       # Dùng full maze
        'few_pellets_count': 30,         # Không dùng
        'adaptive_learning': True,       # Bật adaptive learning
        'performance_window': 100        # Cửa sổ bình thường
    }
    
    # ==========================================================
    # DIRECT TRAINING - 20,000 EPISODES (NO CURRICULUM)
    # ==========================================================
    
    training_config = {
        'max_episodes': 20000,           # 20,000 episodes trực tiếp
        'save_interval': 500,            # Lưu mỗi 500 episodes
        'max_steps_per_episode': 2500,   # 2500 steps mỗi episode
        'render': False,                 # Tắt render để tăng tốc
        'few_pellets_mode': False,       # Full maze ngay từ đầu
        'few_pellets_count': 30,
        'adaptive_learning': False,      # Epsilon fixed theo phases
        'performance_window': 1000       # Cửa sổ lớn
    }
    
    print("\n" + "=" * 80)
    print("🚀 DIRECT TRAINING - 20,000 EPISODES (FULL MAZE)")
    print("=" * 80)
    print(f"Max episodes: {training_config['max_episodes']}")
    print(f"Max steps per episode: {training_config['max_steps_per_episode']}")
    print(f"Save interval: {training_config['save_interval']}")
    print(f"Full maze: ~240 pellets")
    print(f"Estimated time: ~8-10 hours")
    print("=" * 80)
    
    trainer = OptimizedQLearningTrainer(**training_config)
    trainer.train()
    
    print("\n" + "=" * 80)
    print("🎉 TRAINING COMPLETED - 20,000 EPISODES!")
    print("=" * 80)
    print(f"Total training time: {(time.time() - trainer.start_time)/3600:.1f} hours")