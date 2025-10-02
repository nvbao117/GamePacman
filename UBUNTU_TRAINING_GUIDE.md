# 🚀 Hướng dẫn Train Q-Learning trên Ubuntu CLI

## 📋 Yêu cầu hệ thống

### 1. **Cài đặt Python và Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Cài đặt Python 3.8+
sudo apt install python3 python3-pip python3-venv -y

# Cài đặt các thư viện cần thiết cho Pygame headless
sudo apt install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    python3-dev
```

### 2. **Tạo Virtual Environment**
```bash
# Tạo venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. **Cài đặt Dependencies**
```bash
# Cài đặt từ requirements.txt (nếu có)
pip install -r requirements.txt

# Hoặc cài thủ công
pip install pygame numpy matplotlib
```

## 🎯 Các bước Train

### **Bước 1: Upload Code lên Ubuntu**
```bash
# Sử dụng scp hoặc git
scp -r GamePacman/ user@ubuntu-server:/path/to/directory
# Hoặc
git clone your-repo-url
```

### **Bước 2: Cấu hình Headless Mode**
```bash
# Set environment variables (đã có trong train_headless.py)
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
```

### **Bước 3: Chạy Training**
```bash
# Activate venv
source venv/bin/activate

# Chạy training
python3 train_headless.py

# Hoặc chạy trong background với nohup
nohup python3 train_headless.py > training.log 2>&1 &

# Hoặc dùng screen/tmux để có thể detach
screen -S qlearning_training
python3 train_headless.py
# Ctrl+A+D để detach
# screen -r qlearning_training để re-attach
```

### **Bước 4: Theo dõi Training**
```bash
# Xem log real-time
tail -f training.log

# Xem tiến độ
watch -n 5 'tail -20 training.log'

# Kiểm tra file output
ls -lh q_table*.json
ls -lh training_stats/
```

## 📊 Output Files

Training sẽ tạo các files:
- **`q_table.json`**: Q-table chính (được save mỗi 50 episodes)
- **`training_stats/*.json`**: Statistics của từng checkpoint
- **`reward_images/*.png`**: Biểu đồ reward curves
- **`training.log`**: Log file (nếu dùng nohup)

## ⚙️ Tuỳ chỉnh Configuration

Sửa trong `train_headless.py`:
```python
config = {
    'max_episodes': 3000,           # Tăng để train lâu hơn
    'save_interval': 50,            # Save mỗi N episodes
    'max_steps_per_episode': 2500,  # Max steps mỗi episode
    'render': False,                # PHẢI = False cho headless
    'few_pellets_mode': False,      # True = ít pellets (train nhanh)
    'few_pellets_count': 30,        
    'adaptive_learning': True,      
    'performance_window': 100       
}
```

## 🐛 Troubleshooting

### **Lỗi: "No video mode"**
```bash
# Đảm bảo set environment variables
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
```

### **Lỗi: "libSDL2 not found"**
```bash
sudo apt install libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0
```

### **Lỗi: "Permission denied"**
```bash
chmod +x train_headless.py
```

### **Memory leak / High RAM usage**
```bash
# Giảm performance_window
# Giảm max_steps_per_episode
# Clear cache định kỳ trong code
```

### **Training quá chậm**
```bash
# Tắt render (đã tắt)
# Giảm FPS limit trong code
# Dùng few_pellets_mode = True
# Tăng epsilon_decay để exploit sớm hơn
```

## 📈 Monitoring Training Progress

### **Real-time monitoring**
```bash
# Terminal 1: Chạy training
python3 train_headless.py

# Terminal 2: Monitor
watch -n 2 'tail -30 training.log'

# Terminal 3: Kiểm tra resource
htop
```

### **Check checkpoint files**
```bash
# Liệt kê Q-tables đã save
ls -lht q_table*.json | head -10

# Xem size Q-table
du -h q_table.json

# Count số states đã học
grep -o '"state"' q_table.json | wc -l
```

## 🔄 Resume Training

Nếu training bị ngắt, Q-table đã được save tự động. Chỉ cần chạy lại:
```bash
python3 train_headless.py
```

Code sẽ tự động load `q_table.json` nếu tồn tại.

## 📦 Download Results về Local

```bash
# Download Q-table
scp user@ubuntu:/path/to/q_table.json ./

# Download statistics
scp -r user@ubuntu:/path/to/training_stats ./

# Download reward plots
scp -r user@ubuntu:/path/to/reward_images ./
```

## 💡 Tips

1. **Dùng `screen` hoặc `tmux`** để training không bị ngắt khi mất kết nối SSH
2. **Set `max_episodes` cao** (5000-10000) cho kết quả tốt
3. **Monitor RAM usage** - giảm `performance_window` nếu RAM cao
4. **Backup Q-table thường xuyên** - scp về local mỗi vài giờ
5. **Dùng `few_pellets_mode=True`** để test nhanh cấu hình
6. **Check log định kỳ** để đảm bảo training đang tiến bộ

## 🎮 Test Q-table sau khi Train

Sau khi train xong, download Q-table về và test:
```bash
# Trên local machine
python3 main.py
# Chọn Q-Learning algorithm
# Q-table sẽ được load tự động
```

---

**Good luck with training! 🚀**

