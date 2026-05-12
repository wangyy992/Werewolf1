import streamlit as st
import plotly.express as px
from engine import GameEngine
from ai_brain import AIBrain

st.set_page_config(layout="wide", page_title="狼人杀博弈模拟器")

# 初始化游戏引擎
if 'engine' not in st.session_state:
    st.session_state.engine = GameEngine()
    st.session_state.ai_bots = {name: AIBrain(name, role) for name, role in st.session_state.engine.players.items() if name != "你"}

st.title("🐺 AI 狼人杀：非对称信息博弈模拟器")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 游戏进程")
    # 容器用于显示对话历史
    chat_container = st.container(height=400)
    for msg in st.session_state.engine.history:
        chat_container.write(msg)
    
    user_input = st.text_input("在这里输入你的发言，然后按 Enter：")
    if user_input:
        st.session_state.engine.history.append(f"你：{user_input}")
        
        # 触发 AI 思考
        with st.spinner('AI 正在逻辑分析...'):
            for name, bot in st.session_state.ai_bots.items():
                result = bot.think_and_speak("\n".join(st.session_state.engine.history), list(st.session_state.engine.players.keys()))
                st.session_state.engine.history.append(f"**{name}**: {result['speech']}")
                st.session_state.engine.update_matrix(name, result['scores'])
        st.rerun()

with col2:
    st.subheader("📊 怀疑度热力图")
    fig = px.imshow(st.session_state.engine.matrix, 
                    labels=dict(x="被怀疑者", y="评价者", color="怀疑度"),
                    color_continuous_scale="RdBu_r", range_color=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    st.caption("注：红色代表高怀疑度，蓝色代表信任。")