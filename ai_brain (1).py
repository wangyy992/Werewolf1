import google.generativeai as genai
import json
import re

class AIBrain:
    def __init__(self, name, role, api_key):
        self.name = name
        self.role = role
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _call(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # strip markdown code fences
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            return json.loads(text.strip())
        except Exception as e:
            return None

    def night_wolf_action(self, alive_players, fellow_wolves):
        """Wolves discuss who to kill. Returns {"kill": "player_name"}"""
        targets = [p for p in alive_players if p not in fellow_wolves and p != self.name]
        prompt = f"""
你在玩狼人杀。你是 {self.name}，身份：狼人。
你的狼人同伴：{', '.join(fellow_wolves)}。
存活玩家（村民方）：{', '.join(targets)}。
请选择今晚刀人目标，优先杀预言家、女巫等特殊身份。
只输出JSON: {{"kill": "玩家名", "reason": "理由（中文10字内）"}}
"""
        result = self._call(prompt)
        if result and "kill" in result and result["kill"] in targets:
            return result
        return {"kill": targets[0] if targets else None, "reason": "随机选择"}

    def night_seer_action(self, alive_players):
        """Seer picks who to check. Returns {"check": "player_name"}"""
        targets = [p for p in alive_players if p != self.name]
        prompt = f"""
你在玩狼人杀。你是 {self.name}，身份：预言家。
存活玩家：{', '.join(targets)}。
请选择今晚查验谁，优先查验最可疑的人。
只输出JSON: {{"check": "玩家名"}}
"""
        result = self._call(prompt)
        if result and "check" in result and result["check"] in targets:
            return result
        return {"check": targets[0] if targets else None}

    def night_witch_action(self, kill_target, has_save, has_poison, alive_players):
        """Witch decides whether to save or poison. Returns {"save": bool, "poison": "name" or null}"""
        poison_targets = [p for p in alive_players if p != self.name and p != kill_target]
        prompt = f"""
你在玩狼人杀。你是 {self.name}，身份：女巫。
今晚狼人要杀：{kill_target}。
你还有解药：{'是' if has_save else '否'}，毒药：{'是' if has_poison else '否'}。
存活玩家：{', '.join(alive_players)}。
请决定是否用解药救 {kill_target}，以及是否用毒药毒死某人。
只输出JSON: {{"save": true或false, "poison": "玩家名或null"}}
注意：不能同一夜既用解药又用毒药。
"""
        result = self._call(prompt)
        if result:
            save = result.get("save", False) and has_save
            poison = result.get("poison")
            if poison and (not has_poison or poison not in poison_targets):
                poison = None
            if save and poison:
                poison = None  # can't use both same night
            return {"save": save, "poison": poison}
        return {"save": False, "poison": None}

    def day_speech(self, history, alive_players, day, seer_results=None):
        """AI gives a day speech. Returns {"speech": "...", "scores": {player: 0-100}}"""
        seer_hint = ""
        if seer_results:
            seer_hint = f"你的查验记录：{json.dumps(seer_results, ensure_ascii=False)}"
        prompt = f"""
你在玩狼人杀。你是 {self.name}，身份：{self.role}，第{day}天白天。
{seer_hint}
存活玩家：{', '.join(alive_players)}。
游戏记录（最近）：
{history}

任务：
1. 写一段60字内的中文发言，要有逻辑，符合你的身份（{'狼人要伪装，不能暴露' if self.role == '狼人' else '尽量找出狼人'})。
2. 给每位存活玩家（除自己）打怀疑分（0=绝对信任，100=确定是狼）。

只输出JSON: {{"speech": "发言内容", "scores": {{"玩家名": 分数}}}}
"""
        result = self._call(prompt)
        if result and "speech" in result:
            return result
        return {
            "speech": "我还在观察局势，暂时保留意见。",
            "scores": {p: 50 for p in alive_players if p != self.name}
        }

    def day_vote(self, alive_players, history):
        """AI votes for who to eliminate. Returns {"vote": "player_name"}"""
        targets = [p for p in alive_players if p != self.name]
        prompt = f"""
你在玩狼人杀。你是 {self.name}，身份：{self.role}，现在是投票环节。
存活玩家：{', '.join(targets)}。
游戏记录：
{history}

请投票选择最可疑的玩家淘汰（{'作为狼人，投票给最弱的村民' if self.role == '狼人' else '投票给最可疑的狼人'})。
只输出JSON: {{"vote": "玩家名", "reason": "理由（10字内）"}}
"""
        result = self._call(prompt)
        if result and "vote" in result and result["vote"] in targets:
            return result
        return {"vote": targets[0], "reason": "综合判断"}

    def hunter_shoot(self, alive_players, history):
        """Hunter chooses who to shoot when dying. Returns {"shoot": "player_name"}"""
        targets = [p for p in alive_players if p != self.name]
        prompt = f"""
你在玩狼人杀。你是 {self.name}，身份：猎人，你即将死亡，可以开枪带走一名玩家。
存活玩家：{', '.join(targets)}。
游戏记录：{history}
选择最可疑的狼人开枪。
只输出JSON: {{"shoot": "玩家名"}}
"""
        result = self._call(prompt)
        if result and "shoot" in result and result["shoot"] in targets:
            return result
        return {"shoot": targets[0]}
