import google.generativeai as genai
import json

# 配置你的 API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")

class AIBrain:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def think_and_speak(self, history, alive_players):
        prompt = f"""
        你正在玩狼人杀。你的名字是 {self.name}，你的秘密身份是 {self.role}。
        当前存活玩家：{', '.join(alive_players)}。
        游戏历史记录：
        {history}

        请执行以下操作：
        1. 逻辑分析：分析谁最像狼人，谁最像好人。
        2. 发言：写一段简短的发言（50字以内），要有逻辑性，可以质疑他人或保护他人。
        3. 怀疑度打分：给所有存活玩家打分（0-100，0为绝对好人，100为绝对狼人）。

        必须以 JSON 格式输出，格式如下：
        {{
            "speech": "你的发言内容",
            "scores": {{"玩家名": 分数, ...}}
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            # 清理 Markdown 格式
            json_str = response.text.replace('```json', '').replace('
```', '').strip()
            return json.loads(json_str)
        except:
            # 容错处理
            return {"speech": "我正在观察，先听大家的。", "scores": {p: 50 for p in alive_players}}