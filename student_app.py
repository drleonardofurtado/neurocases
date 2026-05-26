"""
NeuroCases — Tela do Aluno
Responda questões, veja gabarito e explicação.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import sqlite3
import random
from database import DB_PATH, init_db

st.set_page_config(
    page_title="NeuroCases — Treinamento",
    page_icon="🧠",
    layout="wide"
)

init_db()

# ── CSS / Branding ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Lato', sans-serif !important; }

section[data-testid="stSidebar"] { background-color: #1a1a1a !important; }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] .stMetric label { color: #aaaaaa !important; }
/* Dropdowns dentro da sidebar: texto escuro para legibilidade */
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * { color: #1a1a1a !important; }
section[data-testid="stSidebar"] .stSelectbox span { color: #1a1a1a !important; }

.option-btn { width: 100%; text-align: left; padding: 12px 16px;
    border: 1px solid #e0e0e0; border-radius: 6px; background: white;
    font-size: 16px; cursor: pointer; margin-bottom: 8px; }
.correct   { background: #e8f5e9 !important; border-color: #4caf50 !important; font-weight: 700; }
.incorrect { background: #ffebee !important; border-color: #f44336 !important; }
.explanation-box { background: #f5f5f5; border-left: 4px solid #1a1a1a;
    padding: 16px 20px; border-radius: 0 6px 6px 0; margin-top: 16px; }
.score-bar { background: #1a1a1a; color: white; padding: 8px 16px;
    border-radius: 20px; font-weight: 700; display: inline-block; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    photo_path = os.path.join(os.path.dirname(__file__), "profile_photo.jpg")
    if os.path.exists(photo_path):
        st.image(photo_path, width=80)
    st.markdown("### Dr. Leonardo Furtado Freitas")
    st.markdown("Neurorradiologista | EDiNR")
    st.markdown("@drleonardofurtado")
    st.divider()

    # Filtros
    st.markdown("**Filtrar por categoria**")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM questions WHERE status='approved' ORDER BY category")
    cats = ["Todas"] + [r[0] for r in c.fetchall() if r[0]]

    c.execute("SELECT COUNT(*) FROM questions WHERE status='approved'")
    total_q = c.fetchone()[0]
    conn.close()

    selected_cat = st.selectbox("Categoria", cats, key="filter_cat", label_visibility="collapsed")
    selected_diff = st.selectbox("Dificuldade", ["Todas", "fácil", "médio", "difícil"], key="filter_diff")

    # Detecta mudança de filtro e reseta questão atual
    prev_cat  = st.session_state.get("_prev_cat", selected_cat)
    prev_diff = st.session_state.get("_prev_diff", selected_diff)
    if selected_cat != prev_cat or selected_diff != prev_diff:
        for k in ["current_q", "selected_option", "answered_current", "load_next"]:
            st.session_state.pop(k, None)
        st.session_state["_prev_cat"]  = selected_cat
        st.session_state["_prev_diff"] = selected_diff
        st.rerun()
    st.session_state["_prev_cat"]  = selected_cat
    st.session_state["_prev_diff"] = selected_diff

    st.divider()
    st.metric("Questões disponíveis", total_q)

    # Placar da sessão
    if "correct" not in st.session_state:
        st.session_state.correct = 0
        st.session_state.answered = 0

    if st.session_state.answered > 0:
        pct = int(st.session_state.correct / st.session_state.answered * 100)
        st.metric("Acertos", f"{st.session_state.correct}/{st.session_state.answered} ({pct}%)")

    if st.button("🔄 Resetar sessão"):
        for k in ["current_q", "selected_option", "answered_current", "correct", "answered"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Carregar questão ──────────────────────────────────────────────────────────
def load_question(cat, diff):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = "SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, category, difficulty, image_url FROM questions WHERE status='approved'"
    params = []
    if cat != "Todas":
        query += " AND category=?"
        params.append(cat)
    if diff != "Todas":
        query += " AND difficulty=?"
        params.append(diff)

    # Excluir já respondidas nessa sessão
    seen = st.session_state.get("seen_ids", set())
    if seen:
        placeholders = ",".join("?" * len(seen))
        query += f" AND id NOT IN ({placeholders})"
        params.extend(list(seen))

    query += " ORDER BY RANDOM() LIMIT 1"
    c.execute(query, params)
    row = c.fetchone()
    conn.close()
    return row

# ── Header ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 8])
with col1:
    if os.path.exists(photo_path):
        st.image(photo_path, width=56)
with col2:
    st.markdown("### 🧠 NeuroCases — Treinamento em Neuroimagem")
    st.markdown("*Dr. Leonardo Furtado Freitas · Neurorradiologista · @drleonardofurtado*")
st.divider()

# ── Sessão: carregar questão atual ────────────────────────────────────────────
if "seen_ids" not in st.session_state:
    st.session_state.seen_ids = set()

if "current_q" not in st.session_state or st.session_state.get("load_next"):
    q = load_question(selected_cat, selected_diff)
    if q:
        st.session_state.current_q = q
        st.session_state.selected_option = None
        st.session_state.answered_current = False
        st.session_state.load_next = False
    else:
        st.info("🎉 Você respondeu todas as questões disponíveis nessa categoria! Resetando...")
        st.session_state.seen_ids = set()
        st.session_state.load_next = True
        st.rerun()

q = st.session_state.get("current_q")
if not q:
    st.warning("Nenhuma questão encontrada com os filtros selecionados.")
    st.stop()

qid, text, a, b, c_opt, d, correct, explanation, category, difficulty, image_url = q

# ── Exibir questão ────────────────────────────────────────────────────────────
diff_color = {"fácil": "🟢", "médio": "🟡", "difícil": "🔴"}.get(difficulty, "⚪")
st.markdown(f"**{diff_color} {difficulty.upper()}** &nbsp;&nbsp; `{category}`", unsafe_allow_html=True)
st.markdown(f"### {text}")

# Imagem se disponível
if image_url:
    try:
        st.image(image_url, use_column_width=True)
    except:
        pass

st.markdown("---")

# ── Alternativas ──────────────────────────────────────────────────────────────
options = {"A": a, "B": b, "C": c_opt, "D": d}
answered = st.session_state.answered_current

cols = st.columns(2)
for i, (key, val) in enumerate(options.items()):
    with cols[i % 2]:
        if answered:
            if key == correct:
                st.success(f"**{key})** {val} ✅")
            elif key == st.session_state.selected_option:
                st.error(f"**{key})** {val} ❌")
            else:
                st.markdown(f"**{key})** {val}")
        else:
            if st.button(f"{key})  {val}", key=f"opt_{key}", use_container_width=True):
                st.session_state.selected_option = key
                st.session_state.answered_current = True
                st.session_state.answered += 1
                st.session_state.seen_ids.add(qid)
                if key == correct:
                    st.session_state.correct += 1
                st.rerun()

# ── Resultado e explicação ────────────────────────────────────────────────────
if answered:
    is_correct = st.session_state.selected_option == correct
    if is_correct:
        st.markdown("### ✅ Correto!")
    else:
        st.markdown(f"### ❌ Incorreto. A resposta correta é **{correct})**")

    st.markdown(f"""
    <div class="explanation-box">
    <strong>Explicação:</strong><br>{explanation}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➡️ Próxima questão", type="primary", use_container_width=False):
        st.session_state.load_next = True
        st.session_state.current_q = None
        st.rerun()
