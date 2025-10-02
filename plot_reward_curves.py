#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REWARD CURVE PLOTTING SCRIPT
============================

Script để vẽ các đường cong reward và performance metrics:
- Episode rewards over time
- Moving average rewards
- Win rate, death rate, timeout rate
- Learning progress visualization

Author: AI Assistant
Date: 2024
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import pandas as pd
from datetime import datetime
import os
import glob

class RewardCurvePlotter:
    def __init__(self):
        self.colors = {
            'reward': '#2E86AB',
            'score': '#A23B72', 
            'win_rate': '#F18F01',
            'death_rate': '#C73E1D',
            'timeout_rate': '#6A994E',
            'moving_avg': '#FF6B35'
        }
        
    def plot_from_training_data(self, data_file=None):
        """Vẽ biểu đồ từ dữ liệu training"""
        if data_file is None:
            # Tìm file training data mới nhất
            training_files = glob.glob('training_stats_*.json')
            if not training_files:
                print("Không tìm thấy file training data!")
                return
            data_file = max(training_files, key=os.path.getctime)
            print(f"Sử dụng file: {data_file}")
        
        # Load data
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        self._plot_comprehensive_analysis(data)
    
    def plot_from_q_table(self, q_table_file='q_table.json'):
        """Vẽ biểu đồ từ Q-table (nếu có thông tin training)"""
        try:
            with open(q_table_file, 'r') as f:
                q_data = json.load(f)
            
            # Tạo dữ liệu giả lập để demo
            episodes = 1000
            rewards = self._generate_demo_rewards(episodes)
            self._plot_demo_curves(episodes, rewards)
            
        except FileNotFoundError:
            print(f"Không tìm thấy file {q_table_file}")
            self._plot_demo_curves()
    
    def plot_real_time(self, episode_rewards, episode_scores=None, 
                      episode_steps=None, win_rates=None):
        """Vẽ biểu đồ real-time từ dữ liệu hiện tại"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Real-time Training Progress', fontsize=16)
        
        episodes = range(1, len(episode_rewards) + 1)
        
        # Plot 1: Episode Rewards
        axes[0, 0].plot(episodes, episode_rewards, alpha=0.6, color=self.colors['reward'])
        if len(episode_rewards) > 10:
            moving_avg = self._calculate_moving_average(episode_rewards, window=50)
            axes[0, 0].plot(episodes[49:], moving_avg, color=self.colors['moving_avg'], 
                           linewidth=2, label='Moving Average (50)')
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Reward')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend()
        
        # Plot 2: Episode Scores
        if episode_scores:
            axes[0, 1].plot(episodes, episode_scores, alpha=0.6, color=self.colors['score'])
            if len(episode_scores) > 10:
                moving_avg = self._calculate_moving_average(episode_scores, window=50)
                axes[0, 1].plot(episodes[49:], moving_avg, color=self.colors['moving_avg'], 
                               linewidth=2, label='Moving Average (50)')
            axes[0, 1].set_title('Episode Scores')
            axes[0, 1].set_xlabel('Episode')
            axes[0, 1].set_ylabel('Score')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].legend()
        
        # Plot 3: Episode Steps
        if episode_steps:
            axes[1, 0].plot(episodes, episode_steps, alpha=0.6, color='purple')
            axes[1, 0].set_title('Episode Steps')
            axes[1, 0].set_xlabel('Episode')
            axes[1, 0].set_ylabel('Steps')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Success Rates
        if win_rates:
            axes[1, 1].plot(episodes, win_rates, color=self.colors['win_rate'], 
                           linewidth=2, label='Win Rate')
            axes[1, 1].set_title('Success Rates')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('Rate (%)')
            axes[1, 1].set_ylim(0, 100)
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].legend()
        
        plt.tight_layout()
        plt.show()
    
    def _plot_comprehensive_analysis(self, data):
        """Vẽ phân tích toàn diện từ dữ liệu training"""
        fig, axes = plt.subplots(3, 2, figsize=(16, 12))
        fig.suptitle('Q-Learning Training Analysis', fontsize=18)
        
        episodes = range(1, len(data['episode_rewards']) + 1)
        
        # Plot 1: Episode Rewards với Moving Average
        axes[0, 0].plot(episodes, data['episode_rewards'], alpha=0.4, color=self.colors['reward'])
        if len(data['episode_rewards']) > 50:
            moving_avg_50 = self._calculate_moving_average(data['episode_rewards'], 50)
            moving_avg_100 = self._calculate_moving_average(data['episode_rewards'], 100)
            axes[0, 0].plot(episodes[49:], moving_avg_50, color=self.colors['moving_avg'], 
                           linewidth=2, label='MA-50')
            axes[0, 0].plot(episodes[99:], moving_avg_100, color='red', 
                           linewidth=2, label='MA-100')
        axes[0, 0].set_title('Episode Rewards với Moving Average')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Reward')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend()
        
        # Plot 2: Episode Scores
        axes[0, 1].plot(episodes, data['episode_scores'], alpha=0.6, color=self.colors['score'])
        if len(data['episode_scores']) > 50:
            moving_avg = self._calculate_moving_average(data['episode_scores'], 50)
            axes[0, 1].plot(episodes[49:], moving_avg, color=self.colors['moving_avg'], 
                           linewidth=2, label='Moving Average')
        axes[0, 1].set_title('Episode Scores')
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Score')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend()
        
        # Plot 3: Epsilon Decay
        if 'episode_epsilons' in data:
            axes[1, 0].plot(episodes, data['episode_epsilons'], color='orange', linewidth=2)
            axes[1, 0].set_title('Epsilon Decay (Exploration Rate)')
            axes[1, 0].set_xlabel('Episode')
            axes[1, 0].set_ylabel('Epsilon')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Learning Rate History
        if 'learning_rate_history' in data and data['learning_rate_history']:
            lr_episodes = range(1, len(data['learning_rate_history']) + 1)
            axes[1, 1].plot(lr_episodes, data['learning_rate_history'], color='green', linewidth=2)
            axes[1, 1].set_title('Learning Rate History')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('Alpha (Learning Rate)')
            axes[1, 1].grid(True, alpha=0.3)
        
        # Plot 5: Reward Distribution
        axes[2, 0].hist(data['episode_rewards'], bins=50, alpha=0.7, color=self.colors['reward'])
        axes[2, 0].axvline(np.mean(data['episode_rewards']), color='red', 
                          linestyle='--', label=f'Mean: {np.mean(data["episode_rewards"]):.2f}')
        axes[2, 0].set_title('Reward Distribution')
        axes[2, 0].set_xlabel('Reward')
        axes[2, 0].set_ylabel('Frequency')
        axes[2, 0].legend()
        axes[2, 0].grid(True, alpha=0.3)
        
        # Plot 6: Performance Metrics
        win_rate = data.get('win_rate', 0) * 100
        death_rate = data.get('death_rate', 0) * 100
        timeout_rate = data.get('timeout_rate', 0) * 100
        
        metrics = ['Win Rate', 'Death Rate', 'Timeout Rate']
        values = [win_rate, death_rate, timeout_rate]
        colors = [self.colors['win_rate'], self.colors['death_rate'], self.colors['timeout_rate']]
        
        bars = axes[2, 1].bar(metrics, values, color=colors, alpha=0.7)
        axes[2, 1].set_title('Final Performance Metrics')
        axes[2, 1].set_ylabel('Rate (%)')
        axes[2, 1].set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            axes[2, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                           f'{value:.1f}%', ha='center', va='bottom')
        
        axes[2, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('comprehensive_training_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Print summary statistics
        self._print_summary_stats(data)
    
    def _plot_demo_curves(self, episodes=1000, rewards=None):
        """Vẽ demo curves để minh họa"""
        if rewards is None:
            rewards = self._generate_demo_rewards(episodes)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Demo: Q-Learning Training Curves', fontsize=16)
        
        episode_range = range(1, episodes + 1)
        
        # Plot 1: Episode Rewards
        axes[0, 0].plot(episode_range, rewards, alpha=0.6, color=self.colors['reward'])
        if episodes > 50:
            moving_avg = self._calculate_moving_average(rewards, 50)
            axes[0, 0].plot(episode_range[49:], moving_avg, color=self.colors['moving_avg'], 
                           linewidth=2, label='Moving Average (50)')
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Reward')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend()
        
        # Plot 2: Reward Distribution
        axes[0, 1].hist(rewards, bins=30, alpha=0.7, color=self.colors['reward'])
        axes[0, 1].axvline(np.mean(rewards), color='red', linestyle='--', 
                          label=f'Mean: {np.mean(rewards):.2f}')
        axes[0, 1].set_title('Reward Distribution')
        axes[0, 1].set_xlabel('Reward')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Epsilon Decay (demo)
        epsilon_values = [max(0.02, 1.0 * (0.9995 ** i)) for i in episode_range]
        axes[1, 0].plot(episode_range, epsilon_values, color='orange', linewidth=2)
        axes[1, 0].set_title('Epsilon Decay (Demo)')
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Epsilon')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Learning Progress (demo)
        progress = np.cumsum(rewards) / np.arange(1, len(rewards) + 1)
        axes[1, 1].plot(episode_range, progress, color='green', linewidth=2)
        axes[1, 1].set_title('Cumulative Average Reward')
        axes[1, 1].set_xlabel('Episode')
        axes[1, 1].set_ylabel('Cumulative Avg Reward')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('demo_training_curves.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _generate_demo_rewards(self, episodes):
        """Tạo dữ liệu demo để minh họa"""
        # Tạo rewards với xu hướng tăng dần và noise
        base_rewards = np.linspace(-10, 30, episodes)
        noise = np.random.normal(0, 5, episodes)
        spikes = np.random.poisson(0.1, episodes) * np.random.uniform(10, 50, episodes)
        
        rewards = base_rewards + noise + spikes
        return rewards
    
    def _calculate_moving_average(self, data, window):
        """Tính moving average"""
        return np.convolve(data, np.ones(window)/window, mode='valid')
    
    def _print_summary_stats(self, data):
        """In thống kê tóm tắt"""
        print("\n" + "="*60)
        print("TRAINING SUMMARY STATISTICS")
        print("="*60)
        print(f"Total Episodes: {len(data['episode_rewards'])}")
        print(f"Average Reward: {np.mean(data['episode_rewards']):.2f} ± {np.std(data['episode_rewards']):.2f}")
        print(f"Average Score: {np.mean(data['episode_scores']):.2f} ± {np.std(data['episode_scores']):.2f}")
        print(f"Best Score: {data.get('best_score', 0)}")
        print(f"Best Reward: {data.get('best_reward', 0):.2f}")
        print(f"Win Rate: {data.get('win_rate', 0)*100:.1f}%")
        print(f"Death Rate: {data.get('death_rate', 0)*100:.1f}%")
        print(f"Timeout Rate: {data.get('timeout_rate', 0)*100:.1f}%")
        
        # Recent performance
        if len(data['episode_rewards']) > 100:
            recent_rewards = data['episode_rewards'][-100:]
            print(f"Recent 100 Episodes Avg: {np.mean(recent_rewards):.2f}")
        
        print("="*60)

def main():
    """Main function để chạy plotting"""
    plotter = RewardCurvePlotter()
    
    print("REWARD CURVE PLOTTING TOOL")
    print("="*50)
    print("1. Plot from training data file")
    print("2. Plot demo curves")
    print("3. Plot from Q-table")
    
    choice = input("\nChọn option (1-3): ").strip()
    
    if choice == '1':
        data_file = input("Nhập tên file training data (Enter để dùng file mới nhất): ").strip()
        if not data_file:
            data_file = None
        plotter.plot_from_training_data(data_file)
    elif choice == '2':
        episodes = int(input("Nhập số episodes cho demo (default 1000): ") or "1000")
        plotter.plot_demo_curves(episodes)
    elif choice == '3':
        q_file = input("Nhập tên file Q-table (default q_table.json): ").strip() or "q_table.json"
        plotter.plot_from_q_table(q_file)
    else:
        print("Invalid choice!")
        plotter.plot_demo_curves()

if __name__ == "__main__":
    main()
