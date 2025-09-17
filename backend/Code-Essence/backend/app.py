from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from authlib.integrations.flask_client import OAuth
from summarizer import summarize_repo
from healthchecker import analyze_repo_health as summarize_repo_health
import os
import warnings
from dotenv import load_dotenv
from file_summarizer import summarize_file_content
from summarizer import summarize_content as summarize_file_content
from push_summary import push_summary_to_repo
import tempfile
import shutil
import subprocess
from flask_cors import CORS


warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

app = Flask(__name__)
CORS(app)

app.secret_key = os.getenv("SECRET_KEY", "supersecret")  # used for session

oauth = OAuth(app)
github = oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)



@app.route("/summarize_repo", methods=["POST"])
def summarize_repository():
    data = request.json
    repo_url = data.get("repo_url")
    level = data.get("level", "repo")

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400
    if level not in ["repo", "folder", "file"]:
        return jsonify({"error": "level must be 'repo', 'folder', or 'file'"}), 400

    try:
        summaries = summarize_repo(repo_url, level)
        return jsonify(summaries), 200
    except Exception as e:
        print(f"[SERVER ERROR] {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/health_check", methods=["POST"])
def health_check():
    data = request.json
    repo_url = data.get("repo_url")
    print("Health check for repo:", repo_url)  # DEBUG
    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400
    try:
        summary = summarize_repo_health(repo_url)
        print("Health summary:", summary)  # DEBUG
        return jsonify(summary), 200
    except Exception as e:
        print("Error in health_check:", e)  # DEBUG
        return jsonify({"error": str(e)}), 500


@app.route("/summarize_snippet", methods=["POST"])
def summarize_snippet():
    data = request.json
    code = data.get("code")
    language = data.get("language", "py")

    if not code:
        return jsonify({"error": "code is required"}), 400

    try:
        from summarizer import summarize_content
        summary = summarize_content("snippet", code, file_type=language)
        return jsonify({"summary": summary}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/summarize_file", methods=["POST"])
def summarize_file():
    data = request.json
    repo_url = data.get("repo_url")
    file_name = data.get("file_name")

    if not repo_url or not file_name:
        return jsonify({"error": "repo_url and file_name are required"}), 400

    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        file_path = os.path.join(temp_dir, file_name)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        ext = file_name.lower().split('.')[-1] if '.' in file_name else file_name.lower()
        summary = summarize_file_content(file_name, content, file_type=ext)
        return jsonify({"summary": summary}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route("/get_file_structure", methods=["POST"])
def get_file_structure():
    data = request.json
    repo_url = data.get("repo_url")

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True)
        structure = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), temp_dir)
                structure.append(rel_path)
        return jsonify({"files": structure}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route("/push_summary", methods=["POST"])
def push_summary():
    data = request.json
    repo_url = data.get("repo_url")
    branch = data.get("branch", "main")

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    temp_dir = tempfile.mkdtemp()
    try:
        # Clone repo
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True, capture_output=True, text=True)

        # Change working dir to repo
        cwd = os.getcwd()
        os.chdir(temp_dir)

        # Make sure branch exists
        subprocess.run(["git", "checkout", branch], check=True, capture_output=True, text=True)

        # Pull latest changes to avoid non-fast-forward errors
        subprocess.run(["git", "pull", "origin", branch], check=True, capture_output=True, text=True)

        # Commit the summary
        if os.path.exists("SUMMARY.md"):
            subprocess.run(["git", "add", "SUMMARY.md"], check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", "Update SUMMARY.md"], check=True, capture_output=True, text=True)

        # Push changes
        result = subprocess.run(["git", "push", "origin", branch], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({
                "error": "Git push failed",
                "details": result.stderr
            }), 500

        return jsonify({"message": "Summary pushed successfully"}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Git command failed",
            "cmd": e.cmd,
            "output": e.output,
            "stderr": e.stderr
        }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.chdir(cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route("/callback")
def authorize():
    token = github.authorize_access_token()
    resp = github.get("user")
    user = resp.json()
    session["user"] = user
    # redirect to frontend React page with user info
    return redirect(f"http://localhost:3000/profile?username={user['login']}&token={token['access_token']}")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("http://localhost:3000")

@app.route("/dependency_graph", methods=["POST"])
def dependency_graph():
    data = request.json
    repo_url = data.get("repo_url")

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True)

        graph = {"nodes": [], "links": []}
        added_nodes = set()

        def add_node(node_id, group):
            if node_id not in added_nodes:
                graph["nodes"].append({"id": node_id, "group": group})
                added_nodes.add(node_id)

        # Always add root project node
        add_node("project", "root")

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)

                #  Node.js: package.json
                if file.lower() == "package.json":
                    import json
                    with open(file_path, "r", encoding="utf-8") as f:
                        pkg = json.load(f)
                        deps = pkg.get("dependencies", {})
                        dev_deps = pkg.get("devDependencies", {})
                        for dep in {**deps, **dev_deps}.keys():
                            add_node(dep, "node")
                            graph["links"].append({"source": "project", "target": dep})

                #  Python: requirements.txt
                elif file.lower() == "requirements.txt":
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            dep = line.strip().split("==")[0]
                            if dep:
                                add_node(dep, "python")
                                graph["links"].append({"source": "project", "target": dep})

                #  Kubernetes: yaml / yml
                elif file.lower().endswith((".yaml", ".yml")):
                    import yaml
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            docs = list(yaml.safe_load_all(f))
                        for doc in docs:
                            if not isinstance(doc, dict):
                                continue
                            kind = doc.get("kind", "Resource")
                            name = doc.get("metadata", {}).get("name", "unknown")
                            node_id = f"{kind}:{name}"
                            add_node(node_id, "k8s")
                            graph["links"].append({"source": "project", "target": node_id})
                    except Exception:
                        continue

        return jsonify(graph), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

