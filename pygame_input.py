
import pygame
from pygame.locals import * 



class ButtonInput:
    """BASE class for all boolean/button inputs"""
    def match(self,event) -> bool:
        """
        whether the event corresponds to this button 
        This method must be overriddent by all subclasses
        """
        raise NotImplemented
    
    def update(self,event):
        if self.match(event) : 
            return self.pressed(event)
        return None
    
    def pressed(self,event)->bool:
        """
        whether a matching event is a press or a release
        """
        raise NotImplemented
class QuitEvent(ButtonInput):
    def match(self,event) ->bool:
        return event.type == pygame.QUIT
    
    def pressed(self,event) ->bool:
        return True
    


class Button : 
    def __init__(self,*events,mouse_button = None , rect = None):
        self.events = events
        self.mouse_button = mouse_button
        self.rect  = rect
        self.on_press_callback = None 
        
    def on_press(self,callback):
        self.on_press_call = callback
        return self  
    
    def trigger(self,event):
        if any(event.type == e for e in self.events):
            if self.on_press_callback:
                self.on_press_callback()
        
        
        if self.mouse_button and event.type == MOUSEBUTTONDOWN:
            if event.button == self.mouse_button:
                if self.rect and self.rect.collidepoint(event.pos) : 
                    if self.on_press_callback:
                        self.on_press_callback()
