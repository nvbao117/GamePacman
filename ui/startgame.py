# Pac-Man Arcade Start Screen
import pygame
import sys
import math
from pathlib import Path


# tạo cửa sổ game trước
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pac-Man UI")

IMG_PATH = Path("../assets/images/pacman.jpg")  # <- chỉnh lại đường dẫn ảnh

pygame.init()

# Lấy thông tin màn hình
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Tạo cửa sổ fullscreen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Pac-Man Arcade")

# Load ảnh nền
IMG_PATH = Path("assets/images/maxresdefault.jpg")
if not IMG_PATH.exists():
    raise FileNotFoundError(f"Background image not found at {IMG_PATH}")

bg = pygame.image.load(str(IMG_PATH)).convert_alpha()
bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Fonts
FONT_LARGE = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 60)
FONT_MEDIUM = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 30)
FONT_SMALL = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)

clock = pygame.time.Clock()

# Màu sắc theo theme Pac-Man
PACMAN_YELLOW = (255, 255, 0)
PACMAN_BLUE = (0, 100, 255)
PACMAN_PINK = (255, 100, 150)
PACMAN_RED = (255, 0, 0)
PACMAN_ORANGE = (255, 165, 0)

# Tạo các nút với vị trí căn giữa
center_x = SCREEN_WIDTH // 2
center_y = SCREEN_HEIGHT // 2

BUTTONS = [
    {
        "label": "PLAY", 
        "rect": pygame.Rect(0, 0, 200, 60),
        "color": PACMAN_YELLOW,
        "hover_color": (255, 255, 100),
        "pos": (center_x, center_y - 50)
    },
    {
        "label": "OPTIONS", 
        "rect": pygame.Rect(0, 0, 200, 60),
        "color": PACMAN_BLUE,
        "hover_color": (100, 150, 255),
        "pos": (center_x, center_y + 50)
    },
    {
        "label": "EXIT", 
        "rect": pygame.Rect(0, 0, 200, 60),
        "color": PACMAN_RED,
        "hover_color": (255, 100, 100),
        "pos": (center_x, center_y + 150)
    },
]

class AnimatedButton:
    def __init__(self, label, pos, color, hover_color):
        self.label = label
        self.pos = pos
        self.color = color
        self.hover_color = hover_color
        self.rect = pygame.Rect(0, 0, 200, 60)
        self.rect.center = pos
        self.is_hovered = False
        self.animation_time = 0
        
    def update(self, mouse_pos):
        self.animation_time += 0.1
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
    def draw(self, surf):
        # Hiệu ứng bounce
        bounce_offset = int(3 * math.sin(self.animation_time * 2))
        current_pos = (self.pos[0], self.pos[1] + bounce_offset)
        
        # Cập nhật rect
        self.rect.center = current_pos
        
        # Màu sắc
        if self.is_hovered:
            color = self.hover_color
            # Hiệu ứng pulse khi hover
            pulse = int(10 * math.sin(self.animation_time * 4))
            color = tuple(min(255, c + pulse) for c in color)
        else:
            color = self.color
            
        # Vẽ background với border radius
        pygame.draw.rect(surf, color, self.rect, border_radius=15)
        
        # Vẽ border
        border_color = (255, 255, 255) if self.is_hovered else (200, 200, 200)
        pygame.draw.rect(surf, border_color, self.rect, width=3, border_radius=15)
        
        # Vẽ text
        text_surface = FONT_MEDIUM.render(self.label, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=current_pos)
        surf.blit(text_surface, text_rect)
        
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

# Tạo các nút animated
animated_buttons = [
    AnimatedButton("PLAY", (center_x, center_y - 50), PACMAN_YELLOW, (255, 255, 100)),
    AnimatedButton("OPTIONS", (center_x, center_y + 50), PACMAN_BLUE, (100, 150, 255)),
    AnimatedButton("EXIT", (center_x, center_y + 150), PACMAN_RED, (255, 100, 100)),
]

