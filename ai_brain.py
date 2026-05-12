import google.generativeai as genai
import json
import streamlit as st

class AIBrain:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        api_key = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def act(self, phase, history, alive_players):
        # 针对 BDA 逻辑优化：明确博弈目标
        persona = f"你是一名资深的狼人杀高玩，性格冷静且擅长伪装。你的名字是{self.name}，身份是{self.role}。"
        
        if phase == "NIGHT":
            if self.role == "狼人":
                task = f"天黑了。请从存活的非狼人玩家 {alive_players} 中选一个今晚杀掉。说明你的战术理由。"
            else:
                return None
        elif phase == "DAY":
            task = "现在是白天发言环节。请结合历史记录，分析谁的行为最可疑，并发表一段犀利的中文评论（50字左右）。必须给所有人重新打分（0-100，100为狼）。"
        else: # VOTE 阶段
            task = f"投票环节。请从 {alive_players} 中选择一个你认为最该出局的人。"

        prompt = f"""
        {persona}
        游戏进程历史：{history}
        当前存活玩家：{alive_players}
        
        你的指令：{task}
        
        **注意**：你必须严格返回以下 JSON 格式，不要包含任何额外文字：
        {{
            "speech": "你的发言内容",
            "scores": {{"玩家名": 分数}},
            "target": "你选择的行动目标名"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # 强化清洗：防止 AI 返回 Markdown 代码块
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].strip()
            
            result = json.loads(text)
            # 补全逻辑：如果 AI 没返回 scores，给个默认值防止报错
            if "scores" not in result:
                result["scores"] = {p: 50 for p in alive_players}
            return result
        except Exception as e:
            # 记录错误，不再默认沉默
            error_msg = f"逻辑思考中断({str(e)[:20]})"
            return {"speech": error_msg, "scores": {p: 50 for p in alive_players}, "target": None}
