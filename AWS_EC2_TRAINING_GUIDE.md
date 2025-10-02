# ☁️ Hướng dẫn Train Q-Learning trên AWS EC2

## 🚀 SETUP AWS EC2 INSTANCE

### **Bước 1: Tạo EC2 Instance**

#### **1.1. Đăng nhập AWS Console**
- Truy cập: https://console.aws.amazon.com/
- Vào **EC2 Dashboard** → Click **Launch Instance**

#### **1.2. Chọn cấu hình:**

**Instance Type (Khuyến nghị):**
```
Cho 30k episodes:
├─ t3.medium (2 vCPU, 4GB RAM) - $0.0416/hour
├─ t3.large (2 vCPU, 8GB RAM) - $0.0832/hour (RECOMMENDED)
└─ t3.xlarge (4 vCPU, 16GB RAM) - $0.1664/hour (nếu train nhiều)

Estimated cost cho 20 giờ training:
- t3.large: ~$1.66 USD
```

**AMI (Operating System):**
```
- Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
- 64-bit (x86)
- Free tier eligible
```

**Storage:**
```
- Volume Type: gp3 (General Purpose SSD)
- Size: 10 GB (Free tier: 30GB)
- Minimum cần: 5 GB
- Recommended: 10 GB
```

**Security Group:**
```
Inbound Rules:
- SSH (Port 22) - Your IP only
- Custom TCP (Port 8888) - Your IP (nếu dùng Jupyter)

Outbound Rules:
- All traffic
```

**Key Pair:**
```
- Create new key pair hoặc dùng existing
- Type: RSA
- Format: .pem
- Download và lưu an toàn: pacman-training.pem
```

### **Bước 2: Connect tới EC2**

#### **2.1. Set permissions cho key file (local machine):**
```bash
# Windows (PowerShell)
icacls pacman-training.pem /inheritance:r
icacls pacman-training.pem /grant:r "%USERNAME%:R"

# Linux/Mac
chmod 400 pacman-training.pem
```

#### **2.2. SSH vào EC2:**
```bash
# Get Public DNS từ EC2 Console
# VD: ec2-xx-xxx-xxx-xxx.compute-1.amazonaws.com

ssh -i "pacman-training.pem" ubuntu@<YOUR-EC2-PUBLIC-DNS>

# Example:
ssh -i "pacman-training.pem" ubuntu@ec2-54-123-45-67.compute-1.amazonaws.com
```

## 📦 SETUP ENVIRONMENT TRÊN EC2

### **Bước 3: Update System & Install Dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python và build tools
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    htop \
    screen \
    vim

# Install SDL2 libraries cho Pygame headless
sudo apt install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    python3-dev

# Install system monitoring tools
sudo apt install -y sysstat iotop
```

### **Bước 4: Upload Code lên EC2**

#### **Option 1: SCP (Recommended cho code nhỏ)**
```bash
# Từ local machine
scp -i "pacman-training.pem" -r GamePacman/ ubuntu@<EC2-DNS>:~/

# Example:
scp -i "pacman-training.pem" -r GamePacman/ ubuntu@ec2-54-123-45-67.compute-1.amazonaws.com:~/
```

#### **Option 2: Git Clone (Recommended nếu có repo)**
```bash
# Trên EC2
cd ~
git clone https://github.com/your-username/GamePacman.git
cd GamePacman
```

#### **Option 3: S3 (Cho file lớn)**
```bash
# Upload lên S3 từ local
aws s3 cp GamePacman.zip s3://your-bucket/

# Download từ S3 trên EC2
aws s3 cp s3://your-bucket/GamePacman.zip .
unzip GamePacman.zip
```

### **Bước 5: Setup Python Environment**

```bash
# Di chuyển vào thư mục project
cd ~/GamePacman

# Tạo virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install pygame numpy matplotlib

# Verify installation
python3 -c "import pygame; print('Pygame version:', pygame.version.ver)"
```

## 🎮 CHẠY TRAINING

### **Bước 6: Configure Training**

```bash
# Edit config trong train_headless.py nếu cần
nano train_headless.py

