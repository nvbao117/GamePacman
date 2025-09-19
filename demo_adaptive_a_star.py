#!/usr/bin/env python3
"""
Demo Adaptive A* - Giải thích cách hoạt động
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.a_star import adaptive_a_star, get_learning_stats, reset_learning
from core.nodes import Node
from config import *

def demo_adaptive_learning():
    """Demo khả năng học của Adaptive A*"""
    print("🧠 DEMO ADAPTIVE A* - KHẢ NĂNG HỌC")
    print("=" * 50)
    
    # Reset learning data
    reset_learning()
    
    # Tạo maze đơn giản
    nodes = {}
    for x in range(5):
        for y in range(5):
            nodes[(x, y)] = Node(x, y)
    
    # Kết nối các nodes
    for x in range(5):
        for y in range(5):
            current = nodes[(x, y)]
            if x > 0:
                current.neighbors[LEFT] = nodes[(x-1, y)]
            if x < 4:
                current.neighbors[RIGHT] = nodes[(x+1, y)]
            if y > 0:
                current.neighbors[UP] = nodes[(x, y-1)]
            if y < 4:
                current.neighbors[DOWN] = nodes[(x, y+1)]
    
    class MockPellet:
        def __init__(self, node):
            self.node = node
            self.visible = True
    
    class MockPelletGroup:
        def __init__(self, pellets):
            self.pelletList = pellets
    
    # Tạo pellets
    pellets = [MockPellet(nodes[(4, 4)])]
    pellet_group = MockPelletGroup(pellets)
    
    print("🎯 Lần tìm kiếm 1:")
    path1 = adaptive_a_star(nodes[(0, 0)], None, pellet_group, learning_rate=0.5)
    print(f"   Đường đi: {[f'({n.position.x},{n.position.y})' for n in path1] if path1 else 'None'}")
    print(f"   Độ dài: {len(path1) if path1 else 0}")
    
    stats1 = get_learning_stats()
    print(f"   Heuristics đã học: {stats1['learned_heuristics']}")
    print(f"   Lịch sử tìm kiếm: {stats1['search_history']}")
    
    print("\n🎯 Lần tìm kiếm 2 (cùng vị trí):")
    path2 = adaptive_a_star(nodes[(0, 0)], None, pellet_group, learning_rate=0.5)
    print(f"   Đường đi: {[f'({n.position.x},{n.position.y})' for n in path2] if path2 else 'None'}")
    print(f"   Độ dài: {len(path2) if path2 else 0}")
    
    stats2 = get_learning_stats()
    print(f"   Heuristics đã học: {stats2['learned_heuristics']}")
    print(f"   Lịch sử tìm kiếm: {stats2['search_history']}")
    
    print("\n🎯 Lần tìm kiếm 3 (vị trí khác):")
    pellets2 = [MockPellet(nodes[(2, 2)])]
    pellet_group2 = MockPelletGroup(pellets2)
    path3 = adaptive_a_star(nodes[(1, 1)], None, pellet_group2, learning_rate=0.5)
    print(f"   Đường đi: {[f'({n.position.x},{n.position.y})' for n in path3] if path3 else 'None'}")
    print(f"   Độ dài: {len(path3) if path3 else 0}")
    
    stats3 = get_learning_stats()
    print(f"   Heuristics đã học: {stats3['learned_heuristics']}")
    print(f"   Lịch sử tìm kiếm: {stats3['search_history']}")
    print(f"   Độ dài trung bình: {stats3['average_path_length']:.2f}")
    
    print("\n" + "=" * 50)

def explain_adaptive_features():
    """Giải thích các tính năng adaptive"""
    print("🔬 GIẢI THÍCH TÍNH NĂNG ADAPTIVE:")
    print("=" * 40)
    
    print("""
🧠 ADAPTIVE A* LÀM GÌ:

1. 📚 HỌC TỪ KINH NGHIỆM:
   - Lưu trữ heuristic cho các cặp node đã gặp
   - Cập nhật heuristic dựa trên kết quả thực tế
   - Sử dụng kinh nghiệm để tối ưu hóa lần tìm kiếm sau

2. 🔄 CẢI THIỆN LIÊN TỤC:
   - Mỗi lần tìm kiếm, học thêm thông tin mới
   - Kết hợp heuristic cơ bản và đã học
   - Tăng dần độ chính xác qua thời gian

