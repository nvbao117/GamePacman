import pygame 
from constants import *
from objects.vector import Vector2

class Text(object) : 
    def __init__(self,text,color,x,y,size,time=None,id = None ,visible = True):
        self.id = id
        self.text = text
        self.color = color
        self.size = size 
        self.visible = visible 
        self.position = Vector2(x,y)
        self.timer = 0 
        self.lifespan =time 
        self.label = None
        self.destroy = False
        self.setupFont("assets/fonts/Aerologica.ttf")
        self.createLabel()
    
    def setupFont(self,fontpath):
        self.font = pygame.font.Font(fontpath,self.size)
    
    def createLabel(self):
        self.label = self.font.render(self.text,1,self.color)
    
    def setText(self,newtext):
        self.text = str(newtext)
        self.createLabel()
    
    def update(self,dt):
        if self.lifespan is not None : 
            self.timer += dt
            if self.timer >= self.lifespan:
                self.timer = 0 
                self.lifespan = None 
                self.destroy = True
                
    
    def render(self,screen):
        if self.visible :
            x,y = self.position.asTuple()
            screen.blit(self.label,(x,y))
    
class TextGroup(object):
    def __init__(self):
        self.nextid = 10
        self.alltext = {}
        self.setupText()
        self.showText(READYTXT)
    
    
    def addText(self,text,color , x, y , size , time=None , id = None) :
        if id is not None:
            # Sử dụng id được cung cấp
            self.alltext[id] = Text(text,color,x,y,size,time = time,id = id )
            return id
        else:
            # Tự động tạo id mới
            self.nextid += 1 
            self.alltext[self.nextid] = Text(text,color,x,y,size,time = time,id = id )
            return self.nextid
    
    def removeText(self,id):
        self.alltext.pop(id)
    
    def setupText(self):
        size = TILEHEIGHT
        self.alltext[SCORETXT] = Text("0".zfill(8), WHITE, 0, TILEHEIGHT, size)
        self.alltext[LEVELTXT] = Text(str(1).zfill(3), WHITE, 23*TILEWIDTH, TILEHEIGHT, size)
        self.alltext[READYTXT] = Text("READY!", YELLOW, 11.25*TILEWIDTH, 20*TILEHEIGHT, size, visible=False)
        self.alltext[PAUSETXT] = Text("PAUSED!", YELLOW, 10.625*TILEWIDTH, 20*TILEHEIGHT, size, visible=False)
        self.alltext[GAMEOVERTXT] = Text("GAMEOVER!", YELLOW, 10*TILEWIDTH, 20*TILEHEIGHT, size, visible=False)
        self.addText("SCORE",WHITE,0,0,size)
        self.addText("LEVEL",WHITE,23*TILEWIDTH,0,size)
        
        # Banner thông tin sinh viên - luôn hiển thị ở góc trái màn hình
        self.setupStudentBanner()
    
    def setupStudentBanner(self):
        """Tạo banner thông tin sinh viên ở góc trái màn hình"""
        # Kích thước font cho banner
        banner_size = 18
        
        # Màu sắc cho banner - tất cả màu trắng
        banner_color = (255, 255, 255)  # Màu trắng
        mssv_color = (255, 255, 255)    # Màu trắng
        
        # Vị trí góc trái màn hình
        start_x = 10
        start_y = 10
        
        # Thông tin sinh viên
        student1_name = "Nguyễn Vũ Bảo"
        student1_mssv = "MSSV: 23110079"
        student2_name = "Trần Hoàng Phúc Quân"
        student2_mssv = "MSSV: 23110146"
        
        # Tạo các text cho banner
        self.addText(student1_name, banner_color, start_x, start_y, banner_size, id="student1_name")
        self.addText(student1_mssv, mssv_color, start_x, start_y + 20, banner_size, id="student1_mssv")
        self.addText(student2_name, banner_color, start_x, start_y + 50, banner_size, id="student2_name")
        self.addText(student2_mssv, mssv_color, start_x, start_y + 70, banner_size, id="student2_mssv")
        
        # Thêm đường viền cho banner
        self.addText("=" * 25, (100, 100, 100), start_x - 5, start_y - 5, 12, id="banner_border_top")
        self.addText("=" * 25, (100, 100, 100), start_x - 5, start_y + 85, 12, id="banner_border_bottom")
    
    def ensureStudentBannerVisible(self):
        """Đảm bảo banner sinh viên luôn hiển thị"""
        banner_ids = ["student1_name", "student1_mssv", "student2_name", "student2_mssv", 
                     "banner_border_top", "banner_border_bottom"]
        for banner_id in banner_ids:
            if banner_id in self.alltext:
                self.alltext[banner_id].visible = True
        
    def update(self,dt):
        for tkey in list(self.alltext.keys()):
            self.alltext[tkey].update(dt)
            if self.alltext[tkey].destroy:
                self.removeText(tkey)
    
    def showText(self,id):
        self.hideText()
        self.alltext[id].visible = True
    
    def hideText(self):
        self.alltext[READYTXT].visible = False
        self.alltext[PAUSETXT].visible = False
        self.alltext[GAMEOVERTXT].visible = False
        # Đảm bảo banner sinh viên luôn hiển thị
        self.ensureStudentBannerVisible()
    
    def updateScore(self,score):
        self.updateText(SCORETXT, str(score).zfill(8))

    def updateLevel(self,level):
        self.updateText(LEVELTXT, str(level + 1).zfill(3))

    def updateText(self,id,value):
        self.alltext[id].setText(value)

    def render(self,screen):
        for tkey in list(self.alltext.keys()):
            self.alltext[tkey].render(screen)
    
    