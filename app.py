import streamlit as st
import plotly.express as px
from engine import GameEngine
from ai_brain import AIBrain

st.set_page_config(layout="wide", page_title="硬核狼人杀模拟器")

if 'engine' not in st.session_state:
    st.session_state.engine = GameEngine()
    st.session_state.ai_bots = {name: AIBrain(name, role) for name, role in st.session_state.engine.players.items() if name != "你"}

engine = st.session_state.engine

st.title(f"🌙 第 {engine.day_count} 天 - {engine.phase}")

# 侧边栏显示个人信息
st.sidebar.header("你的信息")
st.sidebar.info(f"你的身份：**{engine.players['你']}**")
st.sidebar.write("存活情况：")
for name in engine.player_names:
    status = "✅" if engine.alive_status[name] else "💀"
    st.sidebar.write(f"{status} {name}")

col1, col2 = st.columns([2, 1])

with col1:
    # 流程控制按钮
    if engine.phase == "READY":
        if st.button("开始游戏 (天黑请闭眼)"):
            engine.next_phase()
            st.rerun()

    elif engine.phase == "NIGHT":
        st.warning("🌙 天黑请闭眼... 狼人正在行动")
        if st.button("进入白天"):
            # 模拟 AI 狼人杀人逻辑
            for name, bot in st.session_state.ai_bots.items():
                if bot.role == "狼人" and engine.alive_status[name]:
                    res = bot.act("NIGHT", engine.history, engine.get_alive_players())
                    if res and res.get("target"):
                        engine.night_actions["killed"] = res["target"]
            engine.next_phase()
            st.rerun()

    elif engine.phase == "DAY":
        st.success("☀️ 天亮了！")
        if engine.night_actions["killed"]:
            st.error(f"昨晚，{engine.night_actions['killed']} 倒在了血泊中。")
            engine.alive_status[engine.night_actions["killed"]] = False
            engine.night_actions["killed"] = None
        
        # 白天发言逻辑...
        user_speech = st.text_input("发表你的遗言或推理：")
        if st.button("结束发言并进入投票"):
            engine.history.append(f"你：{user_speech}")
            for name, bot in st.session_state.ai_bots.items():
                if engine.alive_status[name]:
                    res = bot.act("DAY", engine.history, engine.get_alive_players())
                    engine.history.append(f"{name}：{res['speech']}")
                    engine.update_matrix(name, res['scores'])
            engine.next_phase()
            st.rerun()

    elif engine.phase == "VOTE":
        st.subheader("🗳️ 投票环节")
        vote_target = st.selectbox("选择你要放逐的目标：", engine.get_alive_players())
        if st.button("确认投票"):
            # 简化逻辑：直接处决玩家选中的人或计算 AI 票数
            engine.alive_status[vote_target] = False
            st.write(f"{vote_target} 被投票出局！")
            engine.next_phase() # 回到 NIGHT 或 READY
            st.rerun()

    # 显示对话历史
    with st.expander("查看完整记录", expanded=True):
        for h in engine.history[-10:]:
            st.write(h)

with col2:
    st.subheader("📊 实时怀疑度矩阵")
    fig = px.imshow(engine.matrix, color_continuous_scale="RdBu_r", range_color=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
