# =============================================================================
# PLAYER.PY - CLASS PAC-MAN CHO GAME PAC-MAN
# =============================================================================
# File này chứa class Pacman - nhân vật chính của game
# Hỗ trợ cả chế độ điều khiển thủ công và AI tự động

import pygame
from pygame.locals import * 
from constants import *
from objects.vector import Vector2
from objects.entity import Entity
from ui.sprites import PacmanScriptes
from objects.pellets import PelletGroup
from objects.nodes import Node
from collections import deque
from engine.a_star import a_star
import sys

class Pacman(Entity):
    """
    Class Pacman - nhân vật chính của game
    - Kế thừa từ Entity để có khả năng di chuyển cơ bản
    - Hỗ trợ cả điều khiển thủ công và AI tự động
    - Sử dụng A* algorithm để tìm đường đến pellet
    - Có hệ thống pathfinding thông minh với target locking
    """
    def __init__(self, node):
        """
        Khởi tạo Pac-Man tại node
        Args:
            node: Node khởi đầu của Pac-Man
        """
        Entity.__init__(self, node) 
        self.name = PACMAN  # ID của Pac-Man
        self.color = YELLOW  # Màu vàng đặc trưng
        self.direction = LEFT  # Hướng di chuyển ban đầu
        self.setBetweenNodes(LEFT)  # Đặt ở giữa 2 node
        self.alive = True  # Trạng thái sống/chết
        self.sprites = PacmanScriptes(self)  # Hệ thống sprite animation
        
        # Hệ thống AI pathfinding
        self.path = []  # Đường đi đã tính toán
        self.locked_target_node = None  # Node mục tiêu đã khóa
        self.previous_node = None  # Node trước đó (để tránh backtracking)
    
    def reset(self):
        """
        Khôi phục Pac-Man về trạng thái ban đầu
        - Gọi reset của Entity base class
        - Reset tất cả thuộc tính về giá trị mặc định
        """
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
        
    def set_path(self, path):
        """
        Thiết lập đường đi cho Pac-Man
        Args:
            path: List các node tạo thành đường đi
        """
        self.path = path[1:]  # Bỏ qua node đầu tiên (node hiện tại)
    
    def get_direction(self, from_node, to_node):
        """
        Lấy hướng di chuyển từ node này sang node khác
        Args:
            from_node: Node xuất phát
            to_node: Node đích
        Returns:
            Hướng di chuyển (UP, DOWN, LEFT, RIGHT, PORTAL) hoặc STOP
        """
        for direction, neighbor in from_node.neighbors.items():
            if neighbor == to_node:
                return direction
        return STOP
    
    def die(self):
        """
        Xử lý khi Pac-Man bị chết
        - Đặt trạng thái alive = False
        - Dừng di chuyển
        """
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
    
    def update_ai(self, dt, pelletGroup=None, auto=False):
        """
        Cập nhật Pac-Man với AI pathfinding
        - Sử dụng A* algorithm để tìm đường đến pellet
        - Có hệ thống target locking để tránh thay đổi mục tiêu liên tục
        - Xử lý pathfinding thông minh với backtracking prevention
        
        Args:
            dt: Delta time
            pelletGroup: Nhóm pellets còn lại trong game
            auto: Có sử dụng AI tự động không
        """
        # Cập nhật animation và di chuyển
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        direction = self.direction 

        if self.overshotTarget():
            # Đã đến target node
            self.previous_node = self.node
            self.node = self.target
            
            # Xử lý portal nếu có
            if self.node.neighbors[PORTAL] is not None: 
                self.node = self.node.neighbors[PORTAL] 
                
            # AI pathfinding logic
            if auto and pelletGroup is not None and pelletGroup.pelletList:
                # Sử dụng BFS cải tiến với ưu tiên hướng hiện tại
                priority_direction = self.direction if self.direction != STOP else None
                
                # Kiểm tra target hiện tại còn hợp lệ không
                if (self.locked_target_node is None or 
                    not any(p.node == self.locked_target_node for p in pelletGroup.pelletList)):
                    self.locked_target_node = None
                    # Tìm pellet gần nhất
                    path = a_star(self.node, None, pelletGroup)
                    if path and len(path) > 0:
                        self.locked_target_node = path[-1]
                
                # Tính toán đường đi mới nếu chưa có
                if not self.path:
                    path = a_star(self.node, self.locked_target_node, pelletGroup)
                    if path:
                        self.set_path(path)
                
                # Chọn bước tiếp theo từ path
                direction = self.move_along_path()
                
                # Xử lý trường hợp bị chặn hoặc không hợp lệ
                attempts = 0
                while ((direction == STOP or 
                       self.getNewTarget(direction) is self.node) and 
                       attempts < 2):
                    if self.path:
                        # Bỏ qua bước này và thử bước tiếp theo
                        self.path.pop(0)
                        direction = self.move_along_path()
                    else:
                        break
                    attempts += 1
                    
                # Replan nếu cần thiết
                if direction == STOP or self.getNewTarget(direction) is self.node:
                    self.path = []
                    path = a_star(self.node, self.locked_target_node, pelletGroup)
                    if path:
                        self.set_path(path)
                        direction = self.move_along_path()
                        
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
            # Xử lý đảo ngược hướng khi không auto
            if not auto and self.oppositeDirection(direction):
                self.reverseDirection()
                
    def update(self, dt):
        """
        Cập nhật Pac-Man với điều khiển thủ công
        - Đọc input từ keyboard
        - Xử lý di chuyển và portal
        - Cập nhật vị trí và animation
        
        Args:
            dt: Delta time
        """
        # Cập nhật animation và di chuyển
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        direction = self.getValidKey()  # Lấy input từ keyboard

        if self.overshotTarget():
            # Đã đến target node
            self.node = self.target
            
            # Xử lý portal nếu có
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
            # Xử lý đảo ngược hướng
            if self.oppositeDirection(direction):
                self.reverseDirection()
    
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
        """
        Kiểm tra và ăn pellets
        - Duyệt qua danh sách pellets
        - Kiểm tra va chạm với từng pellet
        - Trả về pellet đầu tiên bị va chạm
        
        Args:
            pelletList: Danh sách pellets cần kiểm tra
            
        Returns:
            Pellet bị ăn hoặc None nếu không có
        """
        for pellet in pelletList: 
            if self.collideCheck(pellet): 
                return pellet
        return None 
    
    def collideGhost(self, ghost):
        """
        Kiểm tra va chạm với ghost
        Args:
            ghost: Ghost cần kiểm tra va chạm
        Returns:
            True nếu va chạm, False nếu không
        """
        return self.collideCheck(ghost) 

    def collideCheck(self, other):
        """
        Kiểm tra va chạm với đối tượng khác
        - Sử dụng collision detection dựa trên khoảng cách
        - So sánh tổng bán kính với khoảng cách thực tế
        
        Args:
            other: Đối tượng cần kiểm tra va chạm
        Returns:
            True nếu va chạm, False nếu không
        """
        # Tính vector khoảng cách
        d = self.position - other.position 
        dSquared = d.magnitudeSquared()  # Bình phương khoảng cách
        
        # Tính tổng bán kính collision
        rSquared = (self.collideRadius + other.collideRadius) ** 2
        
        # Kiểm tra va chạm
        if dSquared <= rSquared:
            return True
        return False  