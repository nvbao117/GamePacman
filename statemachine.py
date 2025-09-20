# =============================================================================
# STATEMACHINE.PY - HỆ THỐNG QUẢN LÝ STATE (MÀN HÌNH)
# =============================================================================
# File này chứa State Machine Pattern để quản lý các màn hình khác nhau
# trong game (Menu, Game, Pause, Game Over, v.v.)

from enum import Enum
from typing import List, Optional, Tuple, Type, Union


class StateOperations(Enum):
    """
    Enum định nghĩa các thao tác có thể thực hiện với state machine
    """
    NOP = 0      # Không làm gì 
    POP = 1      # Xóa state hiện tại khỏi stack
    PUSH = 2     # Thêm state mới vào stack
    REPLACE = 3  # Thay thế state hiện tại bằng state mới


class State:     
    """
    Base class cho tất cả các state (màn hình) trong game
    - Mỗi state đại diện cho một màn hình (Menu, Game, Pause, v.v.)
    - Có vòng đời: handle_events -> logic -> draw
    - Có thể chuyển đổi sang state khác thông qua state machine
    """
    def __init__(self, app, machine):
        self.app = app              # Tham chiếu đến App chính
        self.machine = machine      # Tham chiếu đến StateMachine
        # Tuple chứa thao tác và state mới sẽ được thực hiện
        self.next_state: Tuple[StateOperations, Optional["State"]] = (StateOperations.NOP, None)

    # =============================================================================
    # VÒNG ĐỜI STATE - Các method được gọi trong mỗi frame
    # =============================================================================
    
    def handle_events(self, event): 
        """
        Xử lý sự kiện input từ người dùng
        - Được gọi mỗi khi có sự kiện (click, keyboard, v.v.)
        - Override trong subclass để xử lý sự kiện cụ thể
        """
        pass
        
    def logic(self): 
        """
        Cập nhật logic của state
        - Được gọi mỗi frame để cập nhật trạng thái
        - Override trong subclass để thêm logic cụ thể
        """
        pass
        
    def draw(self, screen): 
        """
        Vẽ state lên màn hình
        - Được gọi mỗi frame để render
        - Override trong subclass để vẽ nội dung cụ thể
        """
        pass
        
    def on_resume(self): 
        """
        Được gọi khi state được resume (quay lại từ state khác)
        - Override để khôi phục trạng thái khi quay lại
        """
        pass
        
    def on_exit(self): 
        """
        Được gọi khi state bị exit (chuyển sang state khác)
        - Override để dọn dẹp tài nguyên khi thoát
        """
        pass
    
    # =============================================================================
    # CÁC THAO TÁC CHUYỂN STATE
    # =============================================================================
    
    def pop_state(self):
        """
        Xóa state hiện tại khỏi stack (quay về state trước đó)
        - State trước đó sẽ được resume
        """
        self.next_state = (StateOperations.POP, None)

    def push_state(self, new: "State"):
        """
        Thêm state mới vào stack (state hiện tại bị pause)
        - State hiện tại vẫn còn trong stack, chỉ bị pause
        - State mới sẽ được active
        """
        self.next_state = (StateOperations.PUSH, new)

    def replace_state(self, new: "State"):
        """
        Thay thế state hiện tại bằng state mới
        - State hiện tại bị xóa khỏi stack
        - State mới thay thế vị trí của nó
        """
        self.next_state = (StateOperations.REPLACE, new)


class StateMachine:
    """
    State Machine quản lý stack các state
    - Sử dụng stack để quản lý thứ tự các state
    - State ở đỉnh stack là state hiện tại đang active
    - Hỗ trợ push/pop/replace operations
    """
    def __init__(self, initial_state_cls: Type[State], app):
        """
        Khởi tạo state machine với state đầu tiên
        Args:
            initial_state_cls: Class của state đầu tiên (thường là MenuState)
            app: Tham chiếu đến App chính
        """
        self.stack: List[State] = []
        # Tạo state đầu tiên và push vào stack
        initial_state = initial_state_cls(app, self)
        self.apply_operation((StateOperations.PUSH, initial_state))
    
    @property
    def running(self):
        """
        Kiểm tra xem state machine có đang chạy không
        Returns: True nếu còn state trong stack
        """
        return len(self.stack) > 0 
    
    @property
    def current_state(self) -> Union[State, None]:
        """
        Lấy state hiện tại (state ở đỉnh stack)
        Returns: State hiện tại hoặc None nếu stack rỗng
        """
        if self.stack:
            return self.stack[-1] 
        return None

    def apply_operation(self, op_tuple: Tuple[StateOperations, Optional[State]]):
        """
        Thực hiện thao tác với state machine
        Args:
            op_tuple: Tuple chứa (operation, new_state)
        """
        op, new = op_tuple

        if op == StateOperations.NOP:
            return

        elif op == StateOperations.POP:
            # Xóa state hiện tại khỏi stack
            if self.stack:
                prev = self.stack.pop()
                prev.on_exit()  # Gọi on_exit cho state bị xóa
            if self.stack:
                self.stack[-1].on_resume()  # Resume state trước đó

        elif op == StateOperations.REPLACE:
            # Thay thế state hiện tại bằng state mới
            if self.stack:
                prev = self.stack.pop()
                prev.on_exit()  # Gọi on_exit cho state bị thay thế
            if new:
                self.stack.append(new)
                new.on_resume()  # Gọi on_resume cho state mới

        elif op == StateOperations.PUSH:
            # Thêm state mới vào stack
            if self.stack:
                self.stack[-1].on_exit()  # Pause state hiện tại
            if new: 
                self.stack.append(new)
                new.on_resume()  # Resume state mới
        
    def update(self):
        """
        Cập nhật state machine - được gọi mỗi frame
        - Kiểm tra và thực hiện thao tác chuyển state nếu có
        - Reset next_state sau khi thực hiện
        """
        if self.current_state and self.current_state.next_state[0] != StateOperations.NOP:
            # Có thao tác chuyển state cần thực hiện
            self.apply_operation(self.current_state.next_state)
            # Reset next_state sau khi thực hiện
            self.current_state.next_state = (StateOperations.NOP, None)
