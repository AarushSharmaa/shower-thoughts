from crewai.tools import BaseTool
from duckduckgo_search import DDGS


class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = (
        "Search the web to find whether an idea already exists, has been tried before, "
        "succeeded, or failed. Use this to find real-world precedents and facts."
    )

    def _run(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No results found for this query."
            lines = []
            for r in results:
                lines.append(f"- {r['title']}: {r['body']} (source: {r['href']})")
            return "\n".join(lines)
        except Exception as e:
            return f"Search failed: {str(e)}. Report what you know from training data instead."
