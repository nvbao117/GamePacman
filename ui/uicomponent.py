import sys 
import pygame 

class UIComponent: 
    def __init__(self,app):
        self.app = app
        self.surface = app.screen 
        
    def update(self):
        pass
    
    def draw(self):
        pass
    
    def eventHandling(self,e) :
        pass
    
