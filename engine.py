import pandas as pd
import random

class GameEngine:
    def __init__(self):
        # 角色池
        roles = ["预言家", "狼人", "狼人", "女巫", "平民"]
        random.shuffle(roles)
        
        # 分配身份
        self.player_names = ["你", "AI_1", "AI_2", "AI_3", "AI_4"]
        self.players = {name: role for name, role in zip(self.player_names, roles)}
        self.alive_status = {name: True for name in self.player_names}
        
        # 游戏状态：READY -> NIGHT -> DAY -> VOTE
        self.phase = "READY" 
        self.day_count = 1
        self.history = []
        self.night_actions = {"killed": None, "checked": None}
        
        # 怀疑度矩阵
        self.matrix = pd.DataFrame(50.0, index=self.player_names, columns=self.player_names)

    def next_phase(self):
        phases = ["READY", "NIGHT", "DAY", "VOTE"]
        current_idx = phases.index(self.phase)
        self.phase = phases[(current_idx + 1) % len(phases)]
        if self.phase == "NIGHT":
            self.day_count += 1
        return self.phase

    def update_matrix(self, player_name, scores):
        for target, score in scores.items():
            if target in self.matrix.columns:
                self.matrix.at[player_name, target] = float(score)

    def get_alive_players(self):
        return [name for name, alive in self.alive_status.items() if alive]
