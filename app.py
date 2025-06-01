from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import os

# Initialize Flask app
app = Flask(__name__)

# Load secret key from environment variable or use fallback
app.secret_key = os.environ.get("SECRET_KEY", "dev_key_for_local_testing")

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__ = 'users'  # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Home route
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials. Please try again."
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            if User.query.filter_by(username=username).first():
                return "Username already taken."

            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id
            return redirect(url_for('dashboard'))
        return render_template('register.html')
    except Exception as e:
        return f"❌ Internal Server Error: {e}"

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return "✅ Welcome to ShellCoach Dashboard!"

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Debug route to check DB tables
@app.route('/debug-db')
def debug_db():
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        return f"Tables in DB: {tables}"
    except Exception as e:
        return f"❌ DB Error: {e}"

# Run the app locally
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
