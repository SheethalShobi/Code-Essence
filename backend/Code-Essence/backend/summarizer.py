import os
import shutil
import tempfile
from dotenv import load_dotenv
from git import Repo
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_aws import ChatBedrock
import boto3

load_dotenv()
# Load GitHub token from env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# AWS Bedrock client
bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
llm = ChatBedrock(
    client=bedrock_client,
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0"
)

splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

# File prompts
FILE_PROMPTS = {
    "dockerfile": "Summarize Dockerfile: base image, steps, ports, CMD.",
    "yaml": "Summarize Kubernetes manifest: deployments, services, ports.",
    "yml": "Summarize Kubernetes manifest: deployments, services, ports.",
    "requirements.txt": "Summarize Python dependencies and their purpose.",
    "package.json": "Summarize Node.js project: dependencies, scripts, metadata.",
    "readme.md": "Summarize the project purpose, features, and usage.",
    "sql": "Summarize SQL schema and queries.",
    "js": "Summarize JavaScript file: functions, components, and usage.",
    "py": "Summarize Python file: functions, classes, and logic.",
    "json": "Summarize JSON content and structure."
}

IGNORE_DIRS = {".git", ".github", "__pycache__", "node_modules", ".venv", "venv"}
IGNORE_FILES = {".gitignore", ".gitattributes", "LICENSE"}
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".sql", ".yaml", ".yml",
    "dockerfile", "requirements.txt", "readme.md"
}

REPO_PROMPT = """
    You are a senior software engineer. Explain the functionality of the code to a junior developer.
    {docs}
    Describe in 5 sentences, max 400 words, focusing on functionality, tech stack, tools, frameworks.
    Explain everything in detail but in a crisp and concise way.
    Output a clean summary **without newline (\n), tab (\t), or extra spaces**.  
    Format as: - Key points separated by periods. - No code blocks, no JSON.
"""

def clone_repo(repo_url, dest_dir):
    """Clone a GitHub repo using token authentication"""
    url = repo_url
    if GITHUB_TOKEN and repo_url.startswith("https://github.com"):
        url = repo_url.replace(
            "https://github.com",
            f"https://{GITHUB_TOKEN}@github.com"
        )
    Repo.clone_from(url, dest_dir)

def should_ignore_file(file_name):
    return file_name.lower() not in ALLOWED_EXTENSIONS and not any(
        file_name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS
    )

def summarize_content(file_name, content, file_type):
    prompt = FILE_PROMPTS.get(file_type.lower(), "Summarize source code file briefly.")
    try:
        full_prompt = f"""
        You are a senior engineer. Summarize this {file_type} file for documentation.
        
        File: {file_name}
        Instructions: {prompt}
        
        Code/content:
        {content[:4000]}  # truncate if huge
        """

        response = llm.invoke(full_prompt)  # direct Bedrock call
        if hasattr(response, "content"):
            return response.content.strip()
        elif isinstance(response, str):
            return response.strip()
        else:
            return str(response)

    except Exception as e:
        print(f"[ERROR] Summarization failed for {file_name}: {e}")
        return f"[FAILED SUMMARY] {file_name}"


def summarize_repo(repo_url, level="repo"):
    temp_dir = tempfile.mkdtemp()
    summaries = {}
    try:
        print(f"[INFO] Cloning repository: {repo_url}")
        clone_repo(repo_url, temp_dir)
        print(f"[INFO] Repository cloned into {temp_dir}")

        for root, dirs, files in os.walk(temp_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            folder_summary = {}
            for file in files:
                if file in IGNORE_FILES or should_ignore_file(file):
                    continue
                file_path = os.path.join(root, file)
                ext = file.lower().split('.')[-1] if '.' in file else file.lower()
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"[INFO] Summarizing {file} ({ext})...")
                    summary = summarize_content(file, content, file_type=ext)
                    if level == "file":
                        summaries[file_path.replace(temp_dir+'/', '')] = str(summary)
                    elif level == "folder":
                        folder_summary[file] = str(summary)
                except Exception as e:
                    print(f"[WARN] Skipping {file_path}: {e}")
                    continue
            if level == "folder" and folder_summary:
                folder_name = root.replace(temp_dir+'/', '')
                summaries[folder_name] = folder_summary

        if level == "repo":
            all_content = ""
            for root, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    if file in IGNORE_FILES or should_ignore_file(file):
                        continue
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            all_content += f.read() + "\n"
                    except Exception:
                        continue
            print("[INFO] Summarizing entire repository...")
            summaries["repo_summary"] = summarize_content("entire_repo", all_content, "source")

        return {
            "repo_url": repo_url,
            "level": level,
            "summaries": summaries
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        
