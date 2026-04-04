import os
import streamlit as st
from dotenv import load_dotenv

from agents.crew import run_crew
from utils import split_killer_line, parse_researcher_bullets, score_color, label_style, format_share_text

load_dotenv()

st.set_page_config(
    page_title="Shower Thought Validator",
    page_icon="🚿",
    layout="centered",
)

# Minimal CSS — only for things config.toml can't handle
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap');

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 3rem; padding-bottom: 5rem; max-width: 820px; }

/* Typography */
h1 { font-family: 'Lora', serif !important; }
p, div, span, label, textarea, input, select, button {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Agent cards */
.card {
    background: #161616;
    border: 1px solid #222;
    border-radius: 14px;
    padding: 20px;
    height: 100%;
}
.card-accent-top {
    height: 3px;
    border-radius: 14px 14px 0 0;
    margin: -20px -20px 16px -20px;
}
.agent-name {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.agent-persona {
    font-size: 0.58rem;
    color: #555;
    margin-top: 2px;
}
.body-text {
    font-size: 0.83rem;
    color: #c0c0c0;
    line-height: 1.7;
    margin: 0;
}
.killer {
    margin-top: 14px;
    padding: 10px 13px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-style: italic;
    line-height: 1.5;
}
.fact-row {
    display: flex;
    gap: 10px;
    margin-bottom: 8px;
    font-size: 0.8rem;
    color: #b0b0b0;
    line-height: 1.55;
}
.fact-arrow { color: #5b8dee; flex-shrink: 0; margin-top: 1px; }
.tag {
    display: inline-block;
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 1rem 0 2.5rem;">
    <h1 style="font-size: 2.2rem; font-weight: 700; color: #ffffff; margin-bottom: 10px; letter-spacing: -0.5px;">
        shower thought <span style="color: #a3e635;">validator</span>
    </h1>
    <p style="font-size: 0.75rem; color: #4a4a4a; letter-spacing: 0.08em; margin: 0;">
        type a thought &nbsp;·&nbsp; four agents argue &nbsp;·&nbsp; one judge decides
    </p>
</div>
""", unsafe_allow_html=True)


# ── Model selector ─────────────────────────────────────────────────────────────
PROVIDERS = {
    "Groq — Llama 3.3 70B  (free key)": "groq",
    "OpenAI — GPT-4o mini": "openai",
    "Google — Gemini 2.0 Flash": "google",
}
KEY_HINTS = {
    "groq":   ("leave blank to use on the house ✦",  'free key in 30s → <a href="https://console.groq.com" target="_blank" style="color:#a3e635;">console.groq.com</a> &nbsp;·&nbsp; <span style="color:#a3e635;">on the house</span> while capacity lasts'),
    "openai": ("sk-...",   'key → <a href="https://platform.openai.com" target="_blank" style="color:#a3e635;">platform.openai.com</a>'),
    "google": ("AIza...",  'key → <a href="https://aistudio.google.com/apikey" target="_blank" style="color:#a3e635;">aistudio.google.com</a>'),
}

col_p, col_k = st.columns([1, 1])
with col_p:
    provider_label = st.selectbox("Model", list(PROVIDERS.keys()), label_visibility="collapsed")
provider = PROVIDERS[provider_label]
placeholder, hint = KEY_HINTS[provider]

with col_k:
    api_key = st.text_input("API Key", placeholder=placeholder, type="password", label_visibility="collapsed")

st.markdown(f'<div style="font-size:0.68rem;color:#555;margin-top:2px;">↳ {hint}</div>', unsafe_allow_html=True)
st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)


# ── Input ──────────────────────────────────────────────────────────────────────
thought = st.text_area(
    "Your shower thought",
    placeholder="Restaurants should charge by time spent, not food ordered...",
    max_chars=280,
    height=100,
    label_visibility="collapsed",
)

char_count = len(thought)
col_c, col_b = st.columns([3, 1])
with col_c:
    color = "#e05555" if char_count > 250 else "#3a3a3a"
    st.markdown(f'<span style="font-size:0.65rem; color:{color};">{char_count} / 280</span>', unsafe_allow_html=True)
with col_b:
    validate = st.button("validate →", use_container_width=True)


# ── Run ────────────────────────────────────────────────────────────────────────
if validate:
    if not thought.strip():
        st.error("Write something first — even 'what if clouds are just sky cheese' counts.")
    elif not api_key.strip() and provider != "groq":
        st.error("Paste your API key above.")
    else:
        with st.spinner("agents are arguing... (~30s)"):
            try:
                st.session_state["results"] = run_crew(thought.strip(), provider, api_key.strip())
                st.session_state["thought"] = thought.strip()
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.session_state["results"] = None


# ── Results ────────────────────────────────────────────────────────────────────
results = st.session_state.get("results")
saved_thought = st.session_state.get("thought", "")

if results:
    st.markdown("<div style='margin: 2rem 0 1rem;'><hr style='border:none; border-top:1px solid #1e1e1e;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")

    # — Optimist —
    opt_body, opt_killer = split_killer_line(results["optimist"])
    with col1:
        st.markdown(f"""
<div class="card">
    <div class="card-accent-top" style="background:#a3e635;"></div>
    <div style="display:flex;align-items:center;gap:9px;margin-bottom:14px;">
        <span style="font-size:1.1rem;">🚀</span>
        <div>
            <div class="agent-name" style="color:#a3e635;">The Optimist</div>
            <div class="agent-persona">startup founder · every idea has a TAM</div>
        </div>
    </div>
    <p class="body-text">{opt_body}</p>
    {"<div class='killer' style='background:#0d1800; color:#a3e635; border-left: 3px solid #a3e635;'>\"" + opt_killer + "\"</div>" if opt_killer else ""}
</div>""", unsafe_allow_html=True)

    # — Cynic —
    cyn_body, cyn_killer = split_killer_line(results["cynic"])
    with col2:
        st.markdown(f"""
<div class="card">
    <div class="card-accent-top" style="background:#e05555;"></div>
    <div style="display:flex;align-items:center;gap:9px;margin-bottom:14px;">
        <span style="font-size:1.1rem;">💀</span>
        <div>
            <div class="agent-name" style="color:#e05555;">The Cynic</div>
            <div class="agent-persona">senior eng · your idea is a bug</div>
        </div>
    </div>
    <p class="body-text">{cyn_body}</p>
    {"<div class='killer' style='background:#180000; color:#e05555; border-left: 3px solid #e05555;'>\"" + cyn_killer + "\"</div>" if cyn_killer else ""}
</div>""", unsafe_allow_html=True)

    # — Researcher —
    bullets = parse_researcher_bullets(results["researcher"])
    facts_html = "".join(
        f'<div class="fact-row"><span class="fact-arrow">→</span><span>{b}</span></div>'
        for b in bullets
    )
    with col3:
        st.markdown(f"""
<div class="card">
    <div class="card-accent-top" style="background:#5b8dee;"></div>
    <div style="display:flex;align-items:center;gap:9px;margin-bottom:14px;">
        <span style="font-size:1.1rem;">🔍</span>
        <div>
            <div class="agent-name" style="color:#5b8dee;">The Researcher</div>
            <div class="agent-persona">wikipedia editor · citation needed</div>
        </div>
    </div>
    <div class="tag" style="background:#0a1520;color:#5b8dee;border:1px solid #1a3050;">⚡ web searched</div>
    {facts_html}
</div>""", unsafe_allow_html=True)

    # — Judge verdict —
    st.markdown("<div style='margin: 2rem 0 1rem;'><hr style='border:none; border-top:1px solid #1e1e1e;'></div>", unsafe_allow_html=True)

    sc = results["score"]
    lbl = results["label"]
    verdict_text = results["verdict"]
    sc_col = score_color(sc)
    lbl_bg, lbl_border, lbl_fg = label_style(lbl)

    st.markdown(f"""
<div style="background:#161616; border:1px solid #222; border-top:3px solid #f5d020;
            border-radius:14px; padding:24px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:24px;">
        <div style="flex:1;">
            <div style="display:flex; align-items:center; gap:9px; margin-bottom:14px;">
                <span style="font-size:1.1rem;">⚖️</span>
                <div>
                    <div class="agent-name" style="color:#f5d020;">The Judge</div>
                    <div class="agent-persona">product thinker · last word, always</div>
                </div>
            </div>
            <div class="tag" style="background:{lbl_bg}; color:{lbl_fg}; border:1px solid {lbl_border}; margin-bottom:14px;">
                ✦ {lbl}
            </div>
            <p style="font-family:'Lora',serif; font-size:1rem; color:#d0d0d0; line-height:1.75;
                      font-style:italic; margin:0;">
                "{verdict_text}"
            </p>
        </div>
        <div style="background:#111; border:1px solid #2a2a2a; border-radius:12px;
                    padding:14px 18px; text-align:center; flex-shrink:0; min-width:72px;">
            <div style="font-family:'Lora',serif; font-size:2.4rem; font-weight:700;
                        color:{sc_col}; line-height:1;">{sc}</div>
            <div style="font-size:0.65rem; color:#555;">/&nbsp;10</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

    # — Actions —
    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
    col_dl, col_new, _ = st.columns([1, 1, 2])
    with col_dl:
        st.download_button(
            "⎘  save result",
            data=format_share_text(saved_thought, results),
            file_name="shower-thought.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_new:
        if st.button("↺  new thought", use_container_width=True):
            st.session_state["results"] = None
            st.session_state["thought"] = ""
            st.rerun()


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-top: 4rem; padding-bottom: 1rem;">
    <p style="font-size:0.7rem; color:#333; letter-spacing:0.05em; margin-bottom:4px;">
        your group chat is tired of your ideas.
        <span style="color:#a3e635;">we are not.</span>
    </p>
    <p style="font-size:0.6rem; color:#222; letter-spacing:0.04em; margin:0;">
        not liable for startups, pivots, or 3am github commits this inspires
    </p>
    <p style="font-size:0.6rem; color:#2a2a2a; letter-spacing:0.04em; margin-top:8px;">
        made by <a href="https://aarushsharmaa.github.io/aarush-sharma/" target="_blank"
        style="color:#3a3a3a; text-decoration:none;">aarush sharma</a>
    </p>
</div>
""", unsafe_allow_html=True)
