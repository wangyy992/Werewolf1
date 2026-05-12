import pandas as pd
import random

ROLES = {
    "狼人": {"team": "wolf", "count": 3},
    "预言家": {"team": "village", "count": 1},
    "女巫": {"team": "village", "count": 1},
    "猎人": {"team": "village", "count": 1},
    "平民": {"team": "village", "count": 4},
}

ROLE_LIST = ["狼人", "狼人", "狼人", "预言家", "女巫", "猎人", "平民", "平民", "平民", "平民"]

class GameEngine:
    def __init__(self, user_name="你"):
        self.user_name = user_name
        all_players = [user_name] + [f"玩家{i}" for i in range(1, 10)]
        
        roles = ROLE_LIST.copy()
        random.shuffle(roles)
        
        self.players = {name: roles[i] for i, name in enumerate(all_players)}
        self.alive = {name: True for name in all_players}
        self.history = []
        self.day = 1
        self.phase = "night"  # night | day_discuss | day_vote
        self.night_kills = []  # killed by wolves tonight
        self.witch_potion = {"save": True, "poison": True}
        self.witch_saved = False  # used this night?
        self.seer_result = None  # result for seer this night
        self.votes = {}  # player -> target votes
        self.eliminated = []  # list of eliminated player info
        self.game_over = False
        self.winner = None
        self.pending_witch_action = None  # name of wolf kill target, waiting for witch
        self.hunter_trigger = None  # if hunter dies, can shoot

        matrix_players = all_players
        self.matrix = pd.DataFrame(50.0, index=matrix_players, columns=matrix_players)

    def get_alive_players(self):
        return [p for p, alive in self.alive.items() if alive]

    def get_role(self, name):
        return self.players.get(name, "未知")

    def eliminate_player(self, name, reason=""):
        if name in self.alive:
            self.alive[name] = False
            role = self.players[name]
            self.eliminated.append({"name": name, "role": role, "reason": reason, "day": self.day})
            self.history.append(f"💀 **{name}**（{role}）{reason}出局。")
            return role
        return None

    def check_game_over(self):
        alive = self.get_alive_players()
        wolves = [p for p in alive if self.players[p] == "狼人"]
        villagers = [p for p in alive if self.players[p] != "狼人"]
        if len(wolves) == 0:
            self.game_over = True
            self.winner = "village"
            return True
        if len(wolves) >= len(villagers):
            self.game_over = True
            self.winner = "wolf"
            return True
        return False

    def update_matrix(self, player_name, scores):
        for target, score in scores.items():
            if target in self.matrix.columns and player_name in self.matrix.index:
                self.matrix.at[player_name, target] = float(score)

    def get_public_history(self):
        return "\n".join(self.history[-30:])

    def wolf_vote_kill(self, wolf_candidates):
        """AI wolves vote on who to kill"""
        alive_villagers = [p for p in self.get_alive_players() if self.players[p] != "狼人"]
        if not alive_villagers:
            return None
        # Simple: pick the one with highest average suspicion score among wolves
        scores = {}
        for target in alive_villagers:
            total = sum(self.matrix.at[w, target] for w in wolf_candidates if w in self.matrix.index)
            scores[target] = total
        return max(scores, key=scores.get)

    def tally_votes(self):
        """Count day votes and return who gets most votes"""
        if not self.votes:
            return None
        count = {}
        for voter, target in self.votes.items():
            count[target] = count.get(target, 0) + 1
        max_votes = max(count.values())
        candidates = [p for p, v in count.items() if v == max_votes]
        return random.choice(candidates)  # random tiebreak
