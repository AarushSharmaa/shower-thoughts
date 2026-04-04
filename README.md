# shower thought validator 🚿

type a shower thought → 4 AI agents argue about it → one judge decides if you're a genius or an idiot.

**[live demo →](https://your-app.streamlit.app)** *(update after deploy)*

## what it does

- **Optimist** argues why your idea is brilliant
- **Cynic** finds the fatal flaw
- **Researcher** searches the web for prior art
- **Judge** scores it 1–10 and delivers a verdict

Built with CrewAI, LiteLLM, and Streamlit.

## run locally

```bash
pip install -r requirements.txt

# optional: add your Groq key for the "on the house" fallback
cp .env.example .env
# edit .env and set GROQ_API_KEY

streamlit run app.py
```

Users can also paste their own key (Groq / OpenAI / Google) directly in the UI.

## deploy to Streamlit Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo + `app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
5. Deploy — done.

> Note: GitHub Pages only serves static files. Streamlit apps need Streamlit Cloud.

## stack

- [CrewAI](https://github.com/crewAIInc/crewAI) — multi-agent orchestration
- [LiteLLM](https://github.com/BerriAI/litellm) — provider routing
- [DuckDuckGo Search](https://github.com/deedy5/duckduckgo_search) — free web search
- [Streamlit](https://streamlit.io) — UI

---

made by [Aarush Sharma](https://aarushsharmaa.github.io/aarush-sharma/)
