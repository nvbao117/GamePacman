import random
import json
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
from collections import defaultdict
from typing import Optional
from constants import DOWN , LEFT , RIGHT , UP,STOP


Action = int 
DEFAULT_ACTIONS : Tuple[Action, ...] = (UP,DOWN,LEFT,RIGHT,STOP)
State = Tuple[int, ...]
@dataclass
class QLearningConfig:
    alpha : float = 0.3  # Learning rate cao hơn cho ultra long training
    gamma : float = 0.85  # Discount factor cao hơn để ưu tiên long-term reward
    epsilon : float = 1.0  # Bắt đầu với full exploration
    epsilon_min : float = 0.01  # Epsilon min thấp hơn cho exploitation tốt hơn
    epsilon_decay : float = 0.9995  # Decay rất chậm cho 20k episodes
    default_actions : Tuple[Action, ...] = DEFAULT_ACTIONS


class QLearningAgent:
    def __init__(self,config : Optional[QLearningConfig] = None):
        cfg = config or QLearningConfig()
        self.alpha = cfg.alpha
        self.gamma = cfg.gamma
        self.epsilon = cfg.epsilon
        self.epsilon_min = cfg.epsilon_min
        self.epsilon_decay = cfg.epsilon_decay
        self.actions = set(cfg.default_actions)
        self.q_table: Dict[State, Dict[Action, float]] = defaultdict(self._row_factory)
        self._last_state = None
        self._last_action = None
        self._pending_reward = 0.0

    def _row_factory(self) -> Dict[Action,float] : 
        return {action:0.0 for action in self.actions} 

    def start_episode(self): 
        self._last_state = None 
        self._last_action = None
        self._pending_reward = 0.0

    def add_reward(self,value:float) -> None : 
        self._pending_reward += value 

    def selection_action (self,state:State,legal_actions:Iterable[Action]) -> Action : 
        choices = tuple(legal_actions) or (STOP,)
        if random.random() < self.epsilon:
            action = random.choice(choices)
        else:
            row = self.q_table[state]
            action = max(choices, key=lambda a: row.get(a, 0.0))
        self._last_state = state
        self._last_action = action
        return action

    def observe(self, next_state: Optional[State], legal_actions: Iterable[Action], done: bool = False) -> None:
        if self._last_state is None or self._last_action is None:
            self._pending_reward = 0.0
            return

        current = self.q_table[self._last_state][self._last_action]
        if done or next_state is None:
            best_next = 0.0
        else:
            next_choices = tuple(legal_actions)
            if next_choices:
                best_next = max(self.q_table[next_state].get(a, 0.0) for a in next_choices)
            else:
                best_next = 0.0

        target = self._pending_reward + self.gamma * best_next
        self.q_table[self._last_state][self._last_action] = current + self.alpha * (target - current)

        self._pending_reward = 0.0
        if done:
            self._last_state = None
            self._last_action = None
            # KHÔNG tự động decay epsilon ở đây vì optimized_training.py đã handle
            # self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self,path:str) -> None : 
        payload = {
            "config":{
                "alpha":self.alpha,
                "gamma":self.gamma,
                "epsilon":self.epsilon,
                "epsilon_min":self.epsilon_min,
                "epsilon_decay":self.epsilon_decay,	
                "default_actions":list(self.actions)
            },
            "table":[
                {"state": list(state),"values":{str(a):v for a,v in row.items()}}
                for state,row in self.q_table.items()
            ],
        }
        with open(path,"w",encoding="utf-8") as fh: 
            json.dump(payload,fh,indent = 2 )

    def load(self,path:str) -> None : 
        with open(path,"r",encoding="utf-8") as fh: 
            payload = json.load(fh)

        cfg = payload.get("config", {})
        self.alpha = cfg.get("alpha", self.alpha)
        self.gamma = cfg.get("gamma", self.gamma)
        self.epsilon = cfg.get("epsilon", self.epsilon)
        self.epsilon_min = cfg.get("epsilon_min", self.epsilon_min)
        self.epsilon_decay = cfg.get("epsilon_decay", self.epsilon_decay)
        actions = tuple(cfg.get("default_actions", self.actions))
        
        if actions:
            self.actions = actions

        self.q_table.clear()
        for row in payload.get("table", []):
            state = tuple(int(x) for x in row.get("state", []))
            values = {int(a): float(v) for a, v in row.get("values", {}).items()}
            default_row = self._row_factory()
            default_row.update(values)
            self.q_table[state] = default_row

        self.start_episode()