3. 📊 THEO DÕI HIỆU SUẤT:
   - Lưu lịch sử tìm kiếm
   - Thống kê độ dài đường đi
   - Đo lường sự cải thiện

4. 🎯 TỐI ƯU HÓA:
   - Tìm kiếm nhanh hơn với heuristic tốt hơn
   - Giảm số node cần khám phá
   - Cải thiện chất lượng đường đi
    """)

def show_learning_mechanism():
    """Hiển thị cơ chế học"""
    print("\n⚙️ CƠ CHẾ HỌC:")
    print("=" * 20)
    
    print("""
📈 QUÁ TRÌNH HỌC:

1. LẦN ĐẦU TIÊN:
   - Sử dụng Manhattan distance cơ bản
   - Lưu heuristic thực tế vào bộ nhớ
   - Tạo baseline cho lần sau

2. LẦN THỨ HAI:
   - Kết hợp heuristic cơ bản + đã học
   - Cập nhật heuristic dựa trên kết quả mới
   - Cải thiện độ chính xác

3. CÁC LẦN SAU:
   - Sử dụng heuristic đã được cải thiện
   - Tiếp tục học và cập nhật
   - Tối ưu hóa ngày càng tốt hơn

🔧 CÔNG THỨC HỌC:
   new_heuristic = old_heuristic + learning_rate × (actual_cost - old_heuristic)
   
   - learning_rate: Tỷ lệ học (0.0 - 1.0)
   - actual_cost: Chi phí thực tế
   - old_heuristic: Heuristic cũ
    """)

def compare_with_regular_a_star():
    """So sánh với A* thông thường"""
    print("\n📊 SO SÁNH ADAPTIVE A* vs A* THÔNG THƯỜNG:")
    print("=" * 50)
    
    print("""
🎯 A* THÔNG THƯỜNG:
   ✅ Tìm đường tối ưu
   ✅ Sử dụng heuristic cố định
   ❌ Không học từ kinh nghiệm
   ❌ Mỗi lần tìm kiếm như nhau

🧠 ADAPTIVE A*:
   ✅ Tìm đường tối ưu
   ✅ Heuristic cải thiện theo thời gian
   ✅ Học từ kinh nghiệm
   ✅ Tìm kiếm nhanh hơn qua thời gian
   ✅ Thích ứng với từng tình huống

📈 HIỆU SUẤT:
   - Lần đầu: Tương đương A* thông thường
   - Lần 2-3: Bắt đầu cải thiện
   - Lần 4+: Rõ ràng nhanh hơn A* thông thường
   - Lâu dài: Tối ưu hóa đáng kể
    """)

def usage_examples():
    """Ví dụ sử dụng"""
    print("\n💻 VÍ DỤ SỬ DỤNG:")
    print("=" * 20)
    
    print("""
# Sử dụng cơ bản
from ai.a_star import adaptive_a_star, get_learning_stats, reset_learning

# Reset dữ liệu học (nếu cần)
reset_learning()

# Tìm kiếm với learning rate cao (học nhanh)
path = adaptive_a_star(start_node, None, pellet_group, learning_rate=0.8)

# Tìm kiếm với learning rate thấp (học chậm, ổn định)
path = adaptive_a_star(start_node, None, pellet_group, learning_rate=0.1)

# Xem thống kê học
stats = get_learning_stats()
print(f"Heuristics đã học: {stats['learned_heuristics']}")
print(f"Số lần tìm kiếm: {stats['search_history']}")

# Trong game loop
if auto and pelletGroup is not None:
    path = adaptive_a_star(self.node, None, pelletGroup, learning_rate=0.3)
    if path:
        self.set_path(path)
    """)

if __name__ == "__main__":
    print("🎮 DEMO ADAPTIVE A* CHO PACMAN")
    print("=" * 50)
    
    try:
        demo_adaptive_learning()
        explain_adaptive_features()
        show_learning_mechanism()
        compare_with_regular_a_star()
        usage_examples()
        
        print("\n" + "=" * 50)
        print("🎯 TÓM TẮT:")
        print("Adaptive A* = A* + Machine Learning")
        print("Học từ kinh nghiệm để tối ưu hóa tìm kiếm")
        print("Phù hợp cho game có nhiều lần tìm kiếm tương tự")
        print("=" * 50)
        
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