# Hoặc dùng vim
vim train_headless.py
```

**Recommended config cho EC2:**
```python
config = {
    'max_episodes': 30000,          # Train 30k episodes
    'save_interval': 100,           # Save mỗi 100 episodes (giảm I/O)
    'max_steps_per_episode': 2500,
    'render': False,                # MUST be False
    'few_pellets_mode': False,
    'adaptive_learning': True,
    'performance_window': 100
}
```

### **Bước 7: Start Training với Screen**

#### **7.1. Create screen session:**
```bash
# Tạo screen session mới
screen -S pacman_training

# Activate venv trong screen
source venv/bin/activate

# Set environment variables
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
```

#### **7.2. Start training:**
```bash
# Run training
python3 train_headless.py 2>&1 | tee training.log

# Hoặc nếu muốn chạy background
nohup python3 train_headless.py > training.log 2>&1 &
```

#### **7.3. Detach screen (không mất training):**
```
Press: Ctrl + A, then D
```

#### **7.4. Re-attach screen:**
```bash
# List screens
screen -ls

# Attach lại
screen -r pacman_training
```

## 📊 MONITORING

### **Bước 8: Monitor Training Progress**

#### **8.1. Monitor trong terminal khác:**
```bash
# SSH connection thứ 2
ssh -i "pacman-training.pem" ubuntu@<EC2-DNS>

# Watch training log
tail -f ~/GamePacman/training.log

# Hoặc
watch -n 5 'tail -30 ~/GamePacman/training.log'
```

#### **8.2. Monitor system resources:**
```bash
# CPU, RAM usage
htop

# Disk usage
df -h

# I/O stats
iostat -x 5

# Network usage
iftop
```

#### **8.3. Check Q-table size:**
```bash
# Size
ls -lh ~/GamePacman/q_table*.json

# Number of states
grep -o '"state"' ~/GamePacman/q_table.json | wc -l

# Latest updates
ls -lt ~/GamePacman/training_stats/ | head -10
```

### **Bước 9: Backup Q-table về Local (Định kỳ)**

```bash
# Từ local machine, download Q-table
scp -i "pacman-training.pem" ubuntu@<EC2-DNS>:~/GamePacman/q_table.json ./q_table_backup_$(date +%Y%m%d).json

# Download toàn bộ results
scp -i "pacman-training.pem" -r ubuntu@<EC2-DNS>:~/GamePacman/training_stats ./
scp -i "pacman-training.pem" -r ubuntu@<EC2-DNS>:~/GamePacman/reward_images ./

# Hoặc dùng rsync (sync incremental)
rsync -avz -e "ssh -i pacman-training.pem" ubuntu@<EC2-DNS>:~/GamePacman/q_table.json ./
```

## 💰 COST OPTIMIZATION

### **Bước 10: Tối ưu chi phí**

#### **10.1. Use Spot Instances (tiết kiệm 70-90%):**
```
- Request Spot Instance thay vì On-Demand
- Price: ~$0.01-0.02/hour (thay vì $0.08)
- Risk: Có thể bị terminate nếu giá tăng
- Solution: Save Q-table thường xuyên, dễ resume
```

#### **10.2. Stop instance khi không dùng:**
```bash
# Stop (không bị charge compute)
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Start lại khi cần
aws ec2 start-instances --instance-ids i-1234567890abcdef0
```

#### **10.3. Schedule training:**
```bash
# Tạo cron job để auto-start training vào lúc rẻ
crontab -e

# Add:
0 2 * * * cd ~/GamePacman && source venv/bin/activate && python3 train_headless.py
```

## 🔧 TROUBLESHOOTING

### **Common Issues:**

#### **1. Out of Memory:**
```bash
# Check memory
free -h

# Giải pháp:
# - Giảm performance_window trong config
# - Upgrade sang instance lớn hơn
# - Enable swap (không khuyến nghị)
```

#### **2. Disk Full:**
```bash
# Check disk
df -h

