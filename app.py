import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
# import mysql.connector  # Not needed, using pymysql instead
# ...existing code...
from datetime import datetime
import pymysql

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management

# --- Signup Route ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        # Check if username already exists
        c.execute('SELECT * FROM users WHERE username=%s', (username,))
        user = c.fetchone()
        if user:
            flash('Username already exists! Please choose another.')
            return render_template('signup.html')
        # Insert new user
        c.execute('INSERT INTO users (username, password, name) VALUES (%s, %s, %s)', (username, password, name))
        conn.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

# ...existing code...

# MySQL connection config
MYSQL_CONFIG = {
   'user': 'root',
    'password': 'Abhi@1289',
    'host': 'localhost',
    'database': 'support_opp',
    'port': 3000,
    'autocommit': True
}



def get_db():
    conn = pymysql.connect(
        host=MYSQL_CONFIG['host'],
        user=MYSQL_CONFIG['user'],
        password=MYSQL_CONFIG['password'],
        database=MYSQL_CONFIG['database'],
        port=MYSQL_CONFIG['port'],
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor  # <-- Add this line
    )
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Add 'name' column to users table for signup
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        module VARCHAR(100),
        description TEXT,
        status VARCHAR(20) DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100),
        status VARCHAR(20),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_articles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        issue_id INT,
        author VARCHAR(100),
        title VARCHAR(255),
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(issue_id) REFERENCES issues(id)
    )''')
    conn.commit()
    conn.close()


# Initialize DB before the first request using Flask's event system
@app.before_request
def setup():
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True

@app.route('/')
def index():
    if 'username' in session:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM issues ORDER BY created_at DESC')
        issues = c.fetchall()
        return render_template('index.html', username=session['username'], issues=issues)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=%s', (username,))
        user = c.fetchone()
        if user and user['password'] == password:
            session['username'] = username
            c.execute('INSERT INTO logins (username, status) VALUES (%s, %s)', (username, 'success'))
            conn.commit()
            # ...existing code...
            return redirect(url_for('index'))
        else:
            c.execute('INSERT INTO logins (username, status) VALUES (%s, %s)', (username, 'failed'))
            conn.commit()
            # ...existing code...
            flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/report', methods=['GET', 'POST'])
def report_issue():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        module = request.form['module']
        description = request.form['description']
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username=%s', (session['username'],))
        user = c.fetchone()
        user_id = user['id'] if user else None
        c.execute('INSERT INTO issues (user_id, module, description) VALUES (%s, %s, %s)', (user_id, module, description))
        conn.commit()
        # ...existing code...
        flash('Issue reported!')
        return redirect(url_for('index'))
    return render_template('report_issue.html')

@app.route('/issues')
def issues():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM issues ORDER BY created_at DESC')
    issues = c.fetchall()
    return render_template('index.html', username=session['username'], issues=issues)

@app.route('/restart_server')
def restart_server():
    # ...existing code...
    flash('Server restart simulated. Check logs for details.')
    return redirect(url_for('index'))

@app.route('/close_issue/<int:issue_id>', methods=['POST'])
def close_issue(issue_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'UPDATE issues SET status=%s, closed_at=NOW() WHERE id=%s',
        ('closed', issue_id)
    )
    conn.commit()
    # Redirect to knowledge article creation page after closing the issue
    flash('Issue closed successfully. Please create a knowledge article about the resolution.')
    return redirect(url_for('create_knowledge_article', issue_id=issue_id))

@app.route('/knowledge_article/<int:issue_id>', methods=['GET', 'POST'])
def create_knowledge_article(issue_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    # Fetch issue details for context
    c.execute('SELECT * FROM issues WHERE id=%s', (issue_id,))
    issue = c.fetchone()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['username']
        c.execute(
            'INSERT INTO knowledge_articles (issue_id, author, title, content) VALUES (%s, %s, %s, %s)',
            (issue_id, author, title, content)
        )
        conn.commit()
        flash('Knowledge article created successfully.')
        return redirect(url_for('index'))
    return render_template('create_knowledge_article.html', issue=issue)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)

