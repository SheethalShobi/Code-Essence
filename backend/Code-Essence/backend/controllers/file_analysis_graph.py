# controllers/file_analysis_graph.py
import ast
from langgraph.graph import StateGraph
from langchain_core.prompts import PromptTemplate
from controllers.splitters import split_document
from controllers.redis_cache import save_docs_to_redis, load_docs_from_redis

# Define state
class FileState(dict):
    repo_url: str
    file_path: str
    summary: str | None
    dependencies: list[str]

# ---- Node 1: Summarize file ----
def summarize_file_node(state: FileState):
    repo_url, file_path = state["repo_url"], state["file_path"]

    # 1. Check cache
    cached = load_docs_from_redis(repo_url, f"summary:{file_path}")
    if cached:
        print(f" Cache hit (summary): {file_path}")
        state["summary"] = cached
        return state

    # 2. Fresh summarization
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = split_document(content)
    summary = ""

    prompt = PromptTemplate(
        template="Summarize the following Python code clearly and concisely:\n\n{content}\n\nSummary:",
        input_variables=["content"],
    )

    for c in chunks:
        summary += " " + prompt.format(content=c)

    summary = summary.strip()

    # Save to cache
    save_docs_to_redis(repo_url, f"summary:{file_path}", summary)
    state["summary"] = summary
    return state

# ---- Node 2: Analyze dependencies ----
def analyze_dependencies_node(state: FileState):
    repo_url, file_path = state["repo_url"], state["file_path"]

    # 1. Check cache
    cached = load_docs_from_redis(repo_url, f"deps:{file_path}")
    if cached:
        print(f" Cache hit (deps): {file_path}")
        state["dependencies"] = cached
        return state

    # 2. Parse AST for imports
    deps = []
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                deps.append(node.module)

    # Save to cache
    save_docs_to_redis(repo_url, f"deps:{file_path}", deps)
    state["dependencies"] = deps
    return state

# ---- Build Graph ----
def build_file_analysis_graph():
    graph = StateGraph(FileState)

    # Add nodes
    graph.add_node("summarize_file", summarize_file_node)
    graph.add_node("analyze_dependencies", analyze_dependencies_node)

    # Flow: first summarize → then analyze dependencies
    graph.set_entry_point("summarize_file")
    graph.add_edge("summarize_file", "analyze_dependencies")
    graph.set_finish_point("analyze_dependencies")

    return graph.compile()
