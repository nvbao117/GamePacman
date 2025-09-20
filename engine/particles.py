import pygame, random

class Particle:
    def __init__(self, x, y, color, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = lifetime
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 2)

class ParticleFountain:
    def __init__(self, rect, color=(255, 255, 255)):
        self.rect = rect
        self.color = color
        self.particles = []

    @classmethod
    def stars(cls, rect):
        """Tạo particle fountain với hạt ngôi sao"""
        return cls(rect, (255, 255, 255))

    def emit(self):
        # Tạo hạt mới ở vị trí random
        x = random.randint(self.rect.left, self.rect.right)
        y = random.randint(self.rect.top, self.rect.bottom)
        self.particles.append(Particle(x, y, self.color, lifetime=100))

    def update(self):
        for p in self.particles[:]:
            p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
