#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLE REWARD CURVE PLOTTER
===========================

Script đơn giản để vẽ đường cong reward trong quá trình training Q-learning.
Có thể sử dụng trong training script hoặc vẽ từ dữ liệu đã có.

Author: AI Assistant
Date: 2024
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
from collections import deque

class SimpleRewardPlotter:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.rewards_history = []
        self.scores_history = []
        self.episodes = []
        
    def add_episode(self, episode, reward, score=None):
        """Thêm dữ liệu episode mới"""
        self.episodes.append(episode)
        self.rewards_history.append(reward)
        if score is not None:
            self.scores_history.append(score)
    
    def plot_rewards(self, save_path=None, show_plot=True):
        """Vẽ đường cong reward"""
        if not self.rewards_history:
            print("Không có dữ liệu để vẽ!")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Plot 1: Episode Rewards
        plt.subplot(2, 1, 1)
        plt.plot(self.episodes, self.rewards_history, alpha=0.6, color='blue', label='Episode Rewards')
        
        # Moving average
        if len(self.rewards_history) > self.window_size:
            moving_avg = self._calculate_moving_average(self.rewards_history, self.window_size)
            plt.plot(self.episodes[self.window_size-1:], moving_avg, 
                    color='red', linewidth=2, label=f'Moving Average ({self.window_size})')
        
        plt.title('Episode Rewards Over Time')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Plot 2: Episode Scores (nếu có)
        if self.scores_history:
            plt.subplot(2, 1, 2)
            plt.plot(self.episodes, self.scores_history, alpha=0.6, color='green', label='Episode Scores')
            
            if len(self.scores_history) > self.window_size:
                moving_avg = self._calculate_moving_average(self.scores_history, self.window_size)
                plt.plot(self.episodes[self.window_size-1:], moving_avg, 
                        color='orange', linewidth=2, label=f'Moving Average ({self.window_size})')
            
            plt.title('Episode Scores Over Time')
            plt.xlabel('Episode')
            plt.ylabel('Score')
            plt.grid(True, alpha=0.3)
            plt.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Biểu đồ đã được lưu tại: {save_path}")
        
        if show_plot:
            plt.show()
    
    def plot_reward_distribution(self, save_path=None, show_plot=True):
        """Vẽ phân phối reward"""
        if not self.rewards_history:
            print("Không có dữ liệu để vẽ!")
            return
        
        plt.figure(figsize=(10, 6))
        
        plt.hist(self.rewards_history, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(np.mean(self.rewards_history), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(self.rewards_history):.2f}')
        plt.axvline(np.median(self.rewards_history), color='green', linestyle='--', 
                   linewidth=2, label=f'Median: {np.median(self.rewards_history):.2f}')
        
        plt.title('Reward Distribution')
        plt.xlabel('Reward')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Biểu đồ phân phối đã được lưu tại: {save_path}")
        
        if show_plot:
            plt.show()
    
    def _calculate_moving_average(self, data, window):
        """Tính moving average"""
        return np.convolve(data, np.ones(window)/window, mode='valid')
    
    def save_data(self, filename):
        """Lưu dữ liệu ra file JSON"""
        data = {
            'episodes': self.episodes,
            'rewards': self.rewards_history,
            'scores': self.scores_history,
            'window_size': self.window_size
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Dữ liệu đã được lưu tại: {filename}")
    
    def load_data(self, filename):
        """Load dữ liệu từ file JSON"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.episodes = data['episodes']
        self.rewards_history = data['rewards']
        self.scores_history = data.get('scores', [])
        self.window_size = data.get('window_size', 100)
        print(f"Dữ liệu đã được load từ: {filename}")

def plot_from_training_file(filename):
    """Vẽ từ file training data"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        plotter = SimpleRewardPlotter()
        plotter.episodes = list(range(1, len(data['episode_rewards']) + 1))
        plotter.rewards_history = data['episode_rewards']
        plotter.scores_history = data.get('episode_scores', [])
        
        plotter.plot_rewards(save_path='reward_curves.png')
        plotter.plot_reward_distribution(save_path='reward_distribution.png')
        
    except FileNotFoundError:
        print(f"Không tìm thấy file: {filename}")
    except Exception as e:
        print(f"Lỗi khi load file: {e}")

def plot_demo():
    """Vẽ demo với dữ liệu giả lập"""
    print("Tạo demo data...")
    
    plotter = SimpleRewardPlotter(window_size=50)
    
    # Tạo dữ liệu demo
    episodes = 1000
    base_reward = 0
    rewards = []
    
    for episode in range(1, episodes + 1):
        # Tạo xu hướng tăng dần với noise
        trend = episode * 0.02  # Xu hướng tăng
        noise = np.random.normal(0, 3)  # Noise
        spike = np.random.poisson(0.1) * np.random.uniform(5, 20)  # Spikes ngẫu nhiên
        
        reward = base_reward + trend + noise + spike
        rewards.append(reward)
        
        # Thêm vào plotter mỗi 10 episodes
        if episode % 10 == 0:
            plotter.add_episode(episode, reward, reward * 10)  # Score = reward * 10
    
    print("Vẽ biểu đồ demo...")
    plotter.plot_rewards(save_path='demo_reward_curves.png')
    plotter.plot_reward_distribution(save_path='demo_reward_distribution.png')
    
    print("Demo hoàn thành!")

def main():
    """Main function"""
    print("SIMPLE REWARD CURVE PLOTTER")
    print("="*40)
    print("1. Vẽ từ file training data")
    print("2. Vẽ demo")
    print("3. Vẽ từ dữ liệu real-time")
    
    choice = input("\nChọn option (1-3): ").strip()
    
    if choice == '1':
        filename = input("Nhập tên file training data: ").strip()
        if not filename:
            # Tìm file mới nhất
            import glob
            files = glob.glob('training_stats_*.json')
            if files:
                filename = max(files, key=os.path.getctime)
                print(f"Sử dụng file: {filename}")
            else:
                print("Không tìm thấy file training data!")
                return
        plot_from_training_file(filename)
    
    elif choice == '2':
        plot_demo()
    
    elif choice == '3':
        print("Sử dụng trong training script:")
        print("""
# Trong training loop:
from simple_reward_plot import SimpleRewardPlotter

plotter = SimpleRewardPlotter(window_size=100)

for episode in range(max_episodes):
    # ... training code ...
    episode_reward = run_episode()
    
    # Thêm dữ liệu vào plotter
    plotter.add_episode(episode, episode_reward, final_score)
    
    # Vẽ biểu đồ mỗi 50 episodes
    if episode % 50 == 0:
        plotter.plot_rewards(save_path=f'reward_curves_ep{episode}.png')
        """)
    
    else:
        print("Invalid choice!")
        plot_demo()

if __name__ == "__main__":
    main()
