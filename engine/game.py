# =============================================================================
# GAME.PY - CLASS CHÍNH QUẢN LÝ GAME PAC-MAN
# =============================================================================
# File này chứa class Game - quản lý toàn bộ logic game, render, và các sự kiện
# Bao gồm khởi tạo game, cập nhật logic, xử lý va chạm, và render

import pygame
from pygame.locals import * 
from constants import *
from objects.nodes import NodeGroup
from objects.pauser import Pause
from objects.maze import MazeData
from ui.sprites import LifeSprites ,MazeSprites
from objects.player import Pacman
from objects.fruit import Fruit
from objects.ghosts import GhostGroup
from objects.pellets import PelletGroup
from ui.text import TextGroup
import time
from engine.compute_once_system import compute_once

class Game(object):
    """
    Class Game - Quản lý toàn bộ logic game Pac-Man
    
    Chức năng chính:
    - Khởi tạo và quản lý tất cả objects (Pacman, Ghosts, Pellets, Maze)
    - Update logic game mỗi frame (movement, collisions, AI)
    - Render tất cả objects lên màn hình
    - Xử lý va chạm giữa Pacman và Ghosts/Pellets/Fruits  
    - Quản lý timer, score, lives, levels
    - Tích hợp analytics system để theo dõi performance
    - Hỗ trợ các thuật toán AI (BFS, DFS, A*, UCS, IDS, Greedy)
    """
    def __init__(self, algorithm: str = 'BFS', config=None):
        pygame.init()
        
        # Lưu thuật toán AI được chọn
        self.algorithm = algorithm
        self.algorithm_heuristic = "NONE"  # Mặc định không heuristic
        self.custom_heuristic = None  # Hàm heuristic tùy chỉnh
        self.config = config  # Lưu config để truyền cho Pacman
        
        # Khởi tạo analytics
        self.analytics_started = False
        
        # Hệ thống đo thời gian
        self.start_time = None
        self.game_time = 0.0
        self.is_timer_running = False
        self.timer_started_by_user = False  # Flag để đảm bảo timer chỉ bắt đầu khi user nhấn SPACE
        
        # Performance tracking
        self.steps_taken = 0
        self.pathfinding_calls = 0
        self.last_position = None
        
        # Step counting system
        self.total_steps = 0 
        self.ai_steps = 0     # Số bước khi dùng AI
        self.player_steps = 0 # Số bước khi điều khiển thủ công
        self.last_step_position = None  # Vị trí cuối cùng để detect step
        
        # Các thuộc tính màn hình và render
        self.screen = None
        self.background = None
        self.background_norm = None      # Background bình thường
        self.background_flash = None    # Background khi flash (level complete)
        self.clock = pygame.time.Clock()
        
        # Objects trong game
        self.fruit = None               # Trái cây hiện tại
        self.pause = Pause(True)        # Hệ thống pause
        
        # Thông tin game
        self.level = 0                  # Level hiện tại
        self.lives = 4                  # Số mạng còn lại
        self.score = 0                  # Điểm số hiện tại
        
        # UI components
        self.textgroup = TextGroup()    # Nhóm text hiển thị
        self.lifesprites = LifeSprites(self.lives)  # Sprites hiển thị số mạng
        self.hybrid_ai_display = None   # Sẽ được khởi tạo sau khi tạo pacman
        
        # Hiệu ứng visual
        self.flashBG = False            # Có flash background không
        self.flashTime = 0.2            # Thời gian flash
        self.flashTimer = 0             # Timer cho flash
        
        # Quản lý fruit
        self.fruitCaptured = []         # Danh sách fruit đã ăn
        self.fruitNode = None           # Node chứa fruit
        
        # Dữ liệu maze
        self.mazedata = MazeData()      # Dữ liệu maze hiện tại
        
        # Thời gian
        self.starttime = time.time()    # Thời gian bắt đầu level
        self.endtime = time.time()      # Thời gian kết thúc level
        self.running = True             # Game có đang chạy không
        self.ai_mode = True             # Chế độ AI (True) hay Player (False)
        self.ghost_mode = True          # Chế độ Ghost (True) hay không có Ghost (False)
        
        # Few pellets mode configuration
        self.few_pellets_mode = False   # Chế độ few pellets
        self.few_pellets_count = 20     # Số lượng pellets trong chế độ few pellets
    
    def setBackground(self):
        """
        Thiết lập background cho game với các hiệu ứng visual
        - Tạo background bình thường và flash
        - Thêm gradient và hiệu ứng theo level
        - Áp dụng maze sprites lên background
        """
        # Tạo surface cho background bình thường
        try:
            self.background_norm = pygame.surface.Surface(SCREENSIZE).convert()
        except pygame.error:
            # Headless mode - không cần convert()
            self.background_norm = pygame.surface.Surface(SCREENSIZE)
        self.background_norm.fill(BLACK)
        
        # Tạo surface cho background flash (khi level complete)
        try:
            self.background_flash = pygame.surface.Surface(SCREENSIZE).convert()
        except pygame.error:
            # Headless mode - không cần convert()
            self.background_flash = pygame.surface.Surface(SCREENSIZE)
        self.background_flash.fill(BLACK)
        
        # Tạo background nâng cao với gradient và hiệu ứng
        self._create_enhanced_background(self.background_norm, self.level % 5)
        self._create_enhanced_background(self.background_flash, 5)
        
        # Áp dụng maze sprites lên background
        self.background_norm = self.mazesprites.constructBackground(self.background_norm, self.level%5)
        self.background_flash = self.mazesprites.constructBackground(self.background_flash, 5)
        
        # Reset flash state
        self.flashBG = False
        self.background = self.background_norm
    
    def _create_enhanced_background(self, surface, level):
        """Create enhanced background with gradient and visual effects"""
        import math
        import time
        
        current_time = time.time()
        
        for y in range(SCREENHEIGHT):
            intensity = int(15 + (y / SCREENHEIGHT) * 10)
            color = (intensity, intensity, intensity + 20)
            pygame.draw.line(surface, color, (0, y), (SCREENWIDTH, y))
        
        for i in range(50):
            x = (i * 37 + current_time * 5) % SCREENWIDTH
            y = (i * 23 + current_time * 3) % SCREENHEIGHT
            alpha = int(30 + 20 * math.sin(current_time * 2 + i * 0.1))
            color = (alpha, alpha, alpha + 30)
            size = 1 + int(1 * math.sin(current_time * 3 + i * 0.2))
            pygame.draw.circle(surface, color, (int(x), int(y)), size)
        
        # Add floating particles
        for i in range(15):
            x = (current_time * 10 + i * 100) % SCREENWIDTH
            y = 50 + 100 * math.sin(current_time * 1.5 + i * 0.3)
            alpha = int(40 + 30 * math.sin(current_time * 2 + i))
            color = (alpha, alpha // 2, alpha + 20)
            pygame.draw.circle(surface, color, (int(x), int(y)), 2)
        
        # Add level-specific effects
        if level == 0:  # Level 1 - subtle blue glow
            for i in range(3):
                glow_alpha = int(20 - i * 5)
                glow_color = (glow_alpha, glow_alpha, glow_alpha + 40)
                pygame.draw.circle(surface, glow_color, (SCREENWIDTH//2, SCREENHEIGHT//2), 100 + i * 20, 2)
        elif level == 1:  # Level 2 - purple nebula
            for i in range(5):
                x = (current_time * 3 + i * 80) % SCREENWIDTH
                y = (current_time * 2 + i * 60) % SCREENHEIGHT
                alpha = int(15 + 10 * math.sin(current_time * 1 + i))
                color = (alpha, alpha // 3, alpha + 15)
                size = 20 + int(15 * math.sin(current_time * 0.5 + i))
                pygame.draw.circle(surface, color, (int(x), int(y)), size)
        elif level == 2:  # Level 3 - green energy
            for i in range(8):
                x = (current_time * 4 + i * 50) % SCREENWIDTH
                y = (current_time * 3 + i * 40) % SCREENHEIGHT
                alpha = int(20 + 15 * math.sin(current_time * 1.5 + i))
                color = (alpha // 2, alpha, alpha // 2)
                size = 10 + int(8 * math.sin(current_time * 0.8 + i))
                pygame.draw.circle(surface, color, (int(x), int(y)), size)
        elif level == 3:  # Level 4 - red danger
            for i in range(6):
                x = (current_time * 2 + i * 70) % SCREENWIDTH
                y = (current_time * 4 + i * 50) % SCREENHEIGHT
                alpha = int(25 + 20 * math.sin(current_time * 2 + i))
                color = (alpha, alpha // 4, alpha // 4)
                size = 15 + int(10 * math.sin(current_time * 1.2 + i))
                pygame.draw.circle(surface, color, (int(x), int(y)), size)
        else:  # Level 5+ - rainbow chaos
            colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130)]
            for i in range(10):
                x = (current_time * 6 + i * 40) % SCREENWIDTH
                y = (current_time * 5 + i * 30) % SCREENHEIGHT
                color_idx = (i + int(current_time * 2)) % len(colors)
                alpha = int(30 + 20 * math.sin(current_time * 3 + i))
                color = tuple(int(c * alpha / 255) for c in colors[color_idx])
                size = 8 + int(6 * math.sin(current_time * 1.8 + i))
                pygame.draw.circle(surface, color, (int(x), int(y)), size)
    
    def _render_dynamic_effects(self, surface):
        """Render dynamic effects on top of the game"""
        import math
        import time
        
        current_time = time.time()
        
        # Add pulsing border effect around the entire game area
        pulse_intensity = int(20 + 15 * math.sin(current_time * 3))
        border_color = (pulse_intensity, pulse_intensity, pulse_intensity + 30)
        
        # Draw animated border
        for i in range(3):
            border_rect = pygame.Rect(i, i, SCREENWIDTH - i*2, SCREENHEIGHT - i*2)
            alpha = int(30 - i * 10)
            color = (alpha, alpha, alpha + 40)
            pygame.draw.rect(surface, color, border_rect, 1)
        
        # Corner effects removed for cleaner interface
        
        # Add floating energy orbs
        for i in range(8):
            x = (current_time * 20 + i * 100) % SCREENWIDTH
            y = (current_time * 15 + i * 80) % SCREENHEIGHT
            alpha = max(0, min(255, int(30 + 20 * math.sin(current_time * 2 + i))))
            color = (alpha, max(0, min(255, alpha + 20)), max(0, min(255, alpha + 40)))
            size = 3 + int(2 * math.sin(current_time * 4 + i))
            pygame.draw.circle(surface, color, (int(x), int(y)), size)
            
            # Add glow effect
            for j in range(2, 0, -1):
                glow_alpha = max(0, min(255, int(alpha * 0.5 - j * 10)))
                glow_color = (glow_alpha, max(0, min(255, glow_alpha + 10)), max(0, min(255, glow_alpha + 20)))
                pygame.draw.circle(surface, glow_color, (int(x), int(y)), size + j * 2, 1)
    
    def _render_enhanced_effects(self, surface):
        """Render enhanced visual effects for the main game screen"""
        import math
        import time
        
        current_time = time.time()
        
        # Add screen-wide pulsing effect
        pulse_alpha = int(10 + 5 * math.sin(current_time * 2))
        overlay = pygame.Surface((SCREENWIDTH, SCREENHEIGHT), pygame.SRCALPHA)
        overlay.fill((pulse_alpha, pulse_alpha, pulse_alpha + 20, pulse_alpha))
        surface.blit(overlay, (0, 0))
        
        # Add animated scanlines
        for i in range(0, SCREENHEIGHT, 4):
            scanline_alpha = int(5 + 3 * math.sin(current_time * 3 + i * 0.1))
            color = (scanline_alpha, scanline_alpha, scanline_alpha + 10, scanline_alpha)
            pygame.draw.line(surface, color, (0, i), (SCREENWIDTH, i))
        
        # Corner energy effects removed for cleaner interface
    
    def initialize_game(self):
        self.startGame()
    
    def startGame(self):
        self.mazedata.loadMaze(self.level)
        
        # Tạo maze sprites
        self.mazesprites = MazeSprites(
            "assets/maze/"+self.mazedata.obj.name+".txt", 
            "assets/maze/"+self.mazedata.obj.name+"_rotation.txt"
        )
        
        # Thiết lập background
        self.setBackground()
        
        # Tạo node group và thiết lập connections
        self.nodes = NodeGroup("assets/maze/"+self.mazedata.obj.name+".txt")
        self.mazedata.obj.setPortalPairs(self.nodes)      # Thiết lập portal pairs
        self.mazedata.obj.connectHomeNodes(self.nodes)    # Kết nối home nodes
        
        self.pacman = Pacman(self.nodes.getNodeFromTiles(*self.mazedata.obj.pacmanStart), self.config)
        self.pacman.game_instance = self
        
        # Bắt đầu analytics nếu chưa bắt đầu
        if not self.analytics_started:
            self.analytics_started = True
        

        maze_file = "assets/maze/"+self.mazedata.obj.name+".txt"
        
        # Tạo pellets dựa trên maze của level hiện tại
        few_pellets_mode = getattr(self, 'few_pellets_mode', False)
        few_pellets_count = getattr(self, 'few_pellets_count', 20)
        self.pellets = PelletGroup(maze_file, self.nodes, few_pellets_mode, few_pellets_count)
        
        # Tạo ghosts với vị trí bắt đầu từ maze data
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        
        # Thiết lập vị trí bắt đầu cho từng ghost dựa trên maze data
        if hasattr(self.mazedata.obj, 'ghostStart'):
            ghost_starts = self.mazedata.obj.ghostStart
            if len(ghost_starts) >= 4:
                self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(*ghost_starts[0]))
                self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(*ghost_starts[1]))
                self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(*ghost_starts[2]))
                self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(*ghost_starts[3]))
        else:
            # Fallback cho maze cũ không có ghostStart
            self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 0+14))
            self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))
            self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(0+11.5, 3+14))
            self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(4+11.5, 3+14))
        
        # Thiết lập spawn node
        if hasattr(self.mazedata.obj, 'ghostSpawn'):
            self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.ghostSpawn))
        else:
            self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))
    
        # Thiết lập access rules dựa trên maze data
        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        
        # Sử dụng access rules từ maze data nếu có
        if hasattr(self.mazedata.obj, 'accessRules'):
            for rule in self.mazedata.obj.accessRules:
                if len(rule) >= 3:
                    x, y, direction, target = rule[0], rule[1], rule[2], rule[3] if len(rule) > 3 else self.ghosts
                    self.nodes.denyAccessList(x, y, direction, target)
        else:
            # Fallback cho maze cũ
            self.nodes.denyAccessList(2+11.5, 3+14, LEFT, self.ghosts)
            self.nodes.denyAccessList(2+11.5, 3+14, RIGHT, self.ghosts)
            self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
            self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
            self.nodes.denyAccessList(12, 14, UP, self.ghosts)
            self.nodes.denyAccessList(15, 14, UP, self.ghosts)
            self.nodes.denyAccessList(12, 26, UP, self.ghosts)
            self.nodes.denyAccessList(15, 26, UP, self.ghosts)
    
    def update(self) : 
        dt = self.clock.tick(60) / 1000.0
        self.textgroup.update(dt)
        self.pellets.update(dt)
        if not self.pause.paused:
            if self.ghost_mode:
                self.ghosts.update(dt)
            if self.fruit is not None:
                self.fruit.update(dt)
            self.checkPelletEvents()
            self.checkGhostEvents()
            self.checkFruitEvents()
        else:
            if self.is_timer_running:
                self.stop_timer()
        if self.pacman.alive:
            if not self.pause.paused:
                self._track_step()
                if hasattr(self, 'ai_mode') and self.ai_mode:
                    ghost_group = self.ghosts if self.ghost_mode else None
                    self.pacman.update_ai(dt, self.pellets, True, ghostGroup=ghost_group, fruit=self.fruit)
                else:
                    self.pacman.update(dt)
            self.pacman.score = self.score
        else:
            self.pacman.update(dt)
            self.pacman.score = self.score

        if self.flashBG:
            self.flashTimer += dt
            if self.flashTimer >= self.flashTime:
                self.flashTimer = 0 
                if self.background == self.background_norm:
                    self.background = self.background_flash
                else:
                    self.background = self.background_norm
                    
        afterPauseMethod = self.pause.update(dt)
        if afterPauseMethod is not None :
            afterPauseMethod()
        
        # Update Hybrid AI Display
        if hasattr(self, 'hybrid_ai_display') and self.hybrid_ai_display:
            self.hybrid_ai_display.update(dt)
        
    def checkEvents(self) : 
        for event in pygame.event.get():
            if event.type == QUIT : 
                self.running = False
                return
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    # Pause game instead of quitting
                    if self.pacman.alive:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()
                        else:
                            self.textgroup.showText(PAUSETXT)
                if event.key == K_SPACE:
                    if self.pacman.alive:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()
                        else:
                            self.textgroup.showText(PAUSETXT)
                
                # Hybrid AI Controls
                if event.key == K_h:  # H key để toggle Hybrid AI
                    if hasattr(self.pacman, 'toggle_hybrid_ai'):
                        self.pacman.toggle_hybrid_ai()

                if event.key == K_u:  # U key để toggle UI display
                    if hasattr(self, 'hybrid_ai_display') and self.hybrid_ai_display:
                        self.hybrid_ai_display.toggle_display()
                             
    def checkPelletEvents(self) :
        pellet = self.pacman.eatPellets(self.pellets.pelletList)
        if pellet:
            self.pellets.numEaten += 1 
            self.updateScore(pellet.points)
            if self.ghost_mode:
                if self.pellets.numEaten == 30 :
                    self.ghosts.inky.startNode.allowAccess(RIGHT,self.ghosts.inky)
                if self.pellets.numEaten == 70 : 
                    self.ghosts.clyde.startNode.allowAccess(LEFT,self.ghosts.clyde)
            self.pellets.pelletList.remove(pellet)
            if pellet.name == POWERPELLET and self.ghost_mode:
                self.ghosts.startFreight()
            if self.pellets.isEmpty():
                self.flashBG = True
                self.hideEntities()
                self.endtime = time.time()
                self.pause.setPause(pauseTime=3,func=self.nextLevel)
    
    def checkGhostEvents(self) :
        # Chỉ kiểm tra ghost events khi ghost mode được bật
        if self.ghost_mode:
            for ghost in self.ghosts:
                if self.pacman.collideGhost(ghost):
                    if ghost.mode.current is FREIGHT:
                        self.pacman.visible = False
                        ghost.visible = False
                        self.updateScore(ghost.points) 
                        self.textgroup.addText(str(ghost.points),WHITE,ghost.position.x,ghost.position.y,8,time=1 )
                        self.ghosts.updatePoints()
                        self.pause.setPause(pauseTime=1,func=self.showEntities)
                        ghost.startSpawn()
                        self.nodes.allowHomeAccess(ghost) 
                    elif ghost.mode.current is not SPAWN : 
                        if self.pacman.alive : 
                            self.lives -= 1 
                            self.lifesprites.removeImage()
                            self.pacman.die()                            
                            self.ghosts.hide()
                            if self.lives <= 0 : 
                                # Kết thúc game hoàn toàn
                                total_pellets = len(self.pellets.pelletList) if hasattr(self, 'pellets') else 0                                
                                self.textgroup.showText(GAMEOVERTXT) 
                                self.pause.setPause(pauseTime=3,func=self.restartGame) 
                            else : 
                                self.pause.setPause(pauseTime=3,func=self.resetLevel) 
    
    def checkFruitEvents(self) :
        if self.pellets.numEaten == 50 or self.pellets.numEaten == 140 : 
            if self.fruit is None : 
                self.fruit = Fruit(self.nodes.getNodeFromTiles(9,20),self.level)
        if self.fruit is not None : 
            if self.pacman.collideCheck(self.fruit):
                self.updateScore(self.fruit.points)
                self.textgroup.addText(str(self.fruit.points),WHITE,self.fruit.position.x,self.fruit.position.y,8,1)
                fruitCaptured = False
                for fruit in self.fruitCaptured:
                    if fruit.get_offset() == self.fruit.image.get_offset():
                        fruitCaptured = True
                        break
                if not fruitCaptured:
                    self.fruitCaptured.append(self.fruit.image) 
                self.fruit = None 
            elif self.fruit.destroy:
                self.fruit = None
            
    def showEntities(self) :
        self.pacman.visible = True
        if self.ghost_mode:
            self.ghosts.show()
    
    def hideEntities(self):
        self.pacman.visible = False
        if self.ghost_mode:
            self.ghosts.hide()
    
    def nextLevel(self):
        self.showEntities()
        self.level += 1 
        self.pause.paused = True
        
        # Reset fruit khi chuyển level
        self.fruit = None
        
        # Khởi tạo lại game với level mới
        self.startGame()
        
        # Cập nhật UI
        self.textgroup.updateLevel(self.level)
        compute_once.curent_level = self.level
        self.reset_steps()
        
        # Reset pellet count để đảm bảo đếm đúng
        if hasattr(self, 'pellets'):
            self.pellets.numEaten = 0

    def restartGame(self):
        self.lives = 5 
        self.level = 0 
        self.pause.paused = True
        self.fruit = None 
        
        # Khởi tạo lại game từ level 0
        self.startGame()
        
        # Reset tất cả thông tin game
        self.score = 0  
        self.textgroup.updateScore(self.score)
        self.textgroup.updateLevel(self.level)
        self.textgroup.showText(READYTXT)
        self.lifesprites.resetLives(self.lives)
        self.fruitCaptured = []
        
        # Reset timer khi restart game hoàn toàn
        self.reset_timer()
        
        # Reset pellet count
        if hasattr(self, 'pellets'):
            self.pellets.numEaten = 0
        
        # Bắt đầu game mới trong analytics
        
    def resetLevel(self):
        self.pause.paused = True
        self.pacman.reset()
        if self.ghost_mode:
            self.ghosts.reset()
        self.fruit = None
        self.textgroup.showText(READYTXT)
        
        # Reset pellet count khi reset level
        if hasattr(self, 'pellets'):
            self.pellets.numEaten = 0
        # Không reset timer khi Pacman chết nhưng còn mạng
        
    def updateScore(self,points) : 
        self.score += points
        self.textgroup.updateScore(self.score)
        
        # Cập nhật điểm số trong analytics    
    def render(self)  :
        self.screen.blit(self.background,(0,0))
        
        # Add enhanced visual effects
        self._render_enhanced_effects(self.screen)
        
        self.pellets.render(self.screen)
        if self.fruit is not None:
            self.fruit.render(self.screen)       
        self.pacman.render(self.screen)
        if self.ghost_mode:
            self.ghosts.render(self.screen)
        self.textgroup.render(self.screen)
        
        # Enhanced life sprites rendering
        for i in range(len(self.lifesprites.images)):
            x = self.lifesprites.images[i].get_width() * i
            y = SCREENHEIGHT - self.lifesprites.images[i].get_height()
            
            # Add glow effect to life sprites
            glow_surface = pygame.Surface((self.lifesprites.images[i].get_width() + 4, 
                                        self.lifesprites.images[i].get_height() + 4), pygame.SRCALPHA)
            glow_color = (255, 255, 0, 50)  # Yellow glow
            pygame.draw.circle(glow_surface, glow_color, 
                             (glow_surface.get_width()//2, glow_surface.get_height()//2), 
                             self.lifesprites.images[i].get_width()//2 + 2)
            self.screen.blit(glow_surface, (x - 2, y - 2))
            
            self.screen.blit(self.lifesprites.images[i],(x,y))
            
        # Enhanced fruit captured rendering
        for i in range(len(self.fruitCaptured)) : 
            x = SCREENWIDTH - self.fruitCaptured[i].get_width()*(i+1)
            y = SCREENHEIGHT - self.fruitCaptured[i].get_height()
            
            # Add pulsing effect to captured fruits
            import math
            import time
            current_time = time.time()
            pulse_scale = 1.0 + 0.1 * math.sin(current_time * 4 + i)
            
            # Scale the fruit image
            scaled_fruit = pygame.transform.scale(self.fruitCaptured[i], 
                                                (int(self.fruitCaptured[i].get_width() * pulse_scale),
                                                 int(self.fruitCaptured[i].get_height() * pulse_scale)))
            
            # Center the scaled fruit
            offset_x = (scaled_fruit.get_width() - self.fruitCaptured[i].get_width()) // 2
            offset_y = (scaled_fruit.get_height() - self.fruitCaptured[i].get_height()) // 2
            
            self.screen.blit(scaled_fruit, (x - offset_x, y - offset_y))
            
        pygame.display.update()
    
    def handle_event(self, event ,auto = False):
        """Handle pygame events for the game"""
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_SPACE:
                self.pause.setPause(playerPaused=True)
            elif event.key == pygame.K_ESCAPE:
                compute_once.reset()
                self.pause.setPause(playerPaused=True)
    
    def render(self, surface):
        """Render game to a specific surface with enhanced effects"""
        if hasattr(self, 'background') and self.background:
            surface.blit(self.background, (0, 0))
        
        # Add dynamic background effects
        self._render_dynamic_effects(surface)
        
        if hasattr(self, 'nodes'):
            self.nodes.render(surface)
        if hasattr(self, 'pellets'):
            self.pellets.render(surface)
        if hasattr(self, 'pacman'):
            self.pacman.render(surface)
        if hasattr(self, 'ghosts') and self.ghost_mode:
            self.ghosts.render(surface)
        if hasattr(self, 'fruit') and self.fruit:
            self.fruit.render(surface)
        
        # Render Hybrid AI Display
        if hasattr(self, 'hybrid_ai_display') and self.hybrid_ai_display:
            self.hybrid_ai_display.draw(surface)
        
        # Removed textgroup render - score and level now shown in control panel
    
    def quit_game(self):
        """Quit the game"""
        self.running = False
    
    def set_ai_mode(self, ai_mode):
        self.ai_mode = ai_mode
    
    def set_few_pellets_mode(self, enabled: bool, count: int = 20):
        """Set few pellets mode"""
        self.few_pellets_mode = enabled
        self.few_pellets_count = max(7, min(100, count))  # Giới hạn từ 5 đến 100
    
    def set_ghost_mode(self, ghost_mode):
        self.ghost_mode = ghost_mode
        if hasattr(self, 'ghosts'):
            for ghost in self.ghosts.ghosts:
                ghost.visible = ghost_mode
            if not ghost_mode:
                self.ghosts.hide()
            else:
                self.ghosts.show()
    
    def set_algorithm(self, algorithm):
        self.algorithm = algorithm  # Cập nhật algorithm
        if hasattr(self, 'pacman') and self.pacman:
            from engine.algorithms_practical import (
                bfs , dfs , astar , ucs , 
                ids , greedy , heuristic_manhattan, heuristic_euclidean
            )       
            if algorithm == 'DFS':
                self.pacman.pathfinder_name = 'DFS'
                self.pacman.pathfinder = self._get_algorithm_with_heuristic(dfs )
            elif algorithm == 'IDS':
                self.pacman.pathfinder_name = 'IDS'
                self.pacman.pathfinder = self._get_algorithm_with_heuristic(ids )
            elif algorithm == 'UCS':
                self.pacman.pathfinder_name = 'UCS'
                self.pacman.pathfinder = self._get_algorithm_with_heuristic(ucs )
            elif algorithm == 'A*':
                self.pacman.pathfinder_name = 'A*'
                self.pacman.pathfinder = self._get_algorithm_with_heuristic(astar)
            elif algorithm == 'GREEDY':
                self.pacman.pathfinder_name = 'GREEDY'
                self.pacman.pathfinder = self._get_algorithm_with_heuristic(greedy)
            elif algorithm == 'Hill Climbing':
                self.pacman.pathfinder_name = 'Hill Climbing'
            elif algorithm == 'Genetic Algorithm':
                self.pacman.pathfinder_name = 'Genetic Algorithm'
                self.pacman.pathfinder = self._get_algorithm_with_heuristic(astar)  # Tạm dạng A* cho GA
            elif algorithm == 'Minimax':
                self.pacman.pathfinder_name = 'Minimax'
                self.pacman.pathfinder = None
            elif algorithm == 'Alpha-Beta':
                self.pacman.pathfinder_name = 'Alpha-Beta'
                self.pacman.pathfinder = None
            elif algorithm == 'A* Online':
                self.pacman.pathfinder_name = 'A* Online'
                self.pacman.pathfinder = None
            elif algorithm == 'BFS':  
                self.pacman.pathfinder_name = 'BFS'
                self.pacman.pathfinder = self._get_algorithm_with_heuristic(bfs )

            self.pacman.path = []
            self.pacman.locked_target_node = None
            self.pacman.previous_node = None
    
    def _get_algorithm_with_heuristic(self, algorithm_func):
        """Lấy algorithm function với heuristic tương ứng"""
        from engine.algorithms_practical import (
            heuristic_manhattan, heuristic_euclidean
        )
        
        if self.algorithm_heuristic == "MANHATTAN":
            return lambda start, pellets: algorithm_func(start, pellets, heuristic_manhattan)
        elif self.algorithm_heuristic == "EUCLIDEAN":
            return lambda start, pellets: algorithm_func(start, pellets, heuristic_euclidean)
        else:  # NONE
            return lambda start, pellets: algorithm_func(start, pellets, None)
    
    def set_algorithm_heuristic(self, heuristic):
        """Đặt heuristic cho tất cả thuật toán"""
        self.algorithm_heuristic = heuristic
        # Cập nhật pathfinder cho thuật toán hiện tại
        if hasattr(self, 'pacman') and self.pacman:
            # Reset path để áp dụng heuristic mới ngay lập tức
            self.pacman.path = []
            self.pacman.locked_target_node = None
            self.pacman.previous_node = None
            self.pacman.path_computed = False
            # Re-apply algorithm với heuristic mới
            self.set_algorithm(self.algorithm)
    
    def load_heuristic_from_config(self, config):
        """Load heuristic setting từ config"""
        if hasattr(config, 'get'):
            # Hỗ trợ cả tên cũ và tên mới
            self.algorithm_heuristic = config.get('algorithm_heuristic', config.get('bfs_heuristic', 'NONE'))
        else:
            self.algorithm_heuristic = "NONE"
            
            # Reset path computation flags
            self.pacman.path_computed = False
            self.pacman.original_pellet_count = 0
            
            # Cập nhật interval pathfinding cho thuật toán mới
            if hasattr(self.pacman, '_update_pathfind_interval'):
                self.pacman._update_pathfind_interval()
            
            # Reset timer khi thay đổi thuật toán (như restart game)
            self.reset_timer()
              
    def start_timer(self):
        """Bắt đầu đo thời gian game"""
        if not self.is_timer_running:
            self.start_time = time.time() - self.game_time
            self.is_timer_running = True
            self.timer_started_by_user = True            
    
    def stop_timer(self):
        """Dừng đo thời gian game và lưu thời gian hiện tại"""
        if self.is_timer_running and self.start_time:
            self.game_time = time.time() - self.start_time
            self.is_timer_running = False
    
    def reset_timer(self):
        """Reset thời gian game về 0"""
        self.start_time = None
        self.game_time = 0.0
        self.is_timer_running = False
        self.timer_started_by_user = False
    
    def get_game_time(self):
        """Lấy thời gian game hiện tại (tính bằng giây)"""
        if self.is_timer_running and self.start_time:
            return time.time() - self.start_time
        return self.game_time
    
    def get_formatted_time(self):
        """Lấy thời gian game được format (MM:SS)"""
        total_seconds = int(self.get_game_time())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_current_heuristic_info(self):
        """Lấy thông tin heuristic hiện tại"""
        return {
            'heuristic_name': self.algorithm_heuristic,
            'algorithm_name': self.algorithm,
            'is_custom': hasattr(self, 'custom_heuristic') and self.custom_heuristic is not None
        }
    
    def _track_step(self):
        """
        Đếm số bước di chuyển của Pacman
        - Detect khi Pacman di chuyển từ node này sang node khác
        - Phân biệt giữa AI steps và Player steps
        """
        if not self.pacman or not self.pacman.node:
            return
            
        current_position = (self.pacman.node.position.x, self.pacman.node.position.y)
        
        # Debug: In vị trí hiện tại mỗi 100 frames
        if hasattr(self, '_track_debug_counter'):
            self._track_debug_counter += 1
        else:
            self._track_debug_counter = 0
            
        # if self._track_debug_counter % 100 == 0:

        
        # Nếu có vị trí trước đó và khác vị trí hiện tại
        if self.last_step_position and self.last_step_position != current_position:
            # Tăng tổng số bước
            self.total_steps += 1
            
            if hasattr(self, 'ai_mode') and self.ai_mode:
                self.ai_steps += 1
            else:
                self.player_steps += 1
                
            # # Debug: In thông tin steps
            # if self.total_steps % 10 == 0:  # In mỗi 10 bước để debug
            #     mode = "AI" if (hasattr(self, 'ai_mode') and self.ai_mode) else "Player"
        
        # Cập nhật vị trí cuối cùng
        self.last_step_position = current_position
    
    def get_step_info(self):
        """
        Lấy thông tin về số bước
        Returns:
            dict: Thông tin chi tiết về steps
        """
        return {
            'total_steps': self.total_steps,
            'ai_steps': self.ai_steps,
            'player_steps': self.player_steps,
            'current_mode': 'AI' if (hasattr(self, 'ai_mode') and self.ai_mode) else 'Player'
        }
    
    def reset_steps(self):
        self.total_steps = 0
        self.ai_steps = 0
        self.player_steps = 0
        self.last_step_position = None
    