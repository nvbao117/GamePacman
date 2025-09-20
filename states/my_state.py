import pygame
import random
from statemachine import State
from engine.particles import ParticleFountain
from objects.dot import Dot
class DemoState(State):
    BG_COLORS = [pygame.Color(c) for c in ["#203040", "#481e66", "#00605b", "#3f1f3c"]]
    NB_DOTS = 20

    def __init__(self):
        super().__init__()
        # Thêm hiệu ứng hạt: các ngôi sao bay trên nền
        self.particles.fountains.append(ParticleFountain.stars((800, 600)))
        # Sinh dots Pac-Man bay ngẫu nhiên
        self.generate_dots(self.NB_DOTS)

    def generate_dots(self, nb):
        for _ in range(nb):
            x = random.randint(50, 750)
            y = random.randint(50, 550)
            dot = Dot(x, y)  # class Dot bạn định nghĩa (sprite Pac-Man dots)
            self.add(dot)

    def logic(self):
        super().logic()
        # Logic thêm nếu cần (vd: di chuyển dots, animation)

    def draw(self, gfx):
        super().draw(gfx)
        # Có thể vẽ text giới thiệu
        font = pygame.font.SysFont("Arial", 32)
        text = font.render("PAC-MAN SPACE DEMO", True, (255, 255, 0))
        gfx.blit(text, (200, 50))
