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
import pygame
import sys
import time
import csv
import json
import numpy as np
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

        # Setup cho headless mode trên Ubuntu CLI
        if self.render:
            pygame.init()
            self.screen = pygame.display.set_mode(SCREENSIZE)
            pygame.display.set_caption("Optimized Q-Learning Training")
            self.clock = pygame.time.Clock()
        else:
            # Headless mode - không cần display
            os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Use dummy video driver
            pygame.init()
            self.screen = pygame.Surface(SCREENSIZE)  # Virtual surface
            self.clock = None

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
        """Main training loop với adaptive learning"""
        self.print_config()
        
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
            
            # Print episode summary
            self._print_episode_summary(episode, episode_reward, episode_step, final_score, episode_result)
            
            # Plot rewards periodically
            if episode % self.save_interval == 0:
                img_dir = "reward_images"
                os.makedirs(img_dir, exist_ok=True)
                img_path = os.path.join(img_dir, f'reward_curves_ep{episode}.png')
                self.reward_plotter.plot_rewards(save_path=img_path, show_plot=False)
                print(f"   📊 Reward curves saved: {img_path}")
            
            # Save model periodically
            if episode % self.save_interval == 0:
                self.save_model(episode)
    
            # Check for convergence
            if self._check_convergence():
                print(f"\n🎯 CONVERGENCE DETECTED at episode {episode}!")
                print("Training completed early due to convergence.")
                break
        
        print("\n" + "=" * 80)
        print("TRAINING COMPLETED!")
        print("=" * 80)
        self._print_final_statistics()
        self.save_model(self.max_episodes, final=True)
        
        # Final reward plots
        self.reward_plotter.plot_rewards(save_path='final_reward_curves.png', show_plot=True)
        self.reward_plotter.plot_reward_distribution(save_path='final_reward_distribution.png', show_plot=True)
        self.reward_plotter.save_data('training_data.json')
        
        self._plot_training_results()
        
        pygame.quit()

    def run_episode(self, episode_num):
        """Chạy một episode với adaptive parameters"""
        print(f"Creating new game for episode {episode_num}")
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
        
        print(total_reward)
        if steps >= self.max_steps_per_episode:
            episode_result = 'timeout'
            
        final_score = game.score
        return total_reward, steps, final_score, episode_result, current_epsilon

    def _set_adaptive_epsilon(self, game, episode_num):
        if not hasattr(game.pacman, 'hybrid_ai') or not hasattr(game.pacman.hybrid_ai, 'q_agent'):
            return

        q_agent = game.pacman.hybrid_ai.q_agent

        # Cấu hình cho training dài
        eps_start = 1.0
        eps_min = 0.05      # Epsilon min thấp hơn cho exploitation
        decay_rate = 0.9995  # Decay chậm hơn cho training dài

        epsilon = max(eps_min, eps_start * (decay_rate ** episode_num))

        if self.adaptive_learning and len(self.recent_performance) >= 50:
            recent_avg = np.mean(list(self.recent_performance)[-50:])
            if recent_avg < -10:   # Threshold thấp hơn
                epsilon = min(0.8, epsilon + 0.05)  # Tăng exploration ít hơn
            elif recent_avg > 20:  # Threshold cao hơn
                epsilon = max(0.02, epsilon - 0.02)  # Giảm exploration ít hơn
        
        q_agent.epsilon = epsilon

    def _adjust_learning_rate(self, episode):
        if episode < 1000:
            alpha = 0.3      # Cao cho exploration
        elif episode < 5000:
            alpha = 0.2      # Trung bình
        elif episode < 10000:
            alpha = 0.1      # Thấp hơn
        else:
            alpha = 0.05     # Rất thấp cho fine-tuning

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

    def _print_episode_summary(self, episode, reward, steps, score, result):
        """In tóm tắt episode"""
        print(f"\nEPISODE {episode} SUMMARY:")
        print(f"   Total Reward: {reward:.2f}")
        print(f"   Steps Taken: {steps}")
        print(f"   Final Score: {score}")
        print(f"   Result: {result.upper()}")
        print(f"   Best Score Ever: {self.best_score}")
        
        if len(self.recent_performance) >= 10:
            recent_avg = np.mean(list(self.recent_performance)[-10:])
            print(f"   Recent Avg Reward: {recent_avg:.2f}")

    def _check_convergence(self):
        """Kiểm tra convergence"""
        if len(self.recent_performance) < self.performance_window:
            return False
            
        recent_rewards = list(self.recent_performance)[-self.performance_window:]
        std_dev = np.std(recent_rewards)
        mean_reward = np.mean(recent_rewards)
        
        # Convergence nếu std dev thấp và mean reward cao
        return std_dev < self.convergence_threshold and mean_reward > 10

    def _print_final_statistics(self):
        """In thống kê cuối"""
        total_episodes = len(self.episode_rewards)
        total_time = time.time() - self.start_time
        
        print(f"Total Episodes: {total_episodes}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per Episode: {total_time/total_episodes:.2f} seconds")
        print(f"Best Score: {self.best_score} (Episode {self.best_episode})")
        print(f"Best Reward: {self.best_reward:.2f}")
        print(f"Win Rate: {self.total_wins/total_episodes*100:.1f}%")
        print(f"Death Rate: {self.total_deaths/total_episodes*100:.1f}%")
        print(f"Timeout Rate: {self.total_timeouts/total_episodes*100:.1f}%")
        
        if len(self.episode_rewards) > 0:
            print(f"Average Reward: {np.mean(self.episode_rewards):.2f}")
            print(f"Average Score: {np.mean(self.episode_scores):.2f}")
            print(f"Average Steps: {np.mean(self.episode_steps):.2f}")

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
        
        print(f"Saved Q-table to {filename}")
        print(f"Saved training stats to {stats_filename}")

    def _plot_training_results(self):
        """Vẽ biểu đồ kết quả training"""
        try:
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
            print("Training results plot saved as 'training_results.png'")
            
        except Exception as e:
            print(f"Could not create plot: {e}")

