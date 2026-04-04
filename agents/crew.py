import os
import json
import re

from crewai import Agent, Task, Crew, Process, LLM
from agents.tools import WebSearchTool
from prompts import (
    OPTIMIST_BACKSTORY,
    CYNIC_BACKSTORY,
    RESEARCHER_BACKSTORY,
    JUDGE_BACKSTORY,
)


def build_llm(provider: str, api_key: str) -> LLM:
    if provider == "groq":
        return LLM(model="groq/llama-3.3-70b-versatile", api_key=api_key)
    elif provider == "openai":
        return LLM(model="gpt-4o-mini", api_key=api_key)
    elif provider == "google":
        return LLM(model="gemini/gemini-2.0-flash", api_key=api_key)
    raise ValueError(f"Unknown provider: {provider}")


def parse_verdict(raw: str) -> dict:
    """Parse judge JSON output with a fallback."""
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {
        "score": 5,
        "label": "Genuinely Interesting",
        "verdict": raw.strip()[:300],
    }


def run_crew(thought: str, provider: str, api_key: str = "") -> dict:
    # Fall back to server-side Groq key if none provided
    if not api_key and provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY", "")
    llm = build_llm(provider, api_key)
    search_tool = WebSearchTool()

    optimist = Agent(
        role="The Optimist",
        goal="Argue the strongest possible case for why this idea is brilliant",
        backstory=OPTIMIST_BACKSTORY,
        llm=llm,
        verbose=False,
    )
    cynic = Agent(
        role="The Cynic",
        goal="Find and articulate the fatal flaw in this idea",
        backstory=CYNIC_BACKSTORY,
        llm=llm,
        verbose=False,
    )
    researcher = Agent(
        role="The Researcher",
        goal="Find factual evidence of whether this idea exists or has been tried",
        backstory=RESEARCHER_BACKSTORY,
        llm=llm,
        tools=[search_tool],
        verbose=False,
    )
    judge = Agent(
        role="The Judge",
        goal="Deliver the final verdict as a JSON object",
        backstory=JUDGE_BACKSTORY,
        llm=llm,
        verbose=False,
    )

    task_opt = Task(
        description=(
            f'Argue the strongest case FOR this shower thought: "{thought}"\n'
            "Write 3-4 punchy sentences. End with one killer, standalone quotable line."
        ),
        expected_output="3-4 sentences arguing for the idea, ending with a killer quotable line.",
        agent=optimist,
        async_execution=True,
    )
    task_cyn = Task(
        description=(
            f'Dismantle this shower thought: "{thought}"\n'
            "Find the fatal flaw. Write 3-4 punchy sentences. End with one devastating quotable line."
        ),
        expected_output="3-4 sentences dismantling the idea, ending with a devastating quotable line.",
        agent=cynic,
        async_execution=True,
    )
    task_res = Task(
        description=(
            f'Research this idea using your web search tool: "{thought}"\n'
            "Does it already exist? Has it been tried? Did it work? "
            "Output 3-5 bullet points of factual findings. Cite sources where possible."
        ),
        expected_output="3-5 bullet points of factual research with sources.",
        agent=researcher,
        async_execution=True,
    )
    task_judge = Task(
        description=(
            f'The shower thought being judged: "{thought}"\n\n'
            "You have heard from the Optimist, the Cynic, and the Researcher. "
            "Synthesize their arguments and deliver your verdict.\n\n"
            "Output ONLY this JSON and nothing else:\n"
            '{"score": <integer 1-10>, '
            '"label": <"Garbage" | "Underrated" | "Genuinely Interesting" | "Might Actually Work">, '
            '"verdict": "<2 sharp, opinionated sentences>"}'
        ),
        expected_output='Valid JSON: {"score": int, "label": str, "verdict": str}',
        agent=judge,
        context=[task_opt, task_cyn, task_res],
    )

    crew = Crew(
        agents=[optimist, cynic, researcher, judge],
        tasks=[task_opt, task_cyn, task_res, task_judge],
        process=Process.sequential,
        verbose=False,
    )

    crew.kickoff()

    verdict = parse_verdict(task_judge.output.raw)

    return {
        "optimist": task_opt.output.raw.strip(),
        "cynic": task_cyn.output.raw.strip(),
        "researcher": task_res.output.raw.strip(),
        "score": verdict.get("score", 5),
        "label": verdict.get("label", "Genuinely Interesting"),
        "verdict": verdict.get("verdict", ""),
    }
