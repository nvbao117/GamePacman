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
    bfs, dfs, a_star, ucs, iterative_deepening_dfs, greedy
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
        self.pathfinder_name = 'BFS'
        self.pathfinder = bfs
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
        
    def set_path(self, path):
        self.path = path[1:]  # Bỏ qua node đầu tiên (node hiện tại)
    
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
            
    def get_direction(self, from_node, to_node):
        """
        Lấy hướng di chuyển từ node này sang node khác
        Hướng di chuyển (UP, DOWN, LEFT, RIGHT, PORTAL) hoặc STOP
        """
        for direction, neighbor in from_node.neighbors.items():
            if neighbor == to_node:
                return direction
        return STOP
    
    def die(self):
        self.alive = False
        self.direction = STOP 

    def move_along_path(self):
        """
        Di chuyển Pac-Man theo đường đi đã tính toán
        - Xử lý backtracking để tránh ping-pong
        - Kiểm tra hướng hợp lệ
        - Cập nhật path khi đến node mới
        Returns:
            Hướng di chuyển tiếp theo hoặc STOP
        """
        if not self.path:
            return STOP
            
        # Tránh backtracking ngay lập tức (ping-pong effect)
        if (self.previous_node is not None and 
            len(self.path) >= 1 and 
            self.path[0] == self.previous_node):
            
            if len(self.path) > 1:
                # Ưu tiên bỏ qua bước quay lại nếu có bước khác
                self.path.pop(0)
            else:
                # Dead-end: cho phép quay lại 1 bước để thoát
                direction_back = self.get_direction(self.node, self.previous_node)
                return direction_back if direction_back != STOP else STOP
                
        # Lấy node tiếp theo và hướng di chuyển
        next_node = self.path[0]
        direction = self.get_direction(self.node, next_node)
        
        if direction == STOP:
            self.path = []
            return STOP
            
        # Không cho phép đảo ngược hướng giữa chừng khi auto
        opposite = self.oppositeDirection(direction)
        if opposite and self.direction == opposite:
            return self.direction
            
        # Nếu đã đến node tiếp theo, xóa khỏi path
        if self.overshotTarget() and self.node == next_node:
            self.path.pop(0)
            
        return direction
    
    def update_ai(self, dt, pelletGroup=None, auto=False, ghostGroup=None):
        """
        Cập nhật Pac-Man với AI pathfinding - HỖ TRỢ HYBRID AI
        
        Có 3 chế độ AI:
        1. TRADITIONAL: Sử dụng compute-once system (BFS, DFS, A*, etc.)
        2. HYBRID: Kết hợp offline planning + online decision-making
        
        Args:
            dt: Delta time
            pelletGroup: Nhóm pellets còn lại trong game
            auto: Có sử dụng AI tự động không
            ghostGroup: Nhóm ghosts (cho hybrid AI)
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
    
    def get_ai_status(self):
        """Lấy thông tin trạng thái AI"""
        if self.use_hybrid_ai:
            return self.hybrid_ai.get_status_info()
        else:
            return {
                "ai_type": "Traditional",
                "algorithm": self.pathfinder_name,
                "hybrid_enabled": False
            }
    
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
    
    def set_precomputed_path(self, path):
        """
        Thiết lập path đã được tính sẵn từ AI algorithms
        """
        if path and len(path) > 1:
            self.precomputed_path = path[1:] 
            self.path_index = 0
        else:
            self.precomputed_path = []
            self.path_index = 0
    
    def _follow_precomputed_path(self, pelletGroup):
        """
        Follow path đã được tính sẵn từ AI algorithms
        Args:
            pelletGroup: Nhóm pellets còn lại
        Returns:
            direction: Hướng di chuyển tiếp theo
        """
        # Kiểm tra xem có path không
        if not self.precomputed_path or self.path_index >= len(self.precomputed_path):
            # Hết path hoặc chưa có path -> compute new path
            return self._compute_new_path_if_needed(pelletGroup)
        
        # Lấy node tiếp theo từ path
        target_node = self.precomputed_path[self.path_index]
        
        # Kiểm tra nếu đã ở target node, advance path
        if self.node == target_node:
            self.path_index += 1
            remaining = len(self.precomputed_path) - self.path_index
            if remaining % 50 == 0:
                pass
            
            # Lấy target mới sau khi advance
            if self.path_index < len(self.precomputed_path):
                target_node = self.precomputed_path[self.path_index]
            else:
                # Hết path
                return self._compute_new_path_if_needed(pelletGroup)
        
        # Tìm direction đến target node
        direction = self._get_direction_to_node(self.node, target_node)
        
        # Nếu không thể di chuyển, thử skip ahead
        if direction == STOP:
            return self._handle_blocked_path(pelletGroup)
        
        return direction
    
    def _compute_new_path_if_needed(self, pelletGroup):
        """
        Compute path mới khi cần thiết
        """
        if not pelletGroup or not pelletGroup.pelletList:
            return STOP
        
        # Tính path mới khi cần thiết
        
        try:
            # Gọi AI algorithm để tính path
            new_path = self.pathfinder(self.node, None, pelletGroup)
            
            if new_path and len(new_path) > 1:
                self.set_precomputed_path(new_path)
                return self._follow_precomputed_path(pelletGroup)
            else:
                return self._greedy_fallback(pelletGroup)
                
        except Exception:
            return self._greedy_fallback(pelletGroup)
    
    def _handle_blocked_path(self, pelletGroup):
        """
        Xử lý khi path bị block
        """
        # Path bị block: thử skip ahead
        
        # Thử skip 1-3 bước trong path
        for skip in range(1, min(4, len(self.precomputed_path) - self.path_index)):
            if self.path_index + skip < len(self.precomputed_path):
                next_target = self.precomputed_path[self.path_index + skip]
                direction = self._get_direction_to_node(self.node, next_target)
                
                if direction != STOP:
                    self.path_index += skip
                    return direction
        
        # Không thể skip -> compute new path
        self.precomputed_path = []
        self.path_index = 0
        return self._compute_new_path_if_needed(pelletGroup)
    
    def _get_direction_to_node(self, from_node, to_node):
        """
        Tìm direction từ from_node đến to_node
        """
        if not from_node or not to_node:
            return STOP
        
        for direction, neighbor in from_node.neighbors.items():
            if neighbor == to_node:
                # Kiểm tra xem có thể di chuyển không
                if direction == PORTAL:
                    return direction
                elif PACMAN in from_node.access[direction]:
                    return direction
        
        return STOP
    
    def _greedy_fallback(self, pelletGroup):
        """
        Greedy fallback khi không có path
        """
        if not pelletGroup or not pelletGroup.pelletList:
            return STOP
        
        # Tìm pellet gần nhất
        pellet_nodes = [p.node for p in pelletGroup.pelletList if p.node and p.visible]
        if not pellet_nodes:
            return STOP
        
        nearest_pellet = min(pellet_nodes, 
                           key=lambda p: self._manhattan_distance(self.node, p))
        
        # Di chuyển về phía pellet gần nhất
        best_direction = STOP
        min_distance = float('inf')
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = self.node.neighbors.get(direction)
            if neighbor:
                can_move = (direction == PORTAL or 
                           PACMAN in self.node.access[direction])
                
                if can_move:
                    distance = self._manhattan_distance(neighbor, nearest_pellet)
                    if distance < min_distance:
                        min_distance = distance
                        best_direction = direction
        
        return best_direction
    
    def _manhattan_distance(self, node1, node2):
        if not node1 or not node2:
            return float('inf')
        
        dx = abs(node1.position.x - node2.position.x)
        dy = abs(node1.position.y - node2.position.y)
        return dx + dy
    
    def get_path_info(self):
        """
        Lấy thông tin về path hiện tại
        """
        if not self.precomputed_path:
            return "No precomputed path"
        
        total_steps = len(self.precomputed_path)
        current_step = self.path_index
        remaining_steps = total_steps - current_step
        progress_percent = (current_step / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            'algorithm': self.pathfinder_name,
            'total_steps': total_steps,
            'current_step': current_step,
            'remaining_steps': remaining_steps,
            'progress_percent': progress_percent,
            'is_completed': current_step >= total_steps
        }  