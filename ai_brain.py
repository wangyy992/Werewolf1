import google.generativeai as genai
import json
import streamlit as st

class AIBrain:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        # 从 Streamlit 的 Secrets 中读取 Key
        api_key = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def think_and_speak(self, history, alive_players):
        prompt = f"""
        你正在玩狼人杀。你的名字是 {self.name}，身份是 {self.role}。
        当前存活：{', '.join(alive_players)}。
        记录：{history}
        任务：
        1. 写一段50字内的中文发言，要有逻辑。
        2. 给存活玩家打分（0-100，100最像狼）。
        必须输出 JSON: {{"speech": "...", "scores": {{"玩家名": 分数}}}}
        """
        try:
            response = self.model.generate_content(prompt)
            json_str = response.text.replace('```json', '').replace('
```', '').strip()
            return json.loads(json_str)
        except:
            return {"speech": "我还在观察...", "scores": {p: 50 for p in alive_players}}