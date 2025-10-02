#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEADLESS Q-LEARNING TRAINING FOR UBUNTU CLI
============================================
Script để train Q-Learning trên Ubuntu server không có GUI
"""

import os
import sys

# Thiết lập headless mode TRƯỚC KHI import pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from optimized_training import OptimizedQLearningTrainer

def main():
    """
    Main training function cho Ubuntu CLI
    """
    print("=" * 80)
    print("STARTING HEADLESS Q-LEARNING TRAINING")
    print("=" * 80)
    print()
    
    # Configuration
    config = {
        'max_episodes': 3000,           # Số episodes
        'save_interval': 50,            # Lưu mỗi 50 episodes
        'max_steps_per_episode': 2500,  # Max steps mỗi episode
        'render': False,                # KHÔNG render (headless)
        'few_pellets_mode': False,      # Full pellets
        'few_pellets_count': 30,        # Nếu few_pellets_mode = True
        'adaptive_learning': True,      # Adaptive epsilon
        'performance_window': 100       # Window size cho tracking
    }
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # Tạo trainer
    trainer = OptimizedQLearningTrainer(**config)
    
    try:
        # Bắt đầu training
        trainer.train()
        
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("TRAINING INTERRUPTED BY USER")
        print("=" * 80)
        
        # Save progress
        if hasattr(trainer, 'last_game') and trainer.last_game:
            print("Saving current progress...")
            if hasattr(trainer.last_game.pacman, 'hybrid_ai'):
                hybrid_ai = trainer.last_game.pacman.hybrid_ai
                if hasattr(hybrid_ai, 'q_agent'):
                    hybrid_ai.q_agent.save('q_table_interrupted.json')
                    print("✓ Saved Q-table to: q_table_interrupted.json")
        
        # Save stats
        trainer.save_training_stats('interrupted')
        print("✓ Saved training statistics")
        
    except Exception as e:
        print(f"\n{'=' * 80}")
        print(f"ERROR DURING TRAINING: {e}")
        print(f"{'=' * 80}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n" + "=" * 80)
        print("TRAINING SESSION ENDED")
        print("=" * 80)
        print("\nCheck output files:")
        print("  - q_table.json (Q-table data)")
        print("  - training_stats/*.json (statistics)")
        print("  - reward_images/*.png (reward plots)")

if __name__ == "__main__":
    main()

