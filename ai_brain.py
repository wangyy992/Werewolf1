import google.generativeai as genai
import json
import streamlit as st

class AIBrain:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        # 确保你在 Streamlit Secrets 中配置了 GEMINI_KEY
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
        必须输出严格的 JSON 格式: {{"speech": "发言内容", "scores": {{"玩家名": 分数}}}}
        """
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text
            
            # 清理可能存在的 Markdown 代码块标记
            clean_text = raw_text.replace('```json', '').replace('```', '').strip()
            
            return json.loads(clean_text)
        except Exception as e:
            # 如果 AI 返回格式错误或 API 调用失败，返回保底数据
            return {
                "speech": "我还在观察大家的发言...", 
                "scores": {p: 50 for p in alive_players}
            }
