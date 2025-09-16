from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from authlib.integrations.flask_client import OAuth
from summarizer import summarize_repo
from healthchecker import analyze_repo_health as summarize_repo_health
import os
import warnings
from dotenv import load_dotenv
from file_summarizer import summarize_file_content
from push_summary import push_summary_to_repo
import tempfile
import shutil
import subprocess

warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

app = Flask(__name__)

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
        return jsonify({"error": str(e)}), 500


@app.route("/health_check", methods=["POST"])
def health_check():
    data = request.json
    repo_url = data.get("repo_url")
    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400
    try:
        summary = summarize_repo_health(repo_url)
        return jsonify(summary), 200
    except Exception as e:
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
        shutil.rmtree(temp_dir)


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
        shutil.rmtree(temp_dir)


@app.route("/push_summary", methods=["POST"])
def push_summary():
    data = request.json
    repo_url = data.get("repo_url")
    branch = data.get("branch", "main")

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    try:
        push_summary_to_repo(repo_url, branch=branch)
        return jsonify({"message": "Summary pushed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

