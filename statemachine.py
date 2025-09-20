from enum import Enum
from typing import List, Optional, Tuple, Type, Union


class StateOperations(Enum):
    NOP = 0      # Không làm gì 
    POP = 1      # Xóa state hiện tại
    PUSH = 2     # Thêm state mới
    REPLACE = 3  # Thay thế state hiện tại


class State:     
    def __init__(self, app, machine):
        self.app = app              # trỏ về App
        self.machine = machine      # trỏ về StateMachine
        self.next_state: Tuple[StateOperations, Optional["State"]] = (StateOperations.NOP, None)

    # Vòng đời state
    def handle_events(self, event): pass
    def logic(self): pass
    def draw(self, screen): pass
    def on_resume(self): pass
    def on_exit(self): pass
    
    # Các thao tác chuyển state
    def pop_state(self):
        self.next_state = (StateOperations.POP, None)

    def push_state(self, new: "State"):
        self.next_state = (StateOperations.PUSH, new)

    def replace_state(self, new: "State"):
        self.next_state = (StateOperations.REPLACE, new)


class StateMachine:
    def __init__(self, initial_state_cls: Type[State], app):
        self.stack: List[State] = []
        # Tạo state đầu tiên (nhận app và machine)
        initial_state = initial_state_cls(app, self)
        self.apply_operation((StateOperations.PUSH, initial_state))
    
    @property
    def running(self):
        return len(self.stack) > 0 
    
    @property
    def current_state(self) -> Union[State, None]:
        if self.stack:
            return self.stack[-1] 
        return None

    def apply_operation(self, op_tuple: Tuple[StateOperations, Optional[State]]):
        op, new = op_tuple

        if op == StateOperations.NOP:
            return

        elif op == StateOperations.POP:
            if self.stack:
                prev = self.stack.pop()
                prev.on_exit()
            if self.stack:
                self.stack[-1].on_resume()

        elif op == StateOperations.REPLACE:
            if self.stack:
                prev = self.stack.pop()
                prev.on_exit()
            if new:
                self.stack.append(new)
                new.on_resume()

        elif op == StateOperations.PUSH:
            if self.stack:
                self.stack[-1].on_exit()
            if new: 
                self.stack.append(new)
                new.on_resume()
        
    def update(self):
        """Gọi sau mỗi frame để thực thi next_state"""
        if self.current_state and self.current_state.next_state[0] != StateOperations.NOP:
            self.apply_operation(self.current_state.next_state)
            self.current_state.next_state = (StateOperations.NOP, None)
