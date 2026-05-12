import streamlit as st
import plotly.express as px
from engine import GameEngine
from ai_brain import AIBrain

st.set_page_config(layout="wide", page_title="AI 狼人杀博弈实验室")

if 'engine' not in st.session_state:
    st.session_state.engine = GameEngine()
    st.session_state.ai_bots = {name: AIBrain(name, role) for name, role in st.session_state.engine.players.items() if name != "你"}

st.title("🐺 AI 狼人杀：非对称信息博弈模拟器")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 游戏进程")
    for msg in st.session_state.engine.history:
        st.write(msg)
    
    user_input = st.text_input("你的发言：", key="user_say")
    if st.button("发送并开始 AI 回合"):
        # 1. 记录玩家发言
        st.session_state.engine.history.append(f"你：{user_input}")
        
        # 2. 轮流触发 AI 思考
        for name, bot in st.session_state.ai_bots.items():
            result = bot.think_and_speak(st.session_state.engine.get_game_state(), list(st.session_state.engine.players.keys()))
            st.session_state.engine.history.append(f"{name}: {result['speech']}")
            st.session_state.engine.update_matrix(name, result['scores'])
        st.rerun()

with col2:
    st.subheader("📊 怀疑度矩阵 (Heatmap)")
    # 展示 AI 之间的怀疑程度，这就是 BDA 的量化展现
    fig = px.imshow(st.session_state.engine.matrix, 
                    labels=dict(x="被怀疑者", y="评价者", color="怀疑度"),
                    color_continuous_scale="RdBu_r", range_color=[0, 100])
    st.plotly_chart(fig)

st.sidebar.info("作为一个 BDA 学生，你可以向面试官展示这个矩阵如何随时间坍缩，从而揭示博弈论中的信息传递。")