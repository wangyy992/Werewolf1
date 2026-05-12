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
        # 根据不同阶段给 AI 不同的指令
        context = f"你是{self.name}，身份是{self.role}。当前存活：{alive_players}。"
        
        if phase == "NIGHT":
            if self.role == "狼人":
                task = "请从存活的非狼人玩家中选一个杀掉。只需返回JSON。"
            else:
                return None # 非狼人在晚上不发言
        elif phase == "DAY":
            task = "这是白天发言环节，请分析形势并简短发言（50字内），并给所有人打分（0-100，100最像狼）。"
        else: # VOTE
            task = "请决定你今天要投票给谁。只需返回JSON。"

        prompt = f"{context}\n历史记录：{history}\n任务：{task}\n输出格式：{{\"speech\": \"...\", \"scores\": {{...}}, \"target\": \"被选者名字\"}}"
        
        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
        except:
            return {"speech": "我保持沉默。", "scores": {p: 50 for p in alive_players}, "target": None}
