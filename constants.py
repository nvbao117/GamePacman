# =============================================================================
# CONSTANTS.PY - CÁC HẰNG SỐ CỦA GAME PAC-MAN
# =============================================================================
# File này chứa tất cả các hằng số được sử dụng trong toàn bộ game
# bao gồm kích thước màn hình, màu sắc, hướng di chuyển, và các ID entity

# =============================================================================
# ĐƯỜNG DẪN TÀI NGUYÊN
# =============================================================================
G_MENU = "assets/images/bg_menu.jpg"      # Background menu chính
THEME_IMG = "assets/images/theme.png"     # Hình ảnh theme
BUTTON_IMG = "assets/images/button.png"   # Hình ảnh button

# =============================================================================
# KÍCH THƯỚC MÀN HÌNH VÀ TILE
# =============================================================================
NROWS = 36          # Số hàng trong maze (36 tiles)
NCOLS = 28          # Số cột trong maze (28 tiles)
TILEWIDTH = 16      # Chiều rộng mỗi tile (pixel)
TILEHEIGHT = 16     # Chiều cao mỗi tile (pixel)
SCREENWIDTH = NCOLS*TILEWIDTH    # Chiều rộng màn hình game (448px)
SCREENHEIGHT = NROWS*TILEHEIGHT  # Chiều cao màn hình game (576px)
SCREENSIZE = (SCREENWIDTH, SCREENHEIGHT)  # Kích thước màn hình game
PANEL_WIDTH = 200   # Chiều rộng panel điều khiển

# =============================================================================
# MÀU SẮC
# =============================================================================
BLACK = (0, 0, 0)           # Màu đen
YELLOW = (255, 255, 0)      # Màu vàng (Pac-Man)
WHITE = (255, 255, 255)     # Màu trắng
RED = (255, 0, 0)           # Màu đỏ (Blinky)
PINK = (255,100,150)        # Màu hồng (Pinky)
TEAL = (100,255,255)        # Màu xanh lá cây nhạt (Inky)
ORANGE = (230,190,40)       # Màu cam (Clyde)
GREEN = (0, 255, 0)         # Màu xanh lá cây

# =============================================================================
# HƯỚNG DI CHUYỂN
# =============================================================================
STOP = 0        # Dừng lại
UP = 1          # Lên trên
DOWN = -1       # Xuống dưới
LEFT = 2        # Sang trái
RIGHT = -2      # Sang phải
PORTAL = 3      # Cổng teleport

# =============================================================================
# ID CÁC ENTITY TRONG GAME
# =============================================================================
PACMAN = 0      # Pac-Man
PELLET = 1      # Pellet thường (điểm nhỏ)
POWERPELLET = 2 # Power pellet (điểm lớn, ăn được ghost)
GHOST = 3       # Ghost chung
BLINKY = 4      # Ghost đỏ (Blinky)
PINKY = 5       # Ghost hồng (Pinky)
INKY = 6        # Ghost xanh (Inky)
CLYDE = 7       # Ghost cam (Clyde)
FRUIT = 8       # Trái cây

# =============================================================================
# CHẾ ĐỘ CỦA GHOST
# =============================================================================
SCATTER = 0     # Chế độ tản mát (chạy về góc)
CHASE = 1       # Chế độ đuổi theo (đuổi theo Pac-Man)
FREIGHT = 2     # Chế độ sợ hãi (bị ăn được)
SPAWN = 3       # Chế độ hồi sinh (quay về nhà)

# =============================================================================
# ID CÁC TEXT HIỂN THỊ
# =============================================================================
SCORETXT = 0        # Text hiển thị điểm
LEVELTXT = 1        # Text hiển thị level
READYTXT = 2        # Text "READY!"
PAUSETXT = 3        # Text "PAUSED"
GAMEOVERTXT = 4     # Text "GAME OVER"
WINTXT = 5          # Text "YOU WIN!"
LEVELCOMPLETETXT = 6 # Text "LEVEL COMPLETE!"

