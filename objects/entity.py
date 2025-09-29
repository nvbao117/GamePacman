# =============================================================================
# ENTITY.PY - BASE CLASS CHO TẤT CẢ ENTITY TRONG GAME PAC-MAN
# =============================================================================
# File này chứa class Entity cơ bản cho tất cả đối tượng có thể di chuyển
# trong game như Pac-Man, Ghost, Fruit, v.v.

import pygame 
from pygame.locals import * 
from random import randint
from objects.vector import Vector2
from constants import *

class Entity(object):
    """
    Base class cho tất cả entity có thể di chuyển trong game
    - Quản lý vị trí, hướng di chuyển, tốc độ
    - Xử lý di chuyển dựa trên node system
    - Hỗ trợ collision detection và rendering
    """
    def __init__(self, node):
        """
        Khởi tạo entity với node khởi đầu
        Args:
            node: Node khởi đầu của entity
        """
        self.name = None  # ID của entity (PACMAN, GHOST, v.v.)
        
        # Dictionary chứa vector hướng di chuyển cho mỗi direction
        self.directions = {
            UP:Vector2(0,-1) , 
            DOWN:Vector2(0,1) ,
            LEFT:Vector2(-1,0),
            RIGHT:Vector2(1,0),
            STOP:Vector2()
        }
        
        self.direction = STOP        # Hướng di chuyển hiện tại
        self.setSpeed(100)          # Tốc độ di chuyển (pixel/second)
        self.radius = 10            # Bán kính vẽ entity
        self.collideRadius = 5      # Bán kính collision detection
        self.color = WHITE          # Màu vẽ entity
        self.visible = True         # Có hiển thị entity không
        self.disablePortal = False  # Có sử dụng portal không
        self.goal = None            # Mục tiêu di chuyển (cho AI)
        self.directionMethod = self.randomDirection  # Phương thức chọn hướng
        self.setStartNode(node)     # Đặt node khởi đầu
        self.image = None           # Hình ảnh entity (nếu có)
             
    def setPosition(self): 
        """
        Đặt vị trí entity tại vị trí của node hiện tại
        """
        self.position = self.node.position.copy() 
        
    def update(self, dt): 
        """
        Cập nhật vị trí entity mỗi frame
        Args:
            dt: Delta time (thời gian giữa 2 frame)
        """
        # Di chuyển entity theo hướng và tốc độ
        self.position += self.directions[self.direction] * self.speed * dt
        
        if self.overshotTarget():
            # Đã đến target, chuyển sang node mới
            self.node = self.target 
            directions = self.validDirections()
            direction = self.directionMethod(directions)
            if not self.disablePortal:
                if self.node.neighbors[PORTAL] is not None: 
                    self.node = self.node.neighbors[PORTAL] 
            
            # Đặt target mới
            self.target = self.getNewTarget(direction) 
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)
                
            self.setPosition()
    
    #kiểm tra hướng di chuyển hợp lệ     
    def validDirection(self, direction):
        if direction is not STOP:
            # Kiểm tra entity có quyền truy cập hướng này không
            access_list = self.node.access.get(direction)
            if access_list and self.name in access_list:
                if self.node.neighbors[direction] is not None:
                    return True
        return False
    
    def getNewTarget(self, direction):
        """
        Lấy node mục tiêu mới theo hướng
        Args:
            direction: Hướng di chuyển
        Returns:
            Node mục tiêu hoặc node hiện tại nếu không hợp lệ
        """
        if self.validDirection(direction): 
            return self.node.neighbors[direction] 
        return self.node 
    
    #Kiểm tra xem có vượt quá target không 
    def overshotTarget(self):
        if self.target is not None :
            vec1 = self.target.position - self.node.position 
            vec2 = self.position - self.node.position 
            
            # So sánh độ dài (dùng magnitudeSquared để tránh sqrt)
            node2Target = vec1.magnitudeSquared()
            node2Self = vec2.magnitudeSquared()
            return node2Self >= node2Target
        return False
    
    def reverseDirection(self):
        self.direction *= -1 
        temp = self.node 
        self.node = self.target
        self.target = temp 
    
    def oppositeDirection(self, direction):
        """
        Kiểm tra xem hướng có ngược với hướng hiện tại không
        Args:
            direction: Hướng cần kiểm tra
        Returns:
            True nếu ngược hướng
        """
        if direction is not STOP: 
            if direction == self.direction * -1: 
                return True 
        return False 
    
    def validDirections(self):
        """
        Lấy danh sách các hướng di chuyển hợp lệ
        Returns:
            List các hướng có thể di chuyển
        """
        directions = [] 
        for key in [UP,DOWN,LEFT,RIGHT]  :
            if self.validDirection(key) : 
                if key != self.direction * -1 :
                    directions.append(key)
        
        # Nếu không có hướng nào, cho phép quay ngược lại
        if len(directions) == 0: 
            directions.append(self.direction * -1) 
        return directions
    
    def randomDirection(self, directions):
        """
        Chọn hướng ngẫu nhiên từ danh sách
        Args:
            directions: List các hướng hợp lệ
        Returns:
            Hướng được chọn ngẫu nhiên
        """
        return directions[randint(0, len(directions) - 1)]
    
    def goalDirection(self, directions): 
        """
        Chọn hướng gần nhất với mục tiêu (cho AI)
        Args:
            directions: List các hướng hợp lệ
        Returns:
            Hướng gần nhất với goal
        """
        distances = [] 
        for direction in directions: 
            # Tính vị trí sau khi di chuyển theo hướng này
            vec = self.node.position + self.directions[direction] * TILEWIDTH - self.goal
            distances.append(vec.magnitudeSquared())
        
        # Chọn hướng có khoảng cách nhỏ nhất
        index = distances.index(min(distances)) 
        return directions[index] 
    
    def setStartNode(self, node): 
        """
        Đặt node khởi đầu cho entity
        Args:
            node: Node khởi đầu
        """
        self.node = node 
        self.startNode = node 
        self.target = node 
        self.setPosition()
    
    def setBetweenNodes(self, direction): 
        """
        Đặt entity ở giữa 2 node dựa trên hướng
        Args:
            direction: Hướng di chuyển
        """
        if self.node.neighbors[direction] is not None:
            self.target = self.node.neighbors[direction]
            self.position = (self.node.position + self.target.position) / 2.0 
    
    def reset(self):
        """
        Khôi phục entity về trạng thái ban đầu
        """
        self.setStartNode(self.startNode)
        self.direction = STOP
        self.speed = 100 
        self.visible = True 
    
    def setSpeed(self, speed):
        """
        Đặt tốc độ di chuyển
        Args:
            speed: Tốc độ mới (pixel/second)
        """
        self.speed = speed * TILEWIDTH / 16
     
    def render(self, screen): 
        """
        Vẽ entity lên màn hình
        Args:
            screen: Surface để vẽ
        """
        if self.visible: 
            if self.image is not None: 
                # Vẽ hình ảnh nếu có
                adjust = Vector2(TILEWIDTH, TILEHEIGHT) / 2 
                p = self.position - adjust
                screen.blit(self.image, p.asTuple())
            else: 
                # Vẽ hình tròn nếu không có hình ảnh
                p = self.position.asInt()
                pygame.draw.circle(screen, self.color, p, self.radius)