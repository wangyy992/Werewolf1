import pandas as pd

class GameEngine:
    def __init__(self):
        # 初始身份分配
        self.players = {
            "你": "预言家",
            "AI_1": "狼人",
            "AI_2": "平民",
            "AI_3": "平民",
            "AI_4": "狼人"
        }
        self.history = []
        # 创建 5x5 的矩阵，初始分数为 50
        self.matrix = pd.DataFrame(50.0, index=list(self.players.keys()), columns=list(self.players.keys()))

    def update_matrix(self, player_name, scores):
        for target, score in scores.items():
            if target in self.matrix.columns:
                self.matrix.at[player_name, target] = float(score)