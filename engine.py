import pandas as pd

class GameEngine:
    def __init__(self):
        self.players = {
            "你": "预言家", # 玩家固定身份
            "AI_1": "狼人",
            "AI_2": "平民",
            "AI_3": "平民",
            "AI_4": "狼人"
        }
        self.history = []
        self.matrix = pd.DataFrame(50.0, index=self.players.keys(), columns=self.players.keys())

    def update_matrix(self, player_name, scores):
        for target, score in scores.items():
            if target in self.matrix.columns:
                self.matrix.at[player_name, target] = float(score)

    def get_game_state(self):
        return "\n".join(self.history)