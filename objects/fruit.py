# =============================================================================
# FRUIT.PY - CLASS FRUIT CHO GAME PAC-MAN
# =============================================================================
# File này chứa class Fruit - trái cây xuất hiện trong game
# Fruit có thể được Pac-Man ăn để lấy điểm thưởng

import pygame 
from pygame.locals import * 
from constants import *
from objects.vector import Vector2
from objects.entity import Entity
from objects.modes import ModeController
from ui.sprites import FruitSprites

class Fruit(Entity):
    """
    Class Fruit - trái cây xuất hiện trong game
    - Kế thừa từ Entity để có thể di chuyển và render
    - Có thời gian sống giới hạn (lifespan)
    - Điểm thưởng tăng theo level
    - Tự động biến mất sau thời gian nhất định
    """
    def __init__(self, node, level=0):
        """
        Khởi tạo fruit tại node
        Args:
            node: Node xuất hiện của fruit
            level: Level hiện tại (ảnh hưởng đến điểm thưởng)
        """
        Entity.__init__(self, node) 
        self.name = FRUIT  # ID của fruit
        self.color = GREEN  # Màu mặc định
        self.lifespan = 5   # Thời gian sống (giây)
        self.timer = 0      # Timer đếm thời gian
        self.destroy = False  # Flag đánh dấu cần xóa
        # Điểm thưởng tăng theo level: 100 + level*20
        self.points = 100 + level * 20 
        # Đặt fruit ở giữa 2 node (hướng RIGHT)
        self.setBetweenNodes(RIGHT)
        # Khởi tạo sprite cho fruit
        self.sprites = FruitSprites(self, level)
    
    def update(self, dt):
        """
        Cập nhật fruit mỗi frame
        Args:
            dt: Delta time
        """
        self.timer += dt 
        # Kiểm tra hết thời gian sống
        if self.timer >= self.lifespan:
            self.destroy = True  # Đánh dấu cần xóa