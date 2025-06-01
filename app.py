from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import os

app = Flask(__name__)

# Use secure secret key for session handling
app.secret_key = os.environ.get("SECRET_KEY", "dev_key_for_local_testing")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Home route redirects based on session
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Login
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
        else:
            return "❌ Invalid credentials"
    return render_template('login.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "❌ Username already taken"
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        return redirect(url_for('dashboard'))
    return render_template('register.html')

# Protected dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Command explanation endpoint
@app.route('/explain', methods=['POST'])
def explain():
    command = request.json.get('command', '')
    explanations = {
        'cd': 'cd changes the current directory.',
        'mkdir': 'mkdir creates a new directory.',
        'touch': 'touch creates a new empty file.',
        'echo': 'echo prints text to the terminal.',
        'cat': 'cat displays the contents of a file.',
        'man': 'man shows the manual for a command.',
        'pwd': 'pwd prints the current directory.',
        'ls': 'ls lists files and directories.',
        'rm': 'rm removes files or directories.',
        'clear': 'clear clears the terminal screen.',
    }
    return jsonify({'explanation': explanations.get(command.split()[0], 'No explanation available.')})

# Optional debug route
@app.route('/debug-db')
def debug_db():
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        return f"Tables in DB: {tables}"
    except Exception as e:
        return f"❌ DB Error: {e}"

# Local development only: ensure DB is created
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
