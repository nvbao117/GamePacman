# arcade_pygame.py
import pygame
import sys
from pathlib import Path


# tạo cửa sổ game trước
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pac-Man UI")

IMG_PATH = Path("../assets/images/pacman.jpg")  # <- chỉnh lại đường dẫn ảnh

pygame.init()
clock = pygame.time.Clock()

if not IMG_PATH.exists():
    raise FileNotFoundError(f"Background image not found at {IMG_PATH}")

bg = pygame.image.load(str(IMG_PATH)).convert_alpha()
W, H = bg.get_width(), bg.get_height() + 80
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pac-Man Arcade UI Demo (Pygame)")

bg = pygame.transform.smoothscale(bg, (W, bg.get_height()))
FONT = pygame.font.SysFont("Arial", 20, bold=True)

BUTTONS = [
    {"label": "PLAY", "rect": pygame.Rect(180, 540, 90, 40)},
    {"label": "OPTIONS", "rect": pygame.Rect(430, 548, 80, 40)},
    {"label": "PLAYERS", "rect": pygame.Rect(516, 548, 80, 40)},
    {"label": "EXIT", "rect": pygame.Rect(600, 548, 80, 40)},
]

def draw_button(surf, btn, mouse_pos):
    r = btn["rect"]
    hovered = r.collidepoint(mouse_pos)
    base_color = (12, 160, 170) if btn["label"] != "PLAY" else (255, 200, 0)
    bgc = tuple(min(255, int(c * 1.15)) for c in base_color) if hovered else base_color
    pygame.draw.rect(surf, bgc, r, border_radius=8)
    pygame.draw.rect(surf, (30,30,30), r, width=2, border_radius=8)
    txt = FONT.render(btn["label"], True, (0,0,0))
    txtrect = txt.get_rect(center=r.center)
    surf.blit(txt, txtrect)

def mainloop():
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in BUTTONS:
                    if btn["rect"].collidepoint(event.pos):
                        label = btn["label"]
                        if label == "EXIT":
                            running = False
                        else:
                            print(f"Button clicked: {label}")

        screen.fill((0,0,0))
        screen.blit(bg, (0,0))
        pygame.draw.rect(screen, (252, 186, 50), pygame.Rect(0, bg.get_height(), W, H - bg.get_height()))
        pygame.draw.rect(screen, (0,0,0), pygame.Rect(W//2 - 90, bg.get_height() + 6, 180, 44), border_radius=6)
        for btn in BUTTONS:
            draw_button(screen, btn, mouse_pos)
        
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("Pygame window closed.")

if __name__ == "__main__":
    mainloop()
