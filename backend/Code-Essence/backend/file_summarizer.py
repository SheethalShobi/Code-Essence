from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

# Prompts per file type
FILE_PROMPTS = {
    "dockerfile": "Summarize Dockerfile: base image, steps, ports, CMD.",
    "yaml": "Summarize Kubernetes manifest: deployments, services, ports.",
    "yml": "Summarize Kubernetes manifest: deployments, services, ports.",
    "requirements.txt": "Summarize Python dependencies and their purpose.",
    "readme.md": "Summarize the project purpose, features, and usage.",
    "sql": "Summarize SQL schema and queries.",
    "js": "Summarize JavaScript file: functions, components, and usage.",
    "py": "Summarize Python file: functions, classes, and logic.",
}

REPO_PROMPT = """
You are a senior software engineer. Explain the functionality of the code to a junior developer.
{docs}
Describe in 2-3 sentences, max 150 words, focusing on functionality, tech stack, tools, frameworks.
"""

def summarize_file_content(llm, file_name: str, content: str, file_type: str):
    """
    Summarizes a single file content using LangChain + Bedrock.
    """
    prompt = FILE_PROMPTS.get(file_type.lower(), "Summarize source code file briefly.")
    docs = splitter.create_documents([f"{REPO_PROMPT}\n\n{content}"])
    chain = load_summarize_chain(llm, chain_type="map_reduce")
    result = chain.invoke(docs)
    if isinstance(result, dict) and "output_text" in result:
        return result["output_text"]
    return str(result)
