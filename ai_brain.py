import requests
import json
import re
import random

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

class AIBrain:
    def __init__(self, name, role, api_key):
        self.name = name
        self.role = role
        self.api_key = api_key

    def _call(self, prompt):
        try:
            resp = requests.post(
                f"{GEMINI_URL}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300}
                },
                timeout=15
            )
            import streamlit as st
            if resp.status_code != 200:
                st.session_state.setdefault("api_errors", []).append(
                    f"{self.name}: HTTP {resp.status_code} - {resp.text[:200]}"
                )
                return None
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            st.session_state.setdefault("api_last_raw", {})[self.name] = text[:200]
            # 提取第一个 {...} 块
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            st.session_state.setdefault("api_errors", []).append(
                f"{self.name}: JSON提取失败，原文: {text[:100]}"
            )
            return None
        except Exception as e:
            import streamlit as st
            st.session_state.setdefault("api_errors", []).append(f"{self.name}: 异常 {e}")
            return None

    def night_wolf_action(self, alive_players, fellow_wolves):
        targets = [p for p in alive_players if p not in fellow_wolves and p != self.name and p != "你"]
        if not targets:
            targets = [p for p in alive_players if p not in fellow_wolves and p != self.name]
        if not targets:
            return {"kill": None}
        prompt = (
            f'你是狼人杀游戏玩家{self.name}，身份狼人。'
            f'今晚必须从以下玩家中选一人击杀：{targets}。'
            f'直接输出JSON，不要解释：{{"kill": "{targets[0]}"}}'
            f'（把{targets[0]}替换为你选的目标）'
        )
        result = self._call(prompt)
        if result and result.get("kill") in targets:
            return result
        return {"kill": random.choice(targets)}

    def night_seer_action(self, alive_players):
        targets = [p for p in alive_players if p != self.name]
        if not targets:
            return {"check": None}
        prompt = (
            f'你是狼人杀预言家{self.name}。'
            f'从以下玩家选一人查验：{targets}。'
            f'直接输出JSON：{{"check": "{targets[0]}"}}'
        )
        result = self._call(prompt)
        if result and result.get("check") in targets:
            return result
        return {"check": random.choice(targets)}

    def night_witch_action(self, kill_target, has_save, has_poison, alive_players):
        poison_targets = [p for p in alive_players if p != self.name and p != kill_target]
        prompt = (
            f'你是狼人杀女巫{self.name}。狼人今晚杀了{kill_target}。'
            f'解药剩余：{"1瓶" if has_save else "0瓶"}，毒药剩余：{"1瓶" if has_poison else "0瓶"}。'
            f'同一晚不能同时使用解药和毒药。可毒目标：{poison_targets}。'
            f'直接输出JSON（poison填玩家名或null）：{{"save": false, "poison": null}}'
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
        scores_example = {p: 50 for p in others}
        seer_hint = f"你的查验结果：{seer_results}。" if seer_results else ""
        prompt = (
            f'狼人杀第{day}天白天。你是{self.name}，身份{self.role}。{seer_hint}'
            f'存活玩家：{alive_players}。近期记录：{history[-400:]}\n'
            f'{"作为狼人要伪装成好人，不能暴露。" if self.role=="狼人" else "分析发言找出狼人。"}'
            f'输出JSON，speech是你的发言(50字内)，scores是对每人的怀疑分(0-100)：'
            f'{json.dumps({"speech": "你的发言", "scores": scores_example}, ensure_ascii=False)}'
        )
        result = self._call(prompt)
        if result and "speech" in result:
            if "scores" not in result or not result["scores"]:
                result["scores"] = {p: 50 for p in others}
            for p in others:
                if p not in result["scores"]:
                    result["scores"][p] = 50
            return result
        # fallback：至少生成有意义的发言
        fallback_speeches = {
            "狼人": [f"我觉得{random.choice(others)}的发言很可疑，大家注意。", f"昨晚平安夜，我支持先听大家分析。"],
            "预言家": [f"我有查验信息，但先观察一轮。", f"我认为{random.choice(others)}需要重点关注。"],
            "女巫": [f"昨晚我用了药，现在观察局势。", f"大家注意{random.choice(others)}的发言逻辑。"],
            "猎人": [f"我在观察，{random.choice(others)}的发言有漏洞。", f"先听其他人分析，我有自己判断。"],
            "平民": [f"我觉得{random.choice(others)}比较可疑。", f"根据发言逻辑，我怀疑{random.choice(others)}。"],
        }
        speeches = fallback_speeches.get(self.role, [f"我怀疑{random.choice(others)}。"])
        return {"speech": random.choice(speeches), "scores": {p: 50 for p in others}}

    def day_vote(self, alive_players, history):
        targets = [p for p in alive_players if p != self.name]
        if not targets:
            return {"vote": alive_players[0]}
        prompt = (
            f'狼人杀投票环节。你是{self.name}，身份{self.role}。'
            f'可投票目标：{targets}。记录：{history[-300:]}'
            f'{"投给村民转移嫌疑。" if self.role=="狼人" else "投给最可疑的狼人。"}'
            f'直接输出JSON：{{"vote": "{targets[0]}", "reason": "理由"}}'
        )
        result = self._call(prompt)
        if result and result.get("vote") in targets:
            return result
        return {"vote": random.choice(targets), "reason": "综合判断"}

    def hunter_shoot(self, alive_players, history):
        targets = [p for p in alive_players if p != self.name]
        if not targets:
            return {"shoot": None}
        prompt = (
            f'狼人杀猎人{self.name}死亡，可开枪带走一人。'
            f'存活：{targets}。记录：{history[-200:]}'
            f'直接输出JSON：{{"shoot": "{targets[0]}"}}'
        )
        result = self._call(prompt)
        if result and result.get("shoot") in targets:
            return result
        return {"shoot": random.choice(targets)}
