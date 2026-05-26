"""
Tela de revisão: Leonardo aprova/rejeita/edita questões geradas.
Rode com: streamlit run review_app.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database import (
    get_pending_questions, update_question_status,
    get_stats, init_db
)

st.set_page_config(
    page_title="NeuroCases — Dr. Leonardo Furtado",
    page_icon="🧠",
    layout="wide"
)

init_db()

# ── Branding CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif !important;
}

/* Header da página */
.brand-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 0 8px 0;
    border-bottom: 2px solid #1a1a1a;
    margin-bottom: 24px;
}
.brand-header img {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    object-fit: cover;
}
.brand-title {
    font-size: 22px;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
    line-height: 1.2;
}
.brand-subtitle {
    font-size: 13px;
    color: #666;
    margin: 0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1a1a1a !important;
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stMetric label {
    color: #aaaaaa !important;
}

/* Botão aprovar */
div.stButton > button[kind="primary"] {
    background-color: #1a1a1a;
    color: white;
    border: none;
    border-radius: 4px;
    font-family: 'Lato', sans-serif;
    font-weight: 700;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #333333;
}

/* Cards de questão */
div[data-testid="stExpander"] {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
}

/* Remove footer Streamlit */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar: stats e controles ──────────────────────────────────────────────
PHOTO_PATH = str((Path(__file__).parent.parent / "profile_photo.jpg").resolve())

with st.sidebar:
    # Foto + nome
    try:
        st.image(PHOTO_PATH, width=80)
    except Exception:
        pass
    st.markdown("**Dr. Leonardo Furtado Freitas**")
    st.caption("Neurorradiologista | EDiNR")
    st.caption("@drleonardofurtado")
    st.divider()

    stats = get_stats()
    st.metric("Total de questões", stats["total_questions"])
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Aprovadas", stats["approved"])
    col2.metric("⏳ Pendentes", stats["pending"])
    col3.metric("❌ Rejeitadas", stats["rejected"])

    st.divider()
    st.caption(f"Casos coletados: {stats['total_cases']}")
    st.caption(f"Casos processados: {stats['processed_cases']}")

    st.divider()
    if st.button("🔄 Recarregar", use_container_width=True):
        st.rerun()

# ── Header com branding ──────────────────────────────────────────────────────
try:
    import base64
    with open(PHOTO_PATH, "rb") as f:
        photo_b64 = base64.b64encode(f.read()).decode()
    photo_html = f'<img src="data:image/jpeg;base64,{photo_b64}">'
except Exception:
    photo_html = "🧠"

st.markdown(f"""
<div class="brand-header">
    {photo_html}
    <div>
        <p class="brand-title">NeuroCases</p>
        <p class="brand-subtitle">Dr. Leonardo Furtado Freitas · Neurorradiologista · @drleonardofurtado</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.subheader("Revisão de Questões")
st.caption("Aprove, rejeite ou edite cada questão antes de publicar no banco final.")

# ── Carrega questões pendentes ───────────────────────────────────────────────
questions = get_pending_questions(limit=50)

if not questions:
    st.success("Nenhuma questão pendente! Rode o pipeline para gerar mais.")
    st.info("Execute: `python run_pipeline.py`")
    st.stop()

# Filtros rápidos
col_f1, col_f2, col_f3 = st.columns(3)
ALL_CATEGORIES = [
    "Todos",
    "── ENCÉFALO ──",
    "tumor-cerebral", "avc-isquemico", "hemorragia-intracraniana",
    "desmielinizante", "neuroinfeccao", "neurodegenerativo",
    "malformacao-cerebral", "trauma-craniano", "doenca-metabolica-toxica",
    "hidrocefalia", "meninges", "nervos-cranianos",
    "── VASCULAR ──",
    "aneurisma-malformacao-vascular", "trombose-venosa-cerebral", "vasculite",
    "── COLUNA ──",
    "coluna-degenerativa", "tumor-medular", "trauma-raquimedular",
    "mielopatia", "disrafia-espinhal",
    "── PESCOÇO ──",
    "tumor-cabeca-pescoco", "tiroide-paratiroide", "glandulas-salivares",
    "espacos-cervicais", "vascular-cervical", "linfonodos-cervicais", "laringe-hipofaringe",
    "── PEDIATRIA ──",
    "tumor-pediatrico", "leucodistrofia", "neuroimagem-neonatal",
    "malformacao-pediatrica", "infeccao-pediatrica", "trauma-pediatrico",
    "epilepsia-pediatrica", "avc-pediatrico",
    "── ESPECIAL ──",
    "orbita", "base-cranio", "hipofise-sela", "outro",
]
# Inclui categorias que já existem no banco mas não estão na lista fixa
existing = set(q["category"] or "outro" for q in questions)
extra = [c for c in existing if c not in ALL_CATEGORIES]
categories = ALL_CATEGORIES + extra
diffs = ["Todos", "fácil", "médio", "difícil"]
sel_cat = col_f1.selectbox("Categoria", categories)
sel_dif = col_f2.selectbox("Dificuldade", diffs)
search_term = col_f3.text_input("Buscar no enunciado", placeholder="ex: glioma, AVC...")

