# 📊 Performance Logger - Module Thống Kê và Xuất Excel

## 🎯 Mô tả
Module `PerformanceLogger` được thiết kế để thống kê hiệu suất của các thuật toán AI trong game Pacman và xuất kết quả ra file Excel để so sánh.

## 🚀 Tính năng

### ✅ Đã hoàn thành:
- **Ghi nhận dữ liệu game**: Thuật toán, thời gian, số bước, food ăn được, số lần chết, tỉ lệ thắng
- **Xuất Excel**: Tự động tạo file `algorithm_comparison.xlsx` với format đẹp
- **Append dữ liệu**: Thêm dữ liệu mới vào file hiện có thay vì ghi đè
- **Phím tắt**: Nhấn **E** trong comparison mode để export Excel
- **Thống kê tổng hợp**: In ra console các chỉ số hiệu suất
- **Styling Excel**: Header màu xanh, alternating row colors, auto-fit columns

## 🎮 Cách sử dụng

### 1. Trong Comparison Mode:
- Chạy game với các thuật toán khác nhau (BFS, DFS, A*, UCS, IDS, Greedy)
- Dữ liệu được tự động ghi nhận trong quá trình chơi
- Nhấn **E** để xuất kết quả ra Excel
- Nhấn **ESC** để quay lại menu

### 2. Dữ liệu được ghi nhận:
- **Algorithm**: Tên thuật toán (BFS, DFS, A*, UCS, IDS, Greedy)
- **Avg Time (ms)**: Thời gian chạy trung bình (milliseconds)
- **Steps**: Số bước di chuyển để hoàn thành
- **Food Eaten**: Số food ăn được
- **Deaths**: Số lần Pacman bị ghost bắt
- **Win Rate (%)**: Tỉ lệ thắng (100% nếu thắng, 0% nếu thua)
- **Score**: Điểm số cuối cùng
- **Level**: Level đạt được
- **Timestamp**: Thời gian chơi

### 3. File Excel Output:
- **Tên file**: `algorithm_comparison.xlsx`
- **Vị trí**: Cùng thư mục với game
- **Format**: Professional với header màu xanh, alternating rows
- **Append**: Dữ liệu mới được thêm vào cuối file

## 🔧 Cài đặt Dependencies

```bash
pip install openpyxl
```

## 📁 Cấu trúc File

```
GamePacman/
├── engine/
│   ├── performance_logger.py    # Module chính
│   └── algorithms_practical.py  # Các thuật toán AI
├── states/
│   ├── comparison_state.py      # Tích hợp PerformanceLogger
│   └── comparison_layout.py     # UI layout
├── requirements.txt             # Dependencies
└── algorithm_comparison.xlsx    # File Excel output
```

## 🎯 API Usage

### Khởi tạo:
```python
from engine.performance_logger import PerformanceLogger
logger = PerformanceLogger("algorithm_comparison.xlsx")
```

### Bắt đầu session:
```python
logger.start_game_session("BFS")
```

### Cập nhật thống kê:
```python
logger.update_game_stats(steps=50, food_eaten=20, score=200)
logger.update_game_stats(deaths=1)
```

### Kết thúc session:
```python
logger.end_game_session(is_win=True, final_score=200)
```

### Xuất Excel:
```python
success = logger.export_to_excel()
```

### In thống kê:
```python
logger.print_summary()
```

## 🎮 Controls trong Game

- **↑↓←→**: Điều khiển player (bên phải)
- **SPACE**: Tạm dừng/tiếp tục game
- **ESC**: Quay lại menu chính
- **R**: Restart cả 2 game
- **E**: Export kết quả ra Excel

## 📊 Ví dụ Output

### Console Output:
```
Started game session with BFS
Updated steps: 50
Updated food_eaten: 20
Updated score: 200
Updated deaths: 1
Game session ended - Algorithm: BFS, Time: 111.43ms, Steps: 50, Food: 20, Deaths: 1, Win: Yes

================================================================================
ALGORITHM PERFORMANCE SUMMARY
================================================================================

BFS:
   Games Played: 1
   Win Rate: 100.0%
   Avg Time: 111.43ms
   Avg Steps: 50.0
   Avg Food: 20.0
   Avg Deaths: 1.0
   Avg Score: 200.0
```

### Excel Output:
| Algorithm | Avg Time (ms) | Steps | Food Eaten | Deaths | Win Rate (%) | Score | Level | Timestamp |
|-----------|---------------|-------|------------|---------|--------------|-------|-------|-----------|
| BFS       | 111.43       | 50    | 20         | 1       | 100.0        | 200   | 1     | 2025-01-05 20:54:30 |
| A*        | 87.8         | 45    | 22         | 0       | 100.0        | 220   | 1     | 2025-01-05 20:54:35 |

## 🎉 Kết quả

Module đã được tích hợp hoàn toàn vào game và sẵn sàng sử dụng! Bạn có thể:

1. **Chạy comparison mode** với các thuật toán khác nhau
2. **Nhấn E** để xuất kết quả ra Excel
3. **So sánh hiệu suất** giữa các thuật toán
4. **Phân tích dữ liệu** trong Excel để tìm thuật toán tốt nhất

## 🔧 Troubleshooting

- **Lỗi Unicode**: Đã sửa tất cả emoji để tương thích với Windows
- **Lỗi openpyxl**: Cài đặt `pip install openpyxl`
- **File không tạo**: Kiểm tra quyền ghi file trong thư mục game
- **Dữ liệu không cập nhật**: Đảm bảo game đang chạy và có sự kiện xảy ra

---

**🎮 Happy Gaming & Data Analysis! 📊**

