# 🐧 HƯỚNG DẪN TRAIN Q-LEARNING TRÊN UBUNTU

## 📋 YÊU CẦU HỆ THỐNG

- Ubuntu 20.04+ (hoặc Debian-based Linux)
- Python 3.8+
- 8GB RAM (khuyến nghị 16GB cho 20k episodes)
- 5GB disk space

---

## 🔧 BƯỚC 1: CÀI ĐẶT DEPENDENCIES

### 1.1. Update system
```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2. Cài Python và pip
```bash
sudo apt install python3 python3-pip python3-venv -y
```

### 1.3. Cài dependencies cho Pygame (headless)
```bash
# SDL2 libraries (cần thiết cho pygame headless)
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev -y

# Fonts
sudo apt install fonts-dejavu fonts-liberation -y

# Build tools
sudo apt install build-essential libfreetype6-dev libpng-dev -y
```

---

## 📦 BƯỚC 2: SETUP PYTHON ENVIRONMENT

### 2.1. Tạo virtual environment
```bash
cd ~/GamePacman
python3 -m venv venv
source venv/bin/activate
```

### 2.2. Upgrade pip
```bash
pip install --upgrade pip
```

### 2.3. Cài Python packages
```bash
pip install pygame numpy matplotlib
```

**Verify installation:**
```bash
python3 -c "import pygame; import numpy; import matplotlib; print('✅ All packages installed')"
```

---

## 🚀 BƯỚC 3: SETUP HEADLESS MODE

### 3.1. Set environment variables (tạm thời)
```bash
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
export MPLBACKEND=Agg
```

### 3.2. Hoặc thêm vào ~/.bashrc (vĩnh viễn)
```bash
echo 'export SDL_VIDEODRIVER=dummy' >> ~/.bashrc
echo 'export SDL_AUDIODRIVER=dummy' >> ~/.bashrc
echo 'export MPLBACKEND=Agg' >> ~/.bashrc
source ~/.bashrc
```

### 3.3. Verify headless mode
```bash
python3 -c "import os; print('SDL_VIDEODRIVER:', os.environ.get('SDL_VIDEODRIVER')); import pygame; pygame.init(); print('✅ Headless mode OK')"
```

---

## 🎮 BƯỚC 4: CHUẨN BỊ PROJECT

### 4.1. Upload code lên Ubuntu
**Option 1: SCP từ Windows**
```bash
# Trên Windows PowerShell
scp -r D:\AI_final\GamePacman username@ubuntu-ip:~/
```

**Option 2: Git clone**
```bash
git clone <your-repo-url> ~/GamePacman
cd ~/GamePacman
```

**Option 3: Zip và upload**
```bash
# Trên Windows: Zip folder GamePacman
# Upload qua FileZilla hoặc WinSCP
# Trên Ubuntu:
cd ~
unzip GamePacman.zip
cd GamePacman
```

### 4.2. Verify project structure
```bash
ls -la
# Phải thấy: optimized_training.py, engine/, objects/, etc.
```

### 4.3. Xóa data cũ (nếu có)
```bash
rm -f q_table.json
rm -rf training_stats/*
rm -rf reward_images/*
```

---

## 🏃 BƯỚC 5: CHẠY TRAINING

### 5.1. Test nhanh (1 episode)
```bash
python3 -c "
from engine.game import Game
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
game = Game(algorithm='Q-Learning')
game.ai_mode = True
game.initialize_game()
print('✅ Game can run!')
"
```

### 5.2. Chạy training (chế độ background)

**Option A: Dùng `nohup`**
```bash
nohup python3 optimized_training.py > training.log 2>&1 &
echo $! > training.pid
```

**Option B: Dùng `screen`**
```bash
# Cài screen
sudo apt install screen -y

# Tạo session mới
screen -S pacman_training

# Trong screen, chạy:
python3 optimized_training.py

# Detach: Ctrl+A, rồi D
# Reattach: screen -r pacman_training
```

**Option C: Dùng `tmux`**
```bash
# Cài tmux
sudo apt install tmux -y

# Tạo session
tmux new -s training

# Chạy training
python3 optimized_training.py

# Detach: Ctrl+B, rồi D
# Reattach: tmux attach -t training
```

---

## 📊 BƯỚC 6: MONITOR TRAINING

### 6.1. Theo dõi log
```bash
# Nếu dùng nohup
tail -f training.log

# Xem 50 dòng cuối
tail -n 50 training.log

# Grep epsilon values
grep "epsilon" training.log | tail -20
```

### 6.2. Check process
```bash
# Xem process đang chạy
ps aux | grep python

# Kill process nếu cần
kill -9 $(cat training.pid)
```

### 6.3. Monitor resources
```bash
# CPU, RAM usage
top -p $(pgrep -f optimized_training)

# Hoặc dùng htop
sudo apt install htop -y
htop
```

### 6.4. Check tiến độ
```bash
# Xem Q-table size
ls -lh q_table.json

# Count states in Q-table
cat q_table.json | grep "\"state\"" | wc -l

# Xem reward images
ls -lh reward_images/

# Latest stats
ls -lt training_stats/ | head -5
```

---

## 💾 BƯỚC 7: DOWNLOAD KẾT QUẢ VỀ WINDOWS

### 7.1. Download qua SCP
```bash
# Trên Windows PowerShell
scp username@ubuntu-ip:~/GamePacman/q_table.json D:\AI_final\GamePacman\
scp -r username@ubuntu-ip:~/GamePacman/reward_images D:\AI_final\GamePacman\
scp -r username@ubuntu-ip:~/GamePacman/training_stats D:\AI_final\GamePacman\
```

### 7.2. Download qua WinSCP/FileZilla
- Connect tới Ubuntu server
- Navigate tới `~/GamePacman`
- Download: `q_table.json`, `reward_images/`, `training_stats/`

### 7.3. Zip và download
```bash
# Trên Ubuntu
cd ~/GamePacman
tar -czf training_results.tar.gz q_table.json reward_images/ training_stats/

# Download file zip về Windows
```

---

## 🔥 TRAINING 20K EPISODES - QUICK START

```bash
# 1. Activate environment
source ~/GamePacman/venv/bin/activate

# 2. Set headless mode
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy

# 3. Start training in background
cd ~/GamePacman
nohup python3 optimized_training.py > training_20k.log 2>&1 &
echo $! > training.pid

# 4. Monitor
tail -f training_20k.log

# 5. Check progress (mỗi 30 phút)
ls -lh q_table.json
tail -n 50 training_20k.log | grep "COMPLETED"
```

---

## ⏱️ THỜI GIAN DỰ KIẾN (20K EPISODES)

### Hardware tham khảo:
- **CPU:** 4 cores, 2.5GHz
- **RAM:** 8GB
- **Ubuntu 20.04**

### Timeline:
```
Stage 1 (3k episodes):   ~45-60 phút    (Completed: 3k/20k)
Stage 2 (5k episodes):   ~1.5-2 giờ     (Completed: 8k/20k)
Stage 3 (6k episodes):   ~2-3 giờ       (Completed: 14k/20k)
Stage 4 (6k episodes):   ~2.5-3.5 giờ   (Completed: 20k/20k)
──────────────────────────────────────────────────
TOTAL:                   ~7-9 giờ
```

---

## ❓ TROUBLESHOOTING

### Lỗi: "pygame.error: No available video device"
```bash
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
```

### Lỗi: "No module named 'pygame'"
```bash
source venv/bin/activate
pip install pygame
```

### Lỗi: "Permission denied"
```bash
chmod +x optimized_training.py
```

### Lỗi: Out of memory
```bash
# Giảm số episodes hoặc tăng RAM
# Check RAM usage:
free -h
```

### Training bị dừng giữa chừng
```bash
# Training sẽ tự động save Q-table mỗi 300-600 episodes
# Load lại Q-table và continue (cần code thêm resume logic)
```

---

## 🎯 KẾT QUẢ MONG ĐỢI SAU 20K EPISODES

```
✅ Q-table size: ~5,000-10,000 states
✅ Win rate: 10-25%
✅ Average score: 1,500-3,000
✅ File size: q_table.json (~3-8 MB)
✅ Reward curves: Tăng rõ rệt qua các stages
```

---

## 📞 SUPPORT

Nếu gặp vấn đề:
1. Check `training.log` file
2. Verify headless mode: `echo $SDL_VIDEODRIVER`
3. Check disk space: `df -h`
4. Check RAM: `free -h`

**Good luck with 20k episodes training! 🚀**

