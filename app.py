import os
import subprocess
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import openai

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Store shell output history
terminal_history = []

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

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
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    explanation = ""
    output = ""
    show_explanation = request.form.get("show_explanation") == "on"

    if request.method == 'POST':
        command = request.form['command']
        username = session.get("username")

        # Built-in supported commands
        supported_commands = ["ls", "pwd", "whoami", "cd", "mkdir", "rm", "man", "echo", "cat", "touch", "date", "clear"]
        shell_output = ""

        if command.split()[0] in supported_commands:
            try:
                shell_output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                shell_output = e.output
        else:
            shell_output = f"Command '{command}' is not supported in this terminal."

        if show_explanation:
            try:
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful Linux assistant."},
                        {"role": "user", "content": f"Explain the command: {command}"}
                    ]
                )
                explanation = response.choices[0].message.content
            except Exception as e:
                explanation = f"Error fetching explanation: {str(e)}"

        terminal_history.append((f"{username}@shell:~$ {command}", shell_output, explanation))

    return render_template("dashboard.html", terminal_history=terminal_history)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
