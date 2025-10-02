import pygame
import sys
import time
import csv
import json
from datetime import datetime
from engine.game import Game
from constants import *

class QLearningTrainer:
    def __init__(self, 
                 max_episodes=1000,
                 save_interval=50,
                 max_steps_per_episode=2000,
                 render=True,
                 few_pellets_mode=False,
                 few_pellets_count=30):
        self.max_episodes = max_episodes
        self.save_interval = save_interval
        self.max_steps_per_episode = max_steps_per_episode
        self.render = render
        self.few_pellets_mode = few_pellets_mode
        self.few_pellets_count = few_pellets_count

        self.episode_rewards = []
        self.episode_steps = []
        self.episode_scores = []
        self.episode_epsilons = []  
        self.episode_deaths = []   
        self.best_score = 0
        self.timeout_count = 0
        self.win_count = 0    
        self.death_count = 0   

        pygame.init()
        self.screen = pygame.display.set_mode(SCREENSIZE)
        pygame.display.set_caption("Q-Learning Training" + (" [Headless]" if not self.render else ""))
        self.clock = pygame.time.Clock() if self.render else None

    def print_train(self):
        print("=" * 60)
        print("STARTING Q-LEARNING TRAINING")
        print("=" * 60)
        print(f"Max Episodes: {self.max_episodes}")
        print(f"Max Steps per Episode: {self.max_steps_per_episode}")
        print(f"Save Interval: {self.save_interval}")
        print(f"Render: {self.render}")
        print(f"Few Pellets Mode: {self.few_pellets_mode}")
        if self.few_pellets_mode:
            print(f"Pellet Count: {self.few_pellets_count}")
        print("=" * 60)
    
    def train(self):
        self.print_train()
        for episode in range(1, self.max_episodes + 1):
            print(f"\n{'='*60}")
            print(f"EPISODE {episode}/{self.max_episodes}")
            print(f"{'='*60}")
            
            episode_reward, episode_step, final_score, episode_result, current_epsilon = self.run_episode(episode)
            
            self.episode_rewards.append(episode_reward)
            self.episode_steps.append(episode_step)
            self.episode_scores.append(final_score)
            self.episode_epsilons.append(current_epsilon)
            self.episode_deaths.append(episode_result)  
            
            if episode_result == 'win':
                self.win_count += 1
            elif episode_result == 'death':
                self.death_count += 1
            
            if final_score > self.best_score:
                self.best_score = final_score
                print(f"   NEW BEST SCORE: {self.best_score}!")
            
            print(f"\nEPISODE {episode} SUMMARY:")
            print(f"   Total Reward: {episode_reward:.2f}")
            print(f"   Steps Taken: {episode_step}")
            print(f"   Final Score: {final_score}")
            print(f"   Best Score Ever: {self.best_score}")
            
            if episode % self.save_interval == 0:
                self.save_model(episode)
        
        print("\n" + "=" * 60)
        print("TRAINING COMPLETED!")
        print("=" * 60)
        self.save_model(self.max_episodes, final=True)
        
        pygame.quit()

    def run_episode(self, episode_num):
        print(f"Creating new game for episode {episode_num}")
        game = Game(algorithm='Q-Learning')
        game.screen = self.screen if self.render else None

        game.ai_mode = True
        game.ghost_mode = True  
        game.few_pellets_mode = self.few_pellets_mode
        game.few_pellets_count = self.few_pellets_count
        game.initialize_game()

        game.pacman.set_q_learning(True)
        game.pacman.hybrid_ai.set_training_mode(True)
        game.pacman.hybrid_ai.init_q_learning()
        
        # Load Q-table từ file trước đó
        if hasattr(game.pacman, 'hybrid_ai'):
            if hasattr(game.pacman.hybrid_ai, 'q_agent'):
                try:
                    game.pacman.hybrid_ai.q_agent.load('q_table.json')
                    print(f"SUCCESS: Loaded Q-table for episode {episode_num}")
                except:
                    print(f"NEW: Fresh Q-table for episode {episode_num}")
        
        self.last_game = game
            
       

        if hasattr(game.pacman, 'hybrid_ai'):
            if hasattr(game.pacman.hybrid_ai, 'init_q_learning'):
                game.pacman.hybrid_ai.init_q_learning()
            
            if hasattr(game.pacman.hybrid_ai, 'q_agent'):
                if episode_num <= 200:
                    epsilon = 0.9
                elif episode_num <= 400:
                    epsilon = 0.7
                elif episode_num <= 600:
                    epsilon = 0.5
                elif episode_num <= 800:
                    epsilon = 0.3
                else:
                    epsilon = 0.1
        
        self.last_game = game
        total_reward = 0
        steps = 0
        episode_result = 'timeout'  
        current_epsilon = 0.0
        
        if hasattr(game.pacman, 'hybrid_ai'):
            if hasattr(game.pacman.hybrid_ai, 'q_agent'):
                current_epsilon = game.pacman.hybrid_ai.q_agent.epsilon
        
        game.pause.paused = False
        
        while game.running and steps < self.max_steps_per_episode:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            game.update()
            
            if self.render:
                game.render(self.screen)
                pygame.display.update()
                if self.clock:
                    self.clock.tick(60)  
            
            steps += 1
            
            if not game.pacman.alive:
                episode_result = 'death'
                print(f"   Pacman died at step {steps}")
                break
            
            pellets_left = len([p for p in game.pellets.pelletList if p.visible])
            if pellets_left == 0:
                episode_result = 'win'
                print(f"   Level completed at step {steps}!")
                break
        
        if steps >= self.max_steps_per_episode:
            self.timeout_count += 1
            episode_result = 'timeout'
        final_score = game.score
        return total_reward, steps, final_score, episode_result, current_epsilon
    
    def save_model(self, episode, final=False):
        game = self.last_game
        filename = 'q_table.json'
        game.pacman.hybrid_ai.q_agent.save(filename)
        print(f"Saved Q-table to {filename}")
        return

if __name__ == "__main__":
    print("\nQ-LEARNING TRAINING FOR PACMAN")
    print("=" * 60)
    
    config = {
        'max_episodes': 2000,            
        'save_interval': 20,              
        'max_steps_per_episode': 2000,    
        'render': True,                
        'few_pellets_mode': False,       
        'few_pellets_count': 30           
    }
    
    print("TRAINING CONFIGURATION:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    print("=" * 60)
    
    trainer = QLearningTrainer(**config)
    trainer.train()
