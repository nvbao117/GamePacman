from ui import UIComponent
import pygame 
from ui.text import Text
class Button(UIComponent):
    def __init__(self, app,pos:tuple[int,int],text:str,size:tuple[int,int]=(350,100),
                font_size:int = 90 , onclick =None,topleft = False ):
        super().__init__(app)
        
        self.functions = onclick
        self.w = size[0]
        self.h = size[1]
        self.x = pos[0] - self.w //2 if not topleft else pos[0]
        self.y = pos[1] - self.h //2 if not topleft else pos[1]
            
        self.rect = pygame.Rect(self.x,self.y,self.w,self.h)
        self.hover_rect = pygame.Rect(self.x - 5 , self.y - 5, self.w+5,self.h+10)
        
        self.hover_active = False

        self.text = Text(text,(255,255,255),0,0,font_size)
        text_rect = self.text.label.get_rect(center=self.rect.center)
        self.text.position.x, self.text.position.y = text_rect.topleft
        
    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                for function in self.functions:
                    function()
                    
    def render(self):
        rect = self.rect.copy()

        if self.hover_active:
            hover_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            hover_surf.fill((255, 255, 255, 80))  # RGBA (80 = độ trong suốt)
            
            self.surface.blit(hover_surf, (self.x, self.y))
            pygame.draw.rect(self.surface, (255, 255, 0), self.rect, width=1, border_radius=8)


        text_rect = self.text.label.get_rect(center=rect.center)
        self.surface.blit(self.text.label, text_rect)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hover_active = self.rect.collidepoint(mouse_pos)