# =============================================================================
# PLAYER.PY - CLASS PAC-MAN CHO GAME PAC-MAN
# =============================================================================

import pygame
from pygame.locals import * 
from constants import *
from objects.vector import Vector2
from objects.entity import Entity
from ui.sprites import PacmanScriptes
from objects.pellets import PelletGroup
from objects.nodes import Node
from collections import deque
import sys
from engine.algorithms_practical import (
    bfs, dfs, astar, ucs, ids, greedy
)
from engine.compute_once_system import compute_once
from engine.hybrid_ai_system import HybridAISystem

class Pacman(Entity):
    """
    Kế thừa từ Entity để có khả năng di chuyển cơ bản
    
    Chức năng:
    - Điều khiển thủ công bằng bàn phím (UP, DOWN, LEFT, RIGHT)
    - Điều khiển tự động bằng các thuật toán AI
    - Hỗ trợ 6 thuật toán AI: BFS, DFS, A*, UCS, IDS, Greedy
    - Sử dụng compute-once system để tối ưu performance
    - Theo dõi analytics (position, steps, score, path info)
    - Xử lý va chạm với pellets, fruits, và ghosts
    """
    def __init__(self, node):
        Entity.__init__(self, node) 
        self.name = PACMAN 
        self.color = YELLOW 
        self.direction = LEFT 
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanScriptes(self)  
        
        # Hệ thống AI pathfinding
        self.path = []  # Đường đi đã tính toán
        self.locked_target_node = None  # Node mục tiêu đã khóa
        self.previous_node = None  # Node trước đó (để tránh backtracking)
        
        # Thuật toán AI pathfinding (có thể thay đổi)
        self.pathfinder_name = 'BFS'  # Tên thuật toán hiện tại
        self.pathfinder = bfs  # Function thuật toán
        
        # Lưu trữ thuật toán gốc để không bị reset
        self.original_pathfinder_name = 'BFS'
        self.original_pathfinder = bfs 
        
        # Timer để tránh gọi pathfinding quá thường xuyên
        self.last_pathfind_time = 0
        self.pathfind_interval = 0.5  # Gọi pathfinding tối đa mỗi 0.5 giây
        self._update_pathfind_interval()  # Cập nhật interval dựa trên thuật toán
        
        # Flag để kiểm tra đã tính toán path chưa
        self.path_computed = False
        self.original_pellet_count = 0
        
        # Hybrid AI System
        self.hybrid_ai = HybridAISystem(self)
        self.use_hybrid_ai = False  # Flag để bật/tắt hybrid AI
        
        # Stuck detection
        self.stuck_counter = 0
        self.last_position = None
        
        # Precomputed path system
        self.precomputed_path = []  # Path from AI algorithms
        self.path_index = 0 
    
    def reset(self):
        Entity.reset(self) 
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()
        self.target_pellet = None
        self.path = []
        self.locked_target_node = None
        self.previous_node = None
        # Không reset thuật toán - giữ nguyên thuật toán đã chọn
        # self.pathfinder_name = 'BFS'
        # self.pathfinder = bfs
        self.last_pathfind_time = 0
        self._update_pathfind_interval()
        self.path_computed = False
        self.original_pellet_count = 0
        
        self.stuck_counter = 0
        self.last_position = None
        
        # Reset compute-once system
        compute_once.reset()
        
        # Reset precomputed path
        self.precomputed_path = []
        self.path_index = 0
        
        # Không reset thuật toán - giữ nguyên thuật toán đã chọn
        # self.pathfinder_name = self.original_pathfinder_name
        # self.pathfinder = self.original_pathfinder
        
    def _update_pathfind_interval(self):
        """
        Cập nhật interval pathfinding dựa trên thuật toán được sử dụng
        - BFS: Interval dài hơn vì tính toán phức tạp
        - A*: Interval trung bình
        - DFS, UCS: Interval ngắn hơn
        """
        if hasattr(self, 'pathfinder_name'):
            if self.pathfinder_name == 'BFS':
                self.pathfind_interval = 1.0  # 1 giây cho BFS
            elif self.pathfinder_name == 'A*':
                self.pathfind_interval = 0.7  # 0.7 giây cho A*
            elif self.pathfinder_name == 'IDS':
                self.pathfind_interval = 0.8  # 0.8 giây cho IDS
            else:  # DFS, UCS
                self.pathfind_interval = 0.3  # 0.3 giây cho DFS, UCS
        
    def force_recompute_path(self):
        """
        Buộc tính lại path ngay lập tức với heuristic mới
        """
        # Reset tất cả pathfinding state
        self.path = []
        self.locked_target_node = None
        self.previous_node = None
        self.path_computed = False
        
        # Reset precomputed path system nếu có
        if hasattr(self, 'precomputed_path'):
            self.precomputed_path = []
            self.path_index = 0
    
    def die(self):
        self.alive = False
        self.direction = STOP 

    def update_ai(self, dt, pelletGroup=None, auto=False, ghostGroup=None):
        """
        Cập nhật Pac-Man với AI pathfinding
        """
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        direction = self.direction 

        if self.overshotTarget():
            self.previous_node = self.node
            self.node = self.target
            
            if self.node.neighbors[PORTAL] is not None: 
                self.node = self.node.neighbors[PORTAL] 
                
            # In vị trí khi Pacman đến node mới
            if auto and pelletGroup is not None and pelletGroup.pelletList:
                print(f"({int(self.position.x//16)}, {int(self.position.y//16)})",end=" ")
                
            # AI logic: Chọn giữa traditional và hybrid AI
            if auto and pelletGroup is not None and pelletGroup.pelletList:
                if self.use_hybrid_ai:
                    direction = self.hybrid_ai.get_direction(pelletGroup, ghostGroup)
                else:
                    print(self.pathfinder_name)
                    print(self.pathfinder)
                    direction = compute_once.get_direction(
                        self, pelletGroup, self.pathfinder, self.pathfinder_name
                    )
                        
            self.target = self.getNewTarget(direction)              
            if self.target is not self.node: 
                self.direction = direction
            else: 
                self.target = self.getNewTarget(self.direction)
            if self.target is self.node: 
                self.direction = STOP             
            self.setPosition()

        else:
            # Xử lý đảo ngược hướng khi không auto
            if not auto and self.oppositeDirection(direction):
                self.reverseDirection()
                
    def update(self, dt):
        """
        Cập nhật Pac-Man với điều khiển thủ công
        - Đọc input từ keyboard
        - Xử lý di chuyển và portal
        - Cập nhật vị trí và animation
        """
        # Cập nhật animation và di chuyển
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        direction = self.getValidKey()  # Lấy input từ keyboard

        if self.overshotTarget():
            self.node = self.target
            
            if self.node.neighbors[PORTAL] is not None:
                self.node = self.node.neighbors[PORTAL]
                
            # Cập nhật target và direction
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)

            if self.target is self.node:
                self.direction = STOP
            self.setPosition()
        else: 
            if self.oppositeDirection(direction):
                self.reverseDirection()
    
    def enable_hybrid_ai(self):
        self.use_hybrid_ai = True
    
    def disable_hybrid_ai(self):
        self.use_hybrid_ai = False
    
    def toggle_hybrid_ai(self):
        """Chuyển đổi Hybrid AI on/off"""
        self.use_hybrid_ai = not self.use_hybrid_ai
        status = "enabled" if self.use_hybrid_ai else "disabled"
    
    def set_algorithm(self, algorithm_name, algorithm_func):
        """Cập nhật thuật toán AI và lưu trữ để không bị reset"""
        self.pathfinder_name = algorithm_name
        self.pathfinder = algorithm_func
        self.original_pathfinder_name = algorithm_name
        self.original_pathfinder = algorithm_func
        self._update_pathfind_interval()
    
    def getValidKey(self):
        """
        Lấy phím được nhấn từ keyboard
        - Kiểm tra các phím mũi tên
        - Trả về hướng di chuyển tương ứng
        
        Returns:
            Hướng di chuyển (UP, DOWN, LEFT, RIGHT) hoặc STOP
        """
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_UP]: 
            return UP 
        if key_pressed[K_DOWN]: 
            return DOWN
        if key_pressed[K_LEFT]:
            return LEFT
        if key_pressed[K_RIGHT]:
            return RIGHT
        return STOP
    
    def eatPellets(self, pelletList):
        for pellet in pelletList: 
            if self.collideCheck(pellet): 
                return pellet
        return None 
    
    def collideGhost(self, ghost):
        """
        Kiểm tra va chạm với ghost
        """
        return self.collideCheck(ghost) 

    def collideCheck(self, other):
        """
        Kiểm tra va chạm với đối tượng khác
        - Sử dụng collision detection dựa trên khoảng cách
        - So sánh tổng bán kính với khoảng cách thực tế
        """
        d = self.position - other.position 
        dSquared = d.magnitudeSquared()  
        
        rSquared = (self.collideRadius + other.collideRadius) ** 2
        
        if dSquared <= rSquared:
            return True
        return False
    
    
    
    