# Clean up
rm -rf ~/GamePacman/reward_images/*.png  # Xóa plots cũ
rm ~/GamePacman/training_stats/*.json    # Xóa stats cũ (đã backup)

# Compress Q-table
gzip ~/GamePacman/q_table.json
```

#### **3. SSH Connection Timeout:**
```bash
# Thêm vào ~/.ssh/config
Host ec2
    HostName <EC2-DNS>
    User ubuntu
    IdentityFile ~/path/to/pacman-training.pem
    ServerAliveInterval 60
    ServerAliveCountMax 120
```

#### **4. Training bị stuck:**
```bash
# Check process
ps aux | grep python3

# Kill nếu cần
pkill -f train_headless.py

# Check logs
tail -100 training.log
```

## 📤 DOWNLOAD RESULTS

### **Bước 11: Download kết quả về local**

```bash
# Download Q-table
scp -i "pacman-training.pem" ubuntu@<EC2-DNS>:~/GamePacman/q_table.json ./

# Download all results
scp -i "pacman-training.pem" -r ubuntu@<EC2-DNS>:~/GamePacman/training_stats ./
scp -i "pacman-training.pem" -r ubuntu@<EC2-DNS>:~/GamePacman/reward_images ./
scp -i "pacman-training.pem" ubuntu@<EC2-DNS>:~/GamePacman/training.log ./

# Hoặc tạo archive trước
ssh -i "pacman-training.pem" ubuntu@<EC2-DNS> "cd ~/GamePacman && tar -czf results.tar.gz q_table.json training_stats/ reward_images/ training.log"
scp -i "pacman-training.pem" ubuntu@<EC2-DNS>:~/GamePacman/results.tar.gz ./
```

## 🧹 CLEANUP

### **Bước 12: Terminate instance sau khi xong**

```bash
# Từ AWS Console:
# EC2 → Instances → Select instance → Instance State → Terminate

# Hoặc dùng AWS CLI:
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0
```

⚠️ **LƯU Ý: Terminate sẽ XÓA mất data! Backup trước!**

## 📋 CHECKLIST

### **Trước khi train:**
- [ ] EC2 instance đã setup xong
- [ ] Code đã upload
- [ ] Dependencies đã install
- [ ] Config đã set đúng (render=False)
- [ ] Screen session đã tạo
- [ ] Backup strategy đã có

### **Trong khi train:**
- [ ] Monitor CPU/RAM mỗi 1-2 giờ
- [ ] Backup Q-table mỗi 5000 episodes
- [ ] Check logs để đảm bảo progress
- [ ] Monitor disk space

### **Sau khi train xong:**
- [ ] Download Q-table
- [ ] Download statistics
- [ ] Download plots
- [ ] Download logs
- [ ] Terminate instance
- [ ] Verify downloaded files

## 💡 TIPS & BEST PRACTICES

1. **Use t3.large** - Balance giữa cost và performance
2. **Enable detailed CloudWatch monitoring** - Track metrics
3. **Set billing alerts** - Tránh surprise costs
4. **Use screen/tmux** - Không mất training khi disconnect
5. **Backup mỗi 2-3 giờ** - SCP Q-table về local
6. **Compress old files** - Tiết kiệm disk space
7. **Use spot instances** - Tiết kiệm 70-90% cost
8. **Schedule training** - Chạy vào lúc rẻ (off-peak hours)
9. **Monitor logs** - Đảm bảo training đang progress
10. **Test trước** - Chạy 100 episodes để verify setup

## 💵 COST ESTIMATION

### **Training 30k episodes trên t3.large:**

```
Instance: t3.large ($0.0832/hour)
Duration: ~15-20 hours
Cost: 20 hours × $0.0832 = ~$1.66 USD

Storage: 10 GB gp3 ($0.08/GB-month)
Cost: ~$0.01 USD (1 day)

Data Transfer: ~500 MB download
Cost: ~$0.05 USD

Total: ~$1.70 - $2.00 USD
```

### **Với Spot Instance (70% off):**
```
Total: ~$0.50 - $0.60 USD
```

## 🎯 QUICK START SCRIPT

```bash
#!/bin/bash
# save as setup_ec2.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git screen
sudo apt install -y libsdl2-dev libsdl2-image-dev python3-dev

# Setup project
cd ~
git clone YOUR_REPO_URL GamePacman
cd GamePacman
python3 -m venv venv
source venv/bin/activate
pip install pygame numpy matplotlib

# Setup environment
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy

# Start training in screen
screen -S training
python3 train_headless.py 2>&1 | tee training.log

# Ctrl+A+D to detach
```

---

**Ready to train! 🚀 Good luck!**

