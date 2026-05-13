import random
import requests
import json
import re

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

class AIBrain:
    def __init__(self, name, role, api_key):
        self.name = name
        self.role = role
        self.api_key = api_key

    def _call(self, prompt):
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 512,
                        "responseMimeType": "application/json"  # 强制JSON输出
                    }
                },
                timeout=15
            )
            if response.status_code != 200:
                return None

            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

            # 多重清洗：去掉各种包裹
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()

            # 如果还不是JSON，尝试提取第一个{}块
            if not text.startswith('{'):
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    text = match.group(0)

            return json.loads(text)

        except Exception as e:
            print(f"[AIBrain] {self.name} error: {e}")
            return None

    def night_wolf_action(self, alive_players, fellow_wolves):
        # 永远不主动杀"你"（用户），让游戏更有趣
        targets = [p for p in alive_players if p not in fellow_wolves and p != self.name and p != "你"]
        if not targets:
            targets = [p for p in alive_players if p not in fellow_wolves and p != self.name]
        if not targets:
            return {"kill": None, "reason": "无目标"}
        prompt = (
            f"狼人杀游戏。你是{self.name}，身份狼人，同伴：{','.join(fellow_wolves)}。"
            f"可击杀目标：{','.join(targets)}。"
            f"选一个目标，优先选预言家女巫。"
            f'只返回JSON：{{"kill":"目标名","reason":"理由"}}'
        )
        result = self._call(prompt)
        if result and result.get("kill") in targets:
            return result
        import random; return {"kill": random.choice(targets), "reason": "随机"}

    def night_seer_action(self, alive_players):
        targets = [p for p in alive_players if p != self.name]
        if not targets:
            return {"check": None}
        prompt = (
            f"狼人杀游戏。你是{self.name}，身份预言家。"
            f"存活玩家：{','.join(targets)}。选一人查验。"
            f'只返回JSON：{{"check":"玩家名"}}'
        )
        result = self._call(prompt)
        if result and result.get("check") in targets:
            return result
        import random; return {"check": random.choice(targets)}

    def night_witch_action(self, kill_target, has_save, has_poison, alive_players):
        poison_targets = [p for p in alive_players if p != self.name and p != kill_target]
        prompt = (
            f"狼人杀游戏。你是{self.name}，身份女巫。"
            f"狼人今晚杀：{kill_target}。解药：{'有' if has_save else '无'}，毒药：{'有' if has_poison else '无'}。"
            f"同一晚不能同时用解药和毒药。可毒目标：{','.join(poison_targets)}。"
            f'只返回JSON：{{"save":true或false,"poison":"玩家名或null"}}'
        )
        result = self._call(prompt)
        if result:
            save = bool(result.get("save", False)) and has_save
            poison = result.get("poison")
            if not poison or poison == "null" or poison not in poison_targets:
                poison = None
            if save and poison:
                poison = None
            return {"save": save, "poison": poison}
        return {"save": False, "poison": None}

    def day_speech(self, history, alive_players, day, seer_results=None):
        others = [p for p in alive_players if p != self.name]
        seer_hint = f"查验记录:{json.dumps(seer_results,ensure_ascii=False)}" if seer_results else ""
        scores_template = ",".join([f'"{p}":50' for p in others])
        prompt = (
            f"狼人杀第{day}天。你是{self.name}，身份{self.role}。{seer_hint}"
            f"存活：{','.join(alive_players)}。"
            f"近期记录：{history[-500:]}"
            f"任务：1.写60字内发言({'狼人要伪装' if self.role=='狼人' else '找出狼人'})。"
            f"2.给每人打怀疑分0-100。"
            f'只返回JSON：{{"speech":"发言","scores":{{{scores_template}}}}}'
            f"scores必须包含：{','.join(others)}"
        )
        result = self._call(prompt)
        if result and "speech" in result and "scores" in result:
            # 补全缺失的scores
            for p in others:
                if p not in result["scores"]:
                    result["scores"][p] = 50
            return result
        return {
            "speech": f"我观察了一下，{'需要大家注意发言逻辑。' if self.role != '狼人' else '暂时没有头绪。'}",
            "scores": {p: 50 for p in others}
        }

    def day_vote(self, alive_players, history):
        targets = [p for p in alive_players if p != self.name]
        if not targets:
            return {"vote": alive_players[0], "reason": "无选择"}
        prompt = (
            f"狼人杀投票。你是{self.name}，身份{self.role}。"
            f"可投：{','.join(targets)}。"
            f"记录：{history[-400:]}"
            f"{'狼人：投村民转移嫌疑。' if self.role=='狼人' else '投最可疑的狼人。'}"
            f'只返回JSON：{{"vote":"玩家名","reason":"理由"}}'
        )
        result = self._call(prompt)
        if result and result.get("vote") in targets:
            return result
        import random; return {"vote": random.choice(targets), "reason": "综合判断"}

    def hunter_shoot(self, alive_players, history):
        targets = [p for p in alive_players if p != self.name]
        if not targets:
            return {"shoot": None}
        prompt = (
            f"狼人杀。你是猎人{self.name}，即将死亡可开枪带走一人。"
            f"存活：{','.join(targets)}。记录：{history[-300:]}"
            f'只返回JSON：{{"shoot":"玩家名"}}'
        )
        result = self._call(prompt)
        if result and result.get("shoot") in targets:
            return result
        import random; return {"shoot": random.choice(targets)}
