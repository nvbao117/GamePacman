import pygame

class Dot(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 0), (5, 5), 5)  # chấm vàng
        self.rect = self.image.get_rect(center=(x, y))
        self.alive = True  # để State quản lý remove
    
    def logic(self, state):
        # Nếu cần hiệu ứng, vd: lấp lánh
        pass
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def on_death(self, state):
        # gọi khi chấm bị ăn
        pass

    def resize(self, old, new):
        # xử lý khi thay đổi kích thước màn hình
        pass
