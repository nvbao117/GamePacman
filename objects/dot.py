# =============================================================================
# DOT.PY - CLASS DOT CHO GAME PAC-MAN
# =============================================================================
# File này chứa class Dot đơn giản để tạo các chấm vàng bay lơ lửng
# Sử dụng trong demo state hoặc hiệu ứng visual

import pygame

class Dot(pygame.sprite.Sprite):
    """
    Class Dot đơn giản cho hiệu ứng visual
    - Tạo chấm vàng có thể di chuyển
    - Hỗ trợ animation và lifecycle
    - Có thể được sử dụng trong demo state
    """
    def __init__(self, x, y):
        """
        Khởi tạo dot tại vị trí (x, y)
        Args:
            x, y: Tọa độ vị trí của dot
        """
        super().__init__()
        # Tạo surface trong suốt cho dot
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        # Vẽ chấm vàng ở giữa surface
        pygame.draw.circle(self.image, (255, 255, 0), (5, 5), 5)
        # Đặt rect ở vị trí center
        self.rect = self.image.get_rect(center=(x, y))
        self.alive = True  # Flag để State quản lý remove
    
    def logic(self, state):
        """
        Cập nhật logic của dot mỗi frame
        Args:
            state: State hiện tại (có thể cần để truy cập thông tin)
        """
        # Nếu cần hiệu ứng, vd: lấp lánh, di chuyển
        pass
    
    def draw(self, screen):
        """
        Vẽ dot lên màn hình
        Args:
            screen: Surface để vẽ
        """
        screen.blit(self.image, self.rect)

    def on_death(self, state):
        """
        Được gọi khi dot bị xóa
        Args:
            state: State hiện tại
        """
        # gọi khi chấm bị ăn hoặc xóa
        pass

    def resize(self, old, new):
        """
        Xử lý khi thay đổi kích thước màn hình
        Args:
            old: Kích thước cũ
            new: Kích thước mới
        """
        # xử lý khi thay đổi kích thước màn hình
        pass
