import pygame

def lerp(a, b, t):
    return a + (b - a) * t

def draw_rounded_rect(surface, color, rect, radius):
    if radius <= 0:
        pygame.draw.rect(surface, color, rect)
        return
    
    if isinstance(rect, tuple):
        x, y, w, h = rect
    else:
        rect_obj = rect
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
    
    temp_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(temp_surf, color, (0, 0, w, h), border_radius=radius)
    surface.blit(temp_surf, (x, y))

def draw_shadow(surface, rect, offset=(2, 2), blur=4, color=(0,0,0,50)):
    if isinstance(rect, tuple):
        x, y, w, h = rect
    else:
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
    
    shadow_surf = pygame.Surface((w + blur*2, h + blur*2), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(blur, blur, w, h)
    
    for i in range(blur):
        alpha = color[3] // (blur - i + 1)
        shadow_color = (*color[:3], alpha)
        expanded_rect = shadow_rect.inflate(i*2, i*2)
        pygame.draw.rect(shadow_surf, shadow_color, expanded_rect, border_radius=8)
    
    surface.blit(shadow_surf, (x - blur + offset[0], y - blur + offset[1]))