if __name__ == "__main__":
    print("\nOPTIMIZED Q-LEARNING TRAINING FOR PACMAN")
    print("=" * 80)
    
    # ==========================================================
    # CẤU HÌNH TRAINING - CHỌN PHÙ HỢP VỚI MỤC ĐÍCH
    # ==========================================================
    
    # QUICK TEST (5-10 phút) - Tối ưu cho episodes nhỏ
    quick_test_config = {
        'max_episodes': 100,             # Tăng episodes để có nhiều states
        'save_interval': 5,             # Lưu mỗi 10 episodes
        'max_steps_per_episode': 800,    # Tăng steps để explore nhiều hơn
        'render': True,                  # Hiển thị game
        'few_pellets_mode': False,        # Dùng ít pellets để test nhanh
        'few_pellets_count': 20,         # Tăng pellets để có nhiều states
        'adaptive_learning': True,       # Bật adaptive cho episodes nhỏ
        'performance_window': 20         # Cửa sổ nhỏ
    }
    
    ultra_long_training_config = {
        'max_episodes': 30000,           # 30,000 episodes
        'save_interval': 200,            # Lưu mỗi 200 episodes
        'max_steps_per_episode': 3000,   # 3000 steps mỗi episode
        'render': False,                 # Tắt render
        'few_pellets_mode': False,       # Full maze
        'few_pellets_count': 30,         # Không dùng
        'adaptive_learning': True,       # Bật adaptive
        'performance_window': 500        # Cửa sổ rất lớn
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
    
    config = quick_test_config 
    
    print("TRAINING CONFIGURATION:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    print("=" * 80)
    
    trainer = OptimizedQLearningTrainer(**config)
    trainer.train()