filtered = questions
if sel_cat != "Todos":
    filtered = [q for q in filtered if q.get("category") == sel_cat]
if sel_dif != "Todos":
    filtered = [q for q in filtered if q.get("difficulty") == sel_dif]
if search_term:
    filtered = [q for q in filtered if search_term.lower() in (q.get("question_text") or "").lower()]

st.caption(f"Mostrando {len(filtered)} questão(ões) pendente(s)")
st.divider()

# ── Renderiza cada questão ────────────────────────────────────────────────────
for q in filtered:
    with st.container():
        # Header
        badge_cat = q.get("category") or "outro"
        badge_dif = q.get("difficulty") or "?"
        badge_color = {"fácil": "🟢", "médio": "🟡", "difícil": "🔴"}.get(badge_dif, "⚪")

        st.markdown(f"**#{q['id']} — {badge_cat.upper()}** &nbsp; {badge_color} {badge_dif}")
        st.caption(f"Fonte: [{q.get('pmc_id')}](https://pmc.ncbi.nlm.nih.gov/articles/{q.get('pmc_id')}/) — {q.get('case_title','')[:60]}")

        col_q, col_img = st.columns([2, 1])

        with col_q:
            # Questão editável
            with st.expander("✏️ Editar / ver questão completa", expanded=True):
                qt = st.text_area("Enunciado", value=q["question_text"], height=120,
                                   key=f"qt_{q['id']}")
                c1, c2 = st.columns(2)
                oa = c1.text_input("A)", value=q["option_a"], key=f"oa_{q['id']}")
                ob = c1.text_input("B)", value=q["option_b"], key=f"ob_{q['id']}")
                oc = c2.text_input("C)", value=q["option_c"], key=f"oc_{q['id']}")
                od = c2.text_input("D)", value=q["option_d"], key=f"od_{q['id']}")

                ans_options = ["A", "B", "C", "D"]
                default_ans = q["correct_answer"] if q["correct_answer"] in ans_options else "A"
                corr = st.radio("Gabarito correto", ans_options,
                                index=ans_options.index(default_ans),
                                horizontal=True, key=f"corr_{q['id']}")

                expl = st.text_area("Explicação", value=q["explanation"], height=100,
                                     key=f"expl_{q['id']}")

        with col_img:
            if q.get("image_url"):
                try:
                    st.image(q["image_url"], caption=q.get("image_caption", ""), use_container_width=True)
                except Exception:
                    st.caption("⚠️ Imagem não disponível")
                    st.caption(q.get("image_url", ""))
            else:
                st.info("Sem imagem neste caso")

        # Botões de ação
        ba, br, bs = st.columns([1, 1, 2])

        if ba.button("✅ Aprovar", key=f"approve_{q['id']}", type="primary", use_container_width=True):
            updated = {
                "question_text": qt, "option_a": oa, "option_b": ob,
                "option_c": oc, "option_d": od, "correct_answer": corr, "explanation": expl
            }
            update_question_status(q["id"], "approved", updated)
            st.success(f"Questão #{q['id']} aprovada!")
            st.rerun()

        if br.button("❌ Rejeitar", key=f"reject_{q['id']}", use_container_width=True):
            update_question_status(q["id"], "rejected")
            st.warning(f"Questão #{q['id']} rejeitada.")
            st.rerun()

        st.divider()
