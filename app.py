from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from dotenv import load_dotenv
import os
import pexpect

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['cwd'] = os.getcwd()
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/execute', methods=['POST'])
@login_required
def execute():
    command = request.json.get('command', '').strip()

    if 'cwd' not in session:
        session['cwd'] = os.getcwd()
    cwd = session['cwd']

    if command.startswith("cd"):
        try:
            parts = command.split()
            new_dir = os.path.expanduser("~") if len(parts) == 1 else os.path.abspath(os.path.join(cwd, parts[1]))
            if os.path.isdir(new_dir):
                session['cwd'] = new_dir
                return jsonify({'output': f"Changed directory to {new_dir}"})
            else:
                return jsonify({'output': f"No such directory: {parts[1]}"})
        except Exception as e:
            return jsonify({'output': f"Error: {str(e)}"})

    simulated_commands = {
        "ls": "file1.txt  file2.txt  documents/",
        "pwd": cwd,
        "whoami": session['username'],
        "mkdir": "Directory created (simulated)",
        "rm": "File removed (simulated)",
        "touch": "File created (simulated)",
        "man": "This is a simulated man page.",
        "clear": ""
    }

    if command in simulated_commands:
        return jsonify({'output': simulated_commands[command]})

    try:
        child = pexpect.spawn(command, cwd=cwd, timeout=5)
        child.expect(pexpect.EOF)
        output = child.before.decode('utf-8').strip()
    except Exception as e:
        output = f"Error: {str(e)}"

    return jsonify({'output': output})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
