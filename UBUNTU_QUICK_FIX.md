# ⚡ Quick Fix - Chạy training trên Ubuntu

## ✅ Đã fix trong `optimized_training.py`:
- Set `SDL_VIDEODRIVER=dummy` trước khi import pygame
- Use matplotlib backend 'Agg' cho headless mode
- Không cần display window

## 📋 Các bước chạy:

### 1. Upload file mới lên EC2:
```bash
# Từ local machine
scp -i "pacman-training.pem" optimized_training.py ubuntu@<EC2-DNS>:~/GamePacman/
```

### 2. Chạy training (KHÔNG cần set env variables):
```bash
cd ~/GamePacman
source venv/bin/activate

# Cách 1: Chạy trực tiếp
python3 optimized_training.py

# Cách 2: Với screen
screen -S training
python3 optimized_training.py
# Ctrl+A+D để detach
```

## ✨ Không cần làm gì thêm!

Script đã tự động:
- ✓ Set SDL_VIDEODRIVER=dummy
- ✓ Set SDL_AUDIODRIVER=dummy  
- ✓ Use matplotlib Agg backend
- ✓ Create virtual surface thay vì display window

## 🎯 Expected Output:

```
pygame 2.5.2 (SDL 2.30.0, Python 3.12.3)
Hello from the pygame community. https://www.pygame.org/contribute.html

OPTIMIZED Q-LEARNING TRAINING FOR PACMAN
================================================================================
✓ Headless mode activated
TRAINING CONFIGURATION:
   max_episodes: 20000
   save_interval: 100
   ...
```

## 🔍 Verify training đang chạy:

```bash
# Xem log real-time
tail -f training.log  # (nếu dùng nohup)

# Hoặc check trong screen
screen -r training

# Check Q-table size
ls -lh q_table*.json

# Monitor CPU/RAM
htop
```

## 💡 Tips:

1. **Training tự động detect headless mode** - không cần config thêm
2. **Plots vẫn được save** vào `reward_images/` 
3. **Q-table auto-save** mỗi 100 episodes
4. **Press Ctrl+C** để stop gracefully (sẽ save progress)

---

**Ready to train! 🚀**

