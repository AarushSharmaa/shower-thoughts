import re


def split_killer_line(text: str) -> tuple:
    """Split agent output into body paragraph and final killer/quotable line."""
    text = text.strip()
    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\u2018\u2019\u201c\u201d])', text)
    if len(sentences) > 1:
        body = " ".join(sentences[:-1]).strip()
        killer = sentences[-1].strip().strip('"').strip("\u201c\u201d")
        return body, killer
    return text, ""


def parse_researcher_bullets(text: str) -> list:
    """Extract bullet points from researcher output."""
    lines = text.strip().splitlines()
    bullets = []
    for line in lines:
        line = line.strip()
        # Match lines starting with -, *, •, or numbers like 1.
        if re.match(r'^[-*•\u2022]|^\d+[.)]\s', line):
            clean = re.sub(r'^[-*•\u2022\d.)\s]+', '', line).strip()
            if clean:
                bullets.append(clean)
        elif line and bullets:
            # continuation of previous bullet
            bullets[-1] += " " + line
    # Fallback: if no bullets found, split by newlines
    if not bullets:
        bullets = [l.strip() for l in lines if l.strip()]
    return bullets


def score_color(score: int) -> str:
    if score <= 3:
        return "#e05555"
    elif score <= 5:
        return "#f5d020"
    elif score <= 7:
        return "#a3e635"
    return "#4ade80"


def label_style(label: str) -> tuple:
    """Return (background, border, text color) for verdict label pill."""
    styles = {
        "Garbage":               ("#1a0404", "#4a1515", "#e05555"),
        "Underrated":            ("#1a1404", "#4a3a00", "#f5d020"),
        "Genuinely Interesting": ("#0d1a04", "#2a4010", "#a3e635"),
        "Might Actually Work":   ("#0a1f0a", "#1a4a1a", "#4ade80"),
    }
    return styles.get(label, styles["Genuinely Interesting"])


def format_share_text(thought: str, results: dict) -> str:
    return (
        f'💭 Shower Thought: "{thought}"\n\n'
        f'🚀 The Optimist:\n{results["optimist"]}\n\n'
        f'💀 The Cynic:\n{results["cynic"]}\n\n'
        f'🔍 The Researcher:\n{results["researcher"]}\n\n'
        f'⚖️ Final Verdict: {results["label"]} — {results["score"]}/10\n'
        f'"{results["verdict"]}"\n\n'
        f'Validated by Shower Thought Validator'
    )