def start_menu():
    """Chuyển đến màn hình menu chính"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from main import App
    
    # Đóng cửa sổ hiện tại
    pygame.quit()
    
    # Chạy menu chính (App class)
    app = App()
    app.run()

def draw_title(surf, animation_time):
    """Vẽ title với hiệu ứng glow"""
    title_text = "PAC-MAN"
    subtitle_text = "ARCADE"
    
    # Hiệu ứng glow cho title
    glow_intensity = int(50 + 30 * math.sin(animation_time))
    glow_color = (min(255, PACMAN_YELLOW[0] + glow_intensity), 
                 min(255, PACMAN_YELLOW[1] + glow_intensity), 
                 min(255, PACMAN_YELLOW[2] + glow_intensity))
    
    # Vẽ shadow/glow
    for i in range(5, 0, -1):
        shadow_color = tuple(max(0, c - i * 15) for c in glow_color)
        title_surface = FONT_LARGE.render(title_text, True, shadow_color)
        title_rect = title_surface.get_rect(center=(center_x + i, center_y - 200 + i))
        surf.blit(title_surface, title_rect)
    
    # Vẽ title chính
    title_surface = FONT_LARGE.render(title_text, True, PACMAN_YELLOW)
    title_rect = title_surface.get_rect(center=(center_x, center_y - 200))
    surf.blit(title_surface, title_rect)
    
    # Vẽ subtitle
    subtitle_surface = FONT_MEDIUM.render(subtitle_text, True, PACMAN_YELLOW)
    subtitle_rect = subtitle_surface.get_rect(center=(center_x, center_y - 140))
    surf.blit(subtitle_surface, subtitle_rect)

def draw_particles(surf, animation_time):
    """Vẽ các chấm tròn bay lơ lửng như trong Pac-Man"""
    for i in range(30):
        x = (animation_time * 30 + i * 80) % (SCREEN_WIDTH + 50)
        y = 100 + 80 * math.sin(animation_time * 0.5 + i * 0.3)
        size = 2 + int(2 * math.sin(animation_time * 2 + i))
        color = PACMAN_YELLOW if i % 4 == 0 else PACMAN_ORANGE
        pygame.draw.circle(surf, color, (int(x), int(y)), size)

def draw_gradient_overlay(surf):
    """Vẽ overlay gradient để làm mờ ảnh nền"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for y in range(SCREEN_HEIGHT):
        alpha = int(100 + 50 * (y / SCREEN_HEIGHT))
        color = (0, 0, 0, alpha)
        pygame.draw.line(overlay, color, (0, y), (SCREEN_WIDTH, y))
    surf.blit(overlay, (0, 0))

def mainloop():
    running = True
    animation_time = 0
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        animation_time += 0.05
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in animated_buttons:
                    if btn.is_clicked(event.pos):
                        if btn.label == "EXIT":
                            running = False
                        elif btn.label == "PLAY":
                            # Chuyển đến menu chính
                            start_menu()
                            return
                        elif btn.label == "OPTIONS":
                            print("Options clicked!")

        # Vẽ background
        screen.fill((0, 0, 0))
        screen.blit(bg, (0, 0))
        
        # Vẽ gradient overlay
        draw_gradient_overlay(screen)
        
        # Vẽ particles
        draw_particles(screen, animation_time)
        
        # Vẽ title
        draw_title(screen, animation_time)
        
        # Cập nhật và vẽ các nút
        for btn in animated_buttons:
            btn.update(mouse_pos)
            btn.draw(screen)
        
        # Vẽ text hướng dẫn
        instruction_text = "Click PLAY to start your adventure!"
        instruction_surface = FONT_SMALL.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(center_x, center_y + 250))
        screen.blit(instruction_surface, instruction_rect)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("Pygame window closed.")

if __name__ == "__main__":
    mainloop()
