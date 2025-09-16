import os
import tempfile
import shutil
from git import Repo
from summarizer import summarize_repo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def push_summary_to_repo(repo_url, branch="main", summary_file="SUMMARY.md"):
    temp_dir = tempfile.mkdtemp()
    try:
        # Prepare token-auth URL
        url = repo_url
        if GITHUB_TOKEN and repo_url.startswith("https://github.com"):
            url = repo_url.replace(
                "https://github.com",
                f"https://{GITHUB_TOKEN}@github.com"
            )

        print(f"[INFO] Cloning {repo_url}...")
        repo = Repo.clone_from(url, temp_dir, branch=branch)

        # Generate repo summary
        print("[INFO] Generating repository summary...")
        summary = summarize_repo(repo_url, level="repo").get("repo_summary", "")

        # Write/update the summary file
        summary_path = os.path.join(temp_dir, summary_file)
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("# Repository Summary\n\n")
            f.write(summary)
        print(f"[INFO] Summary written to {summary_file}")

        # Add, commit, and push
        repo.index.add([summary_file])
        repo.index.commit("Add/update repository summary")
        origin = repo.remote(name="origin")
        origin.push()
        print("[INFO] Summary pushed to GitHub successfully!")

    finally:
        shutil.rmtree(temp_dir)

# Example usage
push_summary_to_repo("https://github.com/SheethalShobi/Project")
