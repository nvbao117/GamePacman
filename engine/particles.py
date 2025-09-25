# =============================================================================
# PARTICLES.PY - HỆ THỐNG PARTICLE EFFECTS CHO GAME PAC-MAN
# =============================================================================
# File này chứa hệ thống particle effects để tạo các hiệu ứng visual
# như ngôi sao, sparkles, và các hiệu ứng khác trong game

import pygame, random

class Particle:
    """
    Class đại diện cho một particle đơn lẻ
    - Có vị trí, màu sắc, thời gian sống
    - Di chuyển theo vector vận tốc
    - Tự động biến mất khi hết thời gian sống
    """
    def __init__(self, x, y, color, lifetime):
        """
        Khởi tạo particle
        
        Args:
            x, y: Vị trí ban đầu
            color: Màu sắc của particle
            lifetime: Số frame particle sẽ tồn tại
        """
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = lifetime
        # Vector vận tốc ngẫu nhiên
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)

    def update(self):
        """
        Cập nhật vị trí và thời gian sống của particle
        - Di chuyển theo vector vận tốc
        - Giảm thời gian sống
        """
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        """
        Vẽ particle lên surface
        
        Args:
            surface: Pygame surface để vẽ lên
        """
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 2)

class ParticleFountain:
    """
    Class quản lý một nhóm particles tạo hiệu ứng fountain
    - Tạo particles mới trong một vùng nhất định
    - Cập nhật và vẽ tất cả particles
    - Tự động dọn dẹp particles đã chết
    """
    def __init__(self, rect, color=(255, 255, 255)):
        """
        Khởi tạo particle fountain
        
        Args:
            rect: Vùng tạo particles (pygame.Rect)
            color: Màu sắc mặc định của particles
        """
        self.rect = rect
        self.color = color
        self.particles = []  # Danh sách particles hiện tại

    @classmethod
    def stars(cls, rect):
        """
        Tạo particle fountain với hạt ngôi sao màu trắng
        
        Args:
            rect: Vùng tạo particles
            
        Returns:
            ParticleFountain với màu trắng
        """
        return cls(rect, (255, 255, 255))

    def emit(self):
        """
        Tạo particle mới ở vị trí ngẫu nhiên trong vùng rect
        - Particle có thời gian sống 100 frames
        """
        # Tạo hạt mới ở vị trí random trong vùng rect
        x = random.randint(self.rect.left, self.rect.right)
        y = random.randint(self.rect.top, self.rect.bottom)
        self.particles.append(Particle(x, y, self.color, lifetime=100))

    def update(self):
        """
        Cập nhật tất cả particles
        - Gọi update() cho mỗi particle
        - Xóa particles đã hết thời gian sống
        """
        for p in self.particles[:]:  # Sử dụng slice để tránh lỗi khi modify list
            p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        """
        Vẽ tất cả particles lên surface
        
        Args:
            surface: Pygame surface để vẽ lên
        """
        for p in self.particles:
            p.draw(surface)
