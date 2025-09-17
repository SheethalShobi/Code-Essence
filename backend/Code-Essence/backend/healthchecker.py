import os
import tempfile
import shutil
from git import Repo
from summarizer import clone_repo  # use the new clone wrapper

def find_entry_point(path):
    for f in os.listdir(path):
        if f in ["app.py", "main.py", "index.js", "server.js"]:
            return os.path.join(path, f)
    return None

def find_dependency_files(path):
    deps = []
    for f in os.listdir(path):
        if f in ["requirements.txt", "pyproject.toml", "Pipfile", "package.json", "poetry.lock"]:
            deps.append(os.path.join(path, f))
    return deps

def find_readme(path):
    for f in os.listdir(path):
        if f.lower() == "readme.md":
            return os.path.join(path, f)
    return None

def analyze_repo_health(repo_url):
    temp_dir = tempfile.mkdtemp()
    try:
        clone_repo(repo_url, temp_dir)
        projects = {}
        overall_score = 0
        overall_max_score = 0

        # ---- Check root as a project ----
        root_report = []
        root_score = 0
        root_max = 10

        entry_point = find_entry_point(temp_dir)
        if entry_point:
            root_report.append(f"Found entry point: {os.path.basename(entry_point)} → +2")
            root_score += 2

        dep_files = find_dependency_files(temp_dir)
        if dep_files:
            root_report.append(f"Dependency file found: {', '.join(os.path.basename(f) for f in dep_files)} → +2")
            root_score += 2
        else:
            root_report.append("No dependency file found → 0 points")

        if any(f in os.listdir(temp_dir) for f in ["src", "app", "backend", "frontend", "services"]):
            root_report.append("Recognizable folder layout → +2")
            root_score += 2

        if root_report:
            projects["root"] = {
                "details": root_report,
                "score": root_score,
                "max_score": root_max,
                "status": "Healthy project" if entry_point else "Incomplete"
            }
            overall_score += root_score
            overall_max_score += root_max

        # ---- Subproject checks ----
        subprojects = []
        for d in os.listdir(temp_dir):
            folder_path = os.path.join(temp_dir, d)
            if os.path.isdir(folder_path) and not d.startswith("."):
                if find_entry_point(folder_path):
                    subprojects.append(d)

        for proj in subprojects:
            proj_path = os.path.join(temp_dir, proj)
            report = []
            score = 0
            max_score = 10

            entry_point = find_entry_point(proj_path)
            if entry_point:
                report.append(f"Found entry point: {os.path.relpath(entry_point, proj_path)} → +2")
                score += 2

            if any(f in os.listdir(proj_path) for f in ["src", "app", "backend", "frontend", "services"]):
                report.append("Recognizable folder layout → +2")
                score += 2

            dep_files = find_dependency_files(proj_path)
            if dep_files:
                report.append(f"Dependency file found: {', '.join(os.path.basename(f) for f in dep_files)} → +2")
                score += 2
            else:
                report.append("No dependency file found → 0 points")

            status = "Healthy project" if entry_point else "Broken / incomplete"

            projects[proj] = {
                "details": report,
                "score": score,
                "max_score": max_score,
                "status": status
            }
            overall_score += score
            overall_max_score += max_score

        # ---- Root-level bonuses ----
        root_bonus = 0
        root_details = []
        if find_readme(temp_dir):
            root_details.append("README.md found → +2")
            root_bonus += 2
        if os.path.exists(os.path.join(temp_dir, ".github")):
            root_details.append("CI/CD config detected → +2")
            root_bonus += 2

        overall_score += root_bonus
        overall_max_score += 4

        return {
            "overall_repo_score": overall_score,
            "overall_repo_max_score": overall_max_score,
            "projects": projects,
            "root_details": root_details
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
