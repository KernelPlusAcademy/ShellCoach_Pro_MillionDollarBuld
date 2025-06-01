
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import subprocess
import openai

# Load environment
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# ========== Models ==========
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# ========== Routes ==========
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "Username already exists"
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

# ========== Core Command Execution ==========
virtual_fs = {
    "/": {
        "type": "dir",
        "children": {}
    }
}
current_dir = {}

def simulate_command(cmd, cwd="/"):
    global virtual_fs
    tokens = cmd.strip().split()
    if not tokens:
        return ""
    base = tokens[0]

    # Simulate top commands
    if base == "mkdir" and len(tokens) == 2:
        name = tokens[1]
        virtual_fs["/"]["children"][name] = {"type": "dir", "children": {}}
        return ""
    elif base == "ls":
        children = virtual_fs["/"]["children"]
        return "\n".join(children.keys())
    elif base == "rm" and len(tokens) == 2:
        name = tokens[1]
        if name in virtual_fs["/"]["children"]:
            del virtual_fs["/"]["children"][name]
        return ""
    elif base == "touch" and len(tokens) == 2:
        name = tokens[1]
        virtual_fs["/"]["children"][name] = {"type": "file"}
        return ""
    elif base == "cd" and len(tokens) == 2:
        # Currently mock — single level only
        if tokens[1] in virtual_fs["/"]["children"]:
            return f"Changed to {tokens[1]}"
        return "No such directory"

    # Fallback
    try:
        return subprocess.getoutput(cmd)
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/execute', methods=['POST'])
def execute():
    if 'user_id' not in session:
        return jsonify({"output": "Unauthorized"}), 401
    try:
        data = request.get_json()
        command = data.get('command')
        output = simulate_command(command)
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"output": f"Execution error: {e}"}), 500

@app.route('/explain', methods=['POST'])
def explain():
    try:
        data = request.get_json()
        command = data.get('command')
        if not command:
            return jsonify({"explanation": "No command provided."})

        prompt = f"Explain the following Linux command to a beginner: {command}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        explanation = response.choices[0].message.content.strip()
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"explanation": "Error generating explanation."})

# ========== Init ==========
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
