import streamlit as st
import plotly.express as px
import time
import random
from engine import GameEngine
from ai_brain import AIBrain

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="🐺 狼人杀 AI 博弈",
    page_icon="🐺",
    initial_sidebar_state="collapsed"
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Sans+SC:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans SC', sans-serif;
    background-color: #0d0d0d;
    color: #e8d5b0;
}
.stApp { background: #0d0d0d; }

h1, h2, h3 { font-family: 'Ma Shan Zheng', serif !important; color: #f0c060 !important; }

.phase-banner {
    text-align: center;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 1.3em;
    font-weight: 600;
    margin-bottom: 16px;
    letter-spacing: 2px;
}
.night-banner { background: linear-gradient(90deg, #1a0030, #0d001a); border: 1px solid #6020a0; color: #c090ff; }
.day-banner   { background: linear-gradient(90deg, #2a1800, #1a0e00); border: 1px solid #c07000; color: #f0c060; }
.vote-banner  { background: linear-gradient(90deg, #1a0000, #2a0000); border: 1px solid #a02020; color: #ff8080; }

.player-card {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    margin: 4px;
    font-size: 0.85em;
    font-weight: 600;
}
.alive-card  { background: #1a2a1a; border: 1px solid #40a040; color: #80e080; }
.dead-card   { background: #2a1a1a; border: 1px solid #603030; color: #806060; text-decoration: line-through; }
.you-card    { border: 2px solid #f0c060 !important; color: #f0c060 !important; }

.role-box {
    text-align: center;
    padding: 10px 20px;
    border-radius: 8px;
    background: #1a1008;
    border: 1px solid #c07000;
    margin-bottom: 12px;
}
.role-wolf   { border-color: #a02020 !important; background: #1a0808 !important; }
.role-seer   { border-color: #2060a0 !important; background: #080818 !important; }
.role-witch  { border-color: #6020a0 !important; background: #100818 !important; }
.role-hunter { border-color: #806000 !important; background: #181000 !important; }

.log-container {
    background: #0a0a0a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 16px;
    height: 380px;
    overflow-y: auto;
    font-size: 0.88em;
    line-height: 1.7;
}
.stButton button {
    background: #2a1800 !important;
    color: #f0c060 !important;
    border: 1px solid #c07000 !important;
    border-radius: 6px !important;
    font-family: 'Noto Sans SC', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 1px;
}
.stButton button:hover {
    background: #3a2800 !important;
    border-color: #f0c060 !important;
}
.stTextInput input, .stSelectbox select {
    background: #1a1a1a !important;
    color: #e8d5b0 !important;
    border-color: #3a3a3a !important;
}
div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label {
    color: #c0a060 !important;
}
.stAlert { background: #1a1008 !important; border-color: #c07000 !important; }
</style>
""", unsafe_allow_html=True)

# ─── API Key ────────────────────────────────────────────────────────────────────
API_KEY = "AIzaSyAX6VJJtydkkKwPWIPZDwpXf8BBi_6_st0"

# ─── Helpers ───────────────────────────────────────────────────────────────────
ROLE_ICONS = {"狼人": "🐺", "预言家": "🔮", "女巫": "🧙", "猎人": "🏹", "平民": "👤"}
PHASE_LABELS = {
    "night": ("🌙 黑夜", "night-banner"),
    "day_discuss": ("☀️ 白天 · 发言阶段", "day-banner"),
    "day_vote": ("⚖️ 白天 · 投票阶段", "vote-banner"),
}

def role_class(role):
    return {"狼人": "role-wolf", "预言家": "role-seer", "女巫": "role-witch", "猎人": "role-hunter"}.get(role, "")

def get_ai_bots(engine):
    return {
        name: AIBrain(name, role, API_KEY)
        for name, role in engine.players.items()
        if name != "你"
    }

def init_game():
    st.session_state.engine = GameEngine(user_name="你")
    st.session_state.ai_bots = get_ai_bots(st.session_state.engine)
    st.session_state.seer_results = {}   # {checked_player: "狼人"/"好人"}
    st.session_state.speech_done = []    # who has spoken today
    st.session_state.wolf_kill_target = None
    st.session_state.user_voted = False
    st.session_state.night_processed = False
    st.session_state.discuss_ai_done = False

# ─── Init ───────────────────────────────────────────────────────────────────────
if 'engine' not in st.session_state:
    init_game()

engine = st.session_state.engine
ai_bots = st.session_state.ai_bots
user_role = engine.players["你"]
user_alive = engine.alive["你"]

# ─── Title ──────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;letter-spacing:6px;'>🐺 狼人杀 · AI 博弈</h1>", unsafe_allow_html=True)

# ─── Layout ─────────────────────────────────────────────────────────────────────
left, mid, right = st.columns([1.2, 2, 1.2])

# ══════════════ LEFT: Player List + Role ════════════════════════════════════════
with left:
    st.markdown("### 玩家列表")
    for name in list(engine.players.keys()):
        alive = engine.alive[name]
        card_class = "alive-card" if alive else "dead-card"
        you_class = " you-card" if name == "你" else ""
        role_shown = engine.players[name] if not alive else ("?" if name != "你" else engine.players[name])
        icon = ROLE_ICONS.get(engine.players[name], "👤") if (not alive or name == "你") else "❓"
        st.markdown(
            f'<span class="player-card {card_class}{you_class}">{icon} {name} {"· " + role_shown if not alive or name == "你" else ""}</span>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    # Your role box
    rclass = role_class(user_role)
    st.markdown(f"""
    <div class="role-box {rclass}">
        <div style="font-size:2em">{ROLE_ICONS.get(user_role,'👤')}</div>
        <div style="font-size:1.1em;font-weight:600;color:#f0c060">你的身份</div>
        <div style="font-size:1.4em;margin-top:4px">{user_role}</div>
    </div>
    """, unsafe_allow_html=True)

    if user_role == "预言家" and st.session_state.seer_results:
        st.markdown("**🔮 查验结果：**")
        for p, r in st.session_state.seer_results.items():
            color = "#ff8080" if r == "狼人" else "#80e080"
            st.markdown(f'<span style="color:{color}">• {p} → {r}</span>', unsafe_allow_html=True)

    if engine.game_over:
        if engine.winner == "village":
            st.success("🎉 好人阵营胜利！")
        else:
            st.error("🐺 狼人阵营胜利！")
        if st.button("🔄 重新开始"):
            init_game()
            st.rerun()

# ══════════════ MID: Game Log + Actions ═════════════════════════════════════════
with mid:
    # Phase banner
    phase_label, phase_css = PHASE_LABELS.get(engine.phase, ("", "day-banner"))
    st.markdown(
        f'<div class="phase-banner {phase_css}">第 {engine.day} 天 · {phase_label}</div>',
        unsafe_allow_html=True
    )

    # Game log
    log_html = "<br>".join(engine.history[-40:]) if engine.history else "<i style='color:#555'>游戏开始，等待夜晚降临...</i>"
    st.markdown(f'<div class="log-container">{log_html}</div>', unsafe_allow_html=True)

    st.markdown("")

    # ── GAME OVER ──
    if engine.game_over:
        st.markdown("### 游戏结束")
        if engine.winner == "village":
            st.markdown("## 🎉 好人阵营胜利！")
        else:
            st.markdown("## 🐺 狼人阵营胜利！")
        st.markdown("**所有玩家身份：**")
        for name, role in engine.players.items():
            alive_str = "（存活）" if engine.alive[name] else "（已出局）"
            st.markdown(f"- {ROLE_ICONS.get(role,'👤')} **{name}** — {role} {alive_str}")
        st.stop()

    # ────────────────────────────────────────────────────────────────────────────
    # PHASE: NIGHT
    # ────────────────────────────────────────────────────────────────────────────
    if engine.phase == "night":

        if not user_alive:
            st.info("你已出局，等待夜晚结束...")
            if st.button("⏭️ 跳过夜晚"):
                engine.phase = "day_discuss"
                st.session_state.night_processed = False
                st.session_state.discuss_ai_done = False
                st.session_state.speech_done = []
                st.rerun()
        else:
            # ── Seer: choose who to check ──────────────────────────────────────
            if user_role == "预言家" and not st.session_state.night_processed:
                st.markdown("#### 🔮 预言家：请选择今晚查验的玩家")
                check_targets = [p for p in engine.get_alive_players() if p != "你"]
                checked = st.selectbox("查验目标", check_targets, key="seer_check")
                if st.button("✅ 确认查验"):
                    result = "狼人" if engine.players[checked] == "狼人" else "好人"
                    st.session_state.seer_results[checked] = result
                    engine.history.append(f"🔮 [仅你可见] 查验 **{checked}**：{result}")
                    st.session_state.night_processed = True
                    st.rerun()

            # ── Wolf: choose kill target ───────────────────────────────────────
            elif user_role == "狼人" and not st.session_state.night_processed:
                fellow = [n for n, r in engine.players.items() if r == "狼人" and n != "你" and engine.alive[n]]
                st.markdown(f"#### 🐺 狼人：你的同伴是 {', '.join(fellow) if fellow else '无'}")
                kill_targets = [p for p in engine.get_alive_players() if engine.players[p] != "狼人"]
                kill_choice = st.selectbox("选择今晚击杀目标", kill_targets, key="wolf_kill")
                if st.button("🔪 确认击杀"):
                    st.session_state.wolf_kill_target = kill_choice
                    engine.history.append(f"🐺 [狼人内部] 你决定今晚击杀 **{kill_choice}**。")
                    st.session_state.night_processed = True
                    st.rerun()

            # ── Witch: save/poison ─────────────────────────────────────────────
            elif user_role == "女巫" and not st.session_state.night_processed:
                # First resolve wolf kill by AI wolves
                if st.session_state.wolf_kill_target is None:
                    wolves = [n for n, r in engine.players.items() if r == "狼人" and engine.alive[n]]
                    if wolves:
                        wolf_bot = ai_bots.get(wolves[0])
                        if wolf_bot:
                            result = wolf_bot.night_wolf_action(engine.get_alive_players(), wolves)
                            st.session_state.wolf_kill_target = result.get("kill")
                    if not st.session_state.wolf_kill_target:
                        alive_non_wolf = [p for p in engine.get_alive_players() if engine.players[p] != "狼人"]
                        st.session_state.wolf_kill_target = random.choice(alive_non_wolf) if alive_non_wolf else None

                kill_target = st.session_state.wolf_kill_target
                has_save = engine.witch_potion["save"]
                has_poison = engine.witch_potion["poison"]

                st.markdown(f"#### 🧙 女巫行动")
                st.markdown(f"今晚狼人击杀了：**{kill_target}**")

                save_choice = False
                if has_save and kill_target:
                    save_choice = st.checkbox(f"💊 使用解药救 {kill_target}", key="witch_save")

                poison_target = None
                if has_poison and not save_choice:
                    use_poison = st.checkbox("🧪 使用毒药", key="witch_use_poison")
                    if use_poison:
                        poison_targets = [p for p in engine.get_alive_players() if p != "你" and p != kill_target]
                        if poison_targets:
                            poison_target = st.selectbox("选择毒杀目标", poison_targets, key="witch_poison_target")

                if st.button("✅ 确认行动"):
                    engine.pending_witch_action = {"save": save_choice, "poison": poison_target, "kill": kill_target}
                    st.session_state.night_processed = True
                    st.rerun()

            # ── Civilian / Hunter: just wait ───────────────────────────────────
            elif user_role in ("平民", "猎人") and not st.session_state.night_processed:
                st.info("🌙 夜晚降临，请闭眼等待...")
                if st.button("⏭️ 等待天亮"):
                    st.session_state.night_processed = True
                    st.rerun()

            # ── Process night after user action ───────────────────────────────
            if st.session_state.night_processed and engine.phase == "night":
                with st.spinner("🌙 夜晚进行中，处理各方行动..."):
                    time.sleep(1)
                    alive = engine.get_alive_players()

                    # 1. Wolf kill (AI wolves if user isn't wolf)
                    kill_target = st.session_state.wolf_kill_target
                    if kill_target is None:
                        wolves = [n for n, r in engine.players.items() if r == "狼人" and engine.alive[n]]
                        ai_wolves = [w for w in wolves if w != "你"]
                        if ai_wolves:
                            wolf_bot = ai_bots.get(ai_wolves[0])
                            if wolf_bot:
                                res = wolf_bot.night_wolf_action(alive, wolves)
                                kill_target = res.get("kill")
                        if not kill_target:
                            villagers = [p for p in alive if engine.players[p] != "狼人"]
                            kill_target = random.choice(villagers) if villagers else None
                        st.session_state.wolf_kill_target = kill_target

                    # 2. Seer (AI seer)
                    ai_seer = next((n for n, r in engine.players.items() if r == "预言家" and n != "你" and engine.alive[n]), None)
                    if ai_seer:
                        seer_bot = ai_bots.get(ai_seer)
                        if seer_bot:
                            res = seer_bot.night_seer_action(alive)
                            # result is private, no public reveal

                    # 3. Witch (AI witch)
                    witch = next((n for n, r in engine.players.items() if r == "女巫" and n != "你" and engine.alive[n]), None)
                    witch_action = engine.pending_witch_action  # user witch action if any
                    if witch and not witch_action:
                        witch_bot = ai_bots.get(witch)
                        if witch_bot and kill_target:
                            wa = witch_bot.night_witch_action(
                                kill_target,
                                engine.witch_potion["save"],
                                engine.witch_potion["poison"],
                                alive
                            )
                            witch_action = {**wa, "kill": kill_target}

                    # Apply witch actions
                    saved = False
                    if witch_action:
                        if witch_action.get("save") and engine.witch_potion["save"]:
                            engine.witch_potion["save"] = False
                            saved = True
                            engine.history.append(f"🧙 女巫使用解药，{kill_target} 得救了！")
                        if witch_action.get("poison") and engine.witch_potion["poison"]:
                            poison_tgt = witch_action["poison"]
                            engine.witch_potion["poison"] = False
                            engine.history.append(f"🧪 女巫使用毒药！")
                            role_of_poisoned = engine.eliminate_player(poison_tgt, "被女巫毒杀")
                            # hunter trigger
                            if role_of_poisoned == "猎人":
                                engine.hunter_trigger = poison_tgt
                        engine.pending_witch_action = None

                    # Apply wolf kill
                    if kill_target and engine.alive.get(kill_target, False) and not saved:
                        role_killed = engine.eliminate_player(kill_target, "被狼人击杀")
                        if role_killed == "猎人":
                            engine.hunter_trigger = kill_target
                    elif saved:
                        pass
                    else:
                        engine.history.append("🌙 今晚是平安夜，无人死亡。")

                    # Handle hunter trigger (AI)
                    if engine.hunter_trigger and engine.hunter_trigger != "你":
                        hunter_bot = ai_bots.get(engine.hunter_trigger)
                        if hunter_bot:
                            res = hunter_bot.hunter_shoot(engine.get_alive_players(), engine.get_public_history())
                            shoot_tgt = res.get("shoot")
                            if shoot_tgt and engine.alive.get(shoot_tgt, False):
                                engine.history.append(f"🏹 猎人 **{engine.hunter_trigger}** 临死前开枪！")
                                engine.eliminate_player(shoot_tgt, "被猎人射杀")
                        engine.hunter_trigger = None

                    engine.check_game_over()
                    st.session_state.wolf_kill_target = None
                    st.session_state.night_processed = False

                    if not engine.game_over:
                        engine.phase = "day_discuss"
                        st.session_state.discuss_ai_done = False
                        st.session_state.speech_done = []

                st.rerun()

    # ────────────────────────────────────────────────────────────────────────────
    # PHASE: DAY DISCUSS
    # ────────────────────────────────────────────────────────────────────────────
    elif engine.phase == "day_discuss":

        # AI speeches (run once)
        if not st.session_state.discuss_ai_done:
            with st.spinner("☀️ AI 玩家正在发言..."):
                alive = engine.get_alive_players()
                for name, bot in ai_bots.items():
                    if engine.alive.get(name, False):
                        result = bot.day_speech(
                            engine.get_public_history(),
                            alive,
                            engine.day,
                            seer_results=st.session_state.seer_results if engine.players[name] == "预言家" else None
                        )
                        speech = result.get("speech", "...")
                        engine.history.append(f"**{name}**（{ROLE_ICONS.get(engine.players[name],'?')}）：{speech}")
                        engine.update_matrix(name, result.get("scores", {}))
                st.session_state.discuss_ai_done = True
            st.rerun()

        # User speech
        if user_alive:
            # Hunter shoot if triggered
            if engine.hunter_trigger == "你":
                st.markdown("#### 🏹 你是猎人，可以开枪带走一名玩家！")
                shoot_targets = [p for p in engine.get_alive_players() if p != "你"]
                shoot_choice = st.selectbox("开枪目标", shoot_targets, key="hunter_shoot")
                if st.button("🔫 开枪！"):
                    engine.history.append(f"🏹 猎人 **你** 临死前开枪！")
                    engine.eliminate_player(shoot_choice, "被猎人射杀")
                    engine.hunter_trigger = None
                    engine.check_game_over()
                    st.rerun()
            else:
                st.markdown("#### 💬 你的发言")
                user_speech = st.text_area("请发表你的看法（可选）", max_chars=200, key=f"speech_{engine.day}", height=80)
                if st.button("📢 发言并进入投票"):
                    if user_speech.strip():
                        engine.history.append(f"**你**（{ROLE_ICONS.get(user_role,'?')}）：{user_speech}")
                    engine.phase = "day_vote"
                    st.session_state.user_voted = False
                    st.rerun()
        else:
            st.info("你已出局，旁观发言阶段。")
            if st.button("⏭️ 进入投票"):
                engine.phase = "day_vote"
                st.session_state.user_voted = False
                st.rerun()

    # ────────────────────────────────────────────────────────────────────────────
    # PHASE: DAY VOTE
    # ────────────────────────────────────────────────────────────────────────────
    elif engine.phase == "day_vote":

        alive_players = engine.get_alive_players()

        # User vote
        if user_alive and not st.session_state.user_voted:
            st.markdown("#### ⚖️ 投票放逐玩家")
            vote_targets = [p for p in alive_players if p != "你"]
            vote_choice = st.selectbox("你认为谁是狼人？", vote_targets, key="user_vote")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✋ 投票放逐"):
                    engine.votes["你"] = vote_choice
                    engine.history.append(f"你投票放逐：**{vote_choice}**")
                    st.session_state.user_voted = True
                    st.rerun()
            with col_b:
                if st.button("🤐 弃权"):
                    st.session_state.user_voted = True
                    st.rerun()

        elif st.session_state.user_voted or not user_alive:
            # AI votes
            with st.spinner("🗳️ AI 玩家投票中..."):
                time.sleep(0.5)
                for name, bot in ai_bots.items():
                    if engine.alive.get(name, False) and name not in engine.votes:
                        res = bot.day_vote(alive_players, engine.get_public_history())
                        vote_tgt = res.get("vote")
                        if vote_tgt and vote_tgt in alive_players:
                            engine.votes[name] = vote_tgt
                            reason = res.get("reason", "")
                            engine.history.append(f"**{name}** 投票放逐：**{vote_tgt}**（{reason}）")

            # Tally
            eliminated = engine.tally_votes()
            engine.history.append(f"\n⚖️ 投票结果：**{eliminated}** 被放逐！")

            if eliminated:
                role_elim = engine.eliminate_player(eliminated, "被投票放逐")
                # Hunter trigger
                if role_elim == "猎人" and eliminated != "你":
                    hunter_bot = ai_bots.get(eliminated)
                    if hunter_bot:
                        res = hunter_bot.hunter_shoot(engine.get_alive_players(), engine.get_public_history())
                        shoot_tgt = res.get("shoot")
                        if shoot_tgt and engine.alive.get(shoot_tgt, False):
                            engine.history.append(f"🏹 猎人 **{eliminated}** 开枪！")
                            engine.eliminate_player(shoot_tgt, "被猎人射杀")
                elif role_elim == "猎人" and eliminated == "你":
                    engine.hunter_trigger = "你"

            engine.votes = {}
            engine.check_game_over()

            if not engine.game_over and engine.hunter_trigger != "你":
                engine.day += 1
                engine.phase = "night"
                st.session_state.night_processed = False
                st.session_state.user_voted = False

            st.rerun()

# ══════════════ RIGHT: Heatmap ════════════════════════════════════════════════
with right:
    st.markdown("### 📊 怀疑度矩阵")
    alive_list = engine.get_alive_players()
    sub_matrix = engine.matrix.loc[alive_list, alive_list]
    fig = px.imshow(
        sub_matrix,
        labels=dict(x="被怀疑", y="评价者", color="怀疑度"),
        color_continuous_scale="RdBu_r",
        range_color=[0, 100],
        text_auto=".0f",
        aspect="auto"
    )
    fig.update_layout(
        paper_bgcolor="#0d0d0d",
        plot_bgcolor="#0d0d0d",
        font=dict(color="#e8d5b0", size=11),
        margin=dict(l=0, r=0, t=20, b=0),
        coloraxis_colorbar=dict(
            tickfont=dict(color="#e8d5b0"),
            title=dict(font=dict(color="#e8d5b0"))
        )
    )
    fig.update_xaxes(tickfont=dict(color="#e8d5b0"))
    fig.update_yaxes(tickfont=dict(color="#e8d5b0"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🔴 红=高怀疑  🔵 蓝=信任")

    st.markdown("---")
    st.markdown("### 📜 已出局玩家")
    if engine.eliminated:
        for e in engine.eliminated:
            icon = ROLE_ICONS.get(e["role"], "👤")
            st.markdown(f"- {icon} **{e['name']}** ({e['role']}) — 第{e['day']}天 {e['reason']}")
    else:
        st.caption("暂无玩家出局")
