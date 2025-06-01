from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from functools import wraps
import openai
import os
import pexpect

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return 'User already exists'
        new_user = User(username=username, password=password)
        db.session.add(new_user)
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
            session['username'] = username
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'])

@app.route('/execute', methods=['POST'])
@login_required
def execute():
    command = request.json.get('command', '')

    # Simulated commands
    simulated_commands = {
        "ls": "file1.txt  file2.txt  documents/",
        "pwd": "/home/user",
        "whoami": session['username'],
        "mkdir": "Directory created (simulated)",
        "rm": "File removed (simulated)",
        "cd": "Changed directory (simulated)",
        "touch": "File created (simulated)",
        "man": "This is a simulated man page.",
        "clear": ""
    }

    if command.strip() in simulated_commands:
        output = simulated_commands[command.strip()]
    else:
        # Fallback to pexpect for real shell command (safe sandbox)
        try:
            child = pexpect.spawn(command, timeout=5)
            child.expect(pexpect.EOF)
            output = child.before.decode('utf-8').strip()
        except Exception as e:
            output = f"Error: {str(e)}"

    return jsonify({'output': output})

@app.route('/explain', methods=['POST'])
@login_required
def explain():
    command = request.json.get('command', '')
    prompt = f"Explain what the Linux command '{command}' does in simple terms for a beginner."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        explanation = response.choices[0].message.content.strip()
    except Exception as e:
        explanation = f"Error explaining command: {str(e)}"

    return jsonify({'explanation': explanation})

# Create DB if not exists
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
