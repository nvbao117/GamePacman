# Pac-Man Comparison Mode

## Tổng quan
Giao diện comparison mode cho phép so sánh trực tiếp giữa AI và người chơi trong cùng một màn hình. Giao diện được thiết kế với 2 màn hình game song song và một control panel ở phía dưới.

## Cấu trúc giao diện

### 1. Layout chính
- **AI Game Area (Trái)**: Màn hình game cho AI với thuật toán được chọn
- **Player Game Area (Phải)**: Màn hình game cho người chơi điều khiển thủ công
- **Control Panel (Dưới)**: Panel điều khiển chung cho cả 2 game

### 2. Các thành phần chính

#### ComparisonState (`states/comparison_state.py`)
- Quản lý 2 game instances riêng biệt (AI và Player)
- Đồng bộ hóa trạng thái pause/play giữa 2 game
- Xử lý events cho cả 2 game
- Cập nhật thông tin game cho cả 2 bên

#### ComparisonLayout (`states/comparison_layout.py`)
- Quản lý layout UI với 2 game areas song song
- Control panel ở dưới với thống kê so sánh
- Hiệu ứng visual và animation
- Selectbox để chọn thuật toán AI

### 3. Tính năng

#### Điều khiển
- **SPACE**: Pause/Resume cả 2 game
- **ESC**: Pause game
- **R**: Restart cả 2 game
- **↑↓←→**: Điều khiển Player game (AI tự động)

#### Thống kê so sánh
- Điểm số (Score) của cả AI và Player
- Số mạng (Lives) còn lại
- Level hiện tại
- Thuật toán AI đang sử dụng

#### Thuật toán AI hỗ trợ
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- A* (A-Star)
- UCS (Uniform Cost Search)
- IDS (Iterative Deepening Search)

## Cách sử dụng

### 1. Chạy demo
```bash
python test_comparison.py
```

### 2. Tích hợp vào game chính
```python
from states.comparison_state import ComparisonState

# Tạo comparison state
comparison_state = ComparisonState(app, machine, "BFS")

# Chuyển đến comparison state
machine.set_state(comparison_state)
```

### 3. Tùy chỉnh
- Thay đổi thuật toán AI qua selectbox
- Điều khiển Player game bằng phím mũi tên
- Sử dụng control panel để pause/restart

## Cấu trúc file

```
states/
├── comparison_state.py      # State chính cho comparison mode
├── comparison_layout.py     # Layout UI cho comparison
└── game_state.py           # State game đơn lẻ (tham khảo)

test_comparison.py          # Demo file
COMPARISON_README.md        # File hướng dẫn này
```

## Lưu ý kỹ thuật

### Scaling
- Cả 2 game areas đều được scale để giữ aspect ratio gốc
- Sử dụng `pygame.transform.smoothscale` để scaling mượt mà
- Tự động tính toán kích thước phù hợp với màn hình

### Performance
- Mỗi game instance chạy độc lập
- Animation được tối ưu hóa với `animation_time`
- Background effects sử dụng transparency để giảm tải

### Event Handling
- Events được chuyển tiếp cho cả 2 game engines
- Play/Pause button điều khiển cả 2 game cùng lúc
- Keyboard shortcuts hoạt động cho cả 2 game

## Mở rộng

### Thêm thuật toán mới
1. Thêm tên thuật toán vào `algorithm_options` trong `ComparisonLayout`
2. Đảm bảo `Game` class hỗ trợ thuật toán mới

### Thêm thống kê mới
1. Cập nhật `set_game_info()` method
2. Thêm UI elements trong `_draw_comparison_stats()`
3. Cập nhật game engines để cung cấp dữ liệu mới

### Tùy chỉnh giao diện
1. Chỉnh sửa colors trong `ui/constants.py`
2. Thay đổi layout trong `_setup_layout()`
3. Thêm hiệu ứng mới trong các `_draw_*()` methods
