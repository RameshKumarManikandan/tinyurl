from flask import Flask, request, jsonify, redirect, render_template_string, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_session import Session
import string, random, re

app = Flask(__name__)

# ===========================
# SESSION + SECURITY SETTINGS
# ===========================
app.config['SECRET_KEY'] = 'asirvad_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
bcrypt = Bcrypt(app)


# ===========================
# DATABASE CONFIG (YOUR VALUES)
# ===========================
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'asirvad_url_db'
app.config['MYSQL_PORT'] = 3301

mysql = MySQL(app)


# ===========================
# URL VALIDATION REGEX
# ===========================
URL_REGEX = re.compile(
    r'^(https?:\/\/)'
    r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})'
    r'(\/[A-Za-z0-9._~:/?#[\]@!$&\'()*+,;=-]*)?$'
)


# ===========================
# SHORT CODE GENERATOR
# ===========================
def generate_short_code(length=6):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


# ======================================================
# 1️⃣ MAIN PAGE — GLASSMORPHISM UI
# ======================================================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Asirvad URL Shortener</title>

  <style>
    body {
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(135deg, #e8ecf2, #d2d6dd);
        height: 100vh;
        padding: 0; margin: 0;
        display: flex; align-items: center; justify-content: center;
    }
    .glass-card {
        width: 90%; max-width: 600px;
        background: rgba(255, 255, 255, 0.28);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 35px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.18);
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    img.logo {
        width: 100%; border-radius: 15px; margin-bottom: 25px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.20);
    }
    input {
        width: 85%; padding: 14px; border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.5);
        background: rgba(255,255,255,0.3);
        font-size: 16px; margin-bottom: 15px;
    }
    button {
        background: #c40000;
        color: white; border: none;
        padding: 14px 30px;
        border-radius: 12px; cursor: pointer;
        font-size: 17px; font-weight: bold;
        transition: 0.25s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    }
    button:hover { background: #900000; transform: scale(1.03); }
    a { color: #005eff; text-decoration: none; font-weight: bold; }
    .error { color: #ff0000; margin-top: 10px; }
  </style>
</head>

<body>
  <div class="glass-card">
    <img src="/static/logo.png" class="logo">

    <h2>Asirvad Short URL Generator</h2>

    {% if username %}
      <p>Welcome <b>{{username}}</b> | <a href="/logout">Logout</a></p>
    {% else %}
      <p><a href="/login">Login</a></p>
    {% endif %}

    <form method="POST" action="/shorten">
      <input type="text" name="long_url" placeholder="Paste your long URL here..." required>
      <br>
      <button type="submit">Generate Short URL</button>
    </form>

    {% if error %}
      <p class="error">{{ error }}</p>
    {% endif %}

    {% if short_url %}
      <p><b>Your Short URL:</b><br>
      <a href="{{short_url}}" target="_blank">{{short_url}}</a>
      </p>
    {% endif %}
  </div>
</body>
</html>
"""


# ======================================================
# 2️⃣ USER LOGIN — GLASSMORPHISM UI
# ======================================================
USER_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>User Login</title>

  <style>
    body {
        font-family: 'Segoe UI';
        background: linear-gradient(135deg, #eceff4, #cbd2df);
        height: 100vh; margin: 0;
        display: flex; justify-content: center; align-items: center;
    }
    .glass-card {
        width: 90%; max-width: 420px;
        background: rgba(255,255,255,0.3);
        padding: 35px; border-radius: 20px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        text-align: center;
    }
    img.logo { width: 100%; border-radius: 15px; margin-bottom: 25px; }
    input {
        width: 80%; padding: 14px;
        border-radius: 12px; border: 1px solid rgba(255,255,255,0.5);
        background: rgba(255,255,255,0.4);
        margin-bottom: 15px;
        font-size: 16px;
    }
    button {
        background: #c40000; color: white;
        padding: 12px 30px; border-radius: 12px; border: none;
        font-size: 17px; cursor: pointer; transition: .2s;
    }
    button:hover { background: #900000; transform: scale(1.05); }
  </style>
</head>

<body>
  <div class="glass-card">
    <img src="/static/logo.png" class="logo">
    <h2>User Login</h2>

    <form method="POST">
      <input type="text" name="username" placeholder="Username" required>
      <br>
      <input type="password" name="password" placeholder="Password" required>
      <br><br>
      <button type="submit">Login</button>
    </form>

  </div>
</body>
</html>
"""


# ======================================================
# 3️⃣ ADMIN LOGIN — GLASSMORPHISM UI
# ======================================================
ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Admin Login</title>

  <style>
    body {
        font-family: 'Segoe UI';
        background: linear-gradient(135deg, #e8ecf2, #bfc6d1);
        height: 100vh; margin: 0;
        display: flex; justify-content: center; align-items: center;
    }
    .glass-card {
        width: 90%; max-width: 420px; padding: 35px;
        background: rgba(255,255,255,0.3);
        backdrop-filter: blur(15px);
        border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        text-align: center;
    }
    img.logo { width: 100%; border-radius: 15px; margin-bottom: 25px; }
    input {
        width: 80%; padding: 14px;
        background: rgba(255,255,255,0.4);
        border-radius: 12px; border: 1px solid rgba(255,255,255,0.5);
        margin-bottom: 15px; 
        font-size: 16px;
    }
    button {
        background: #c40000; color: white;
        padding: 12px 30px; border-radius: 12px; border: none;
        font-size: 17px; cursor: pointer; transition: 0.2s;
    }
    button:hover { background: #900000; transform: scale(1.05); }
  </style>
</head>

<body>
  <div class="glass-card">
    <img src="/static/logo.png" class="logo">
    <h2>Admin Login</h2>

    <form method="POST">
      <input type="text" name="username" placeholder="Admin Username" required><br>
      <input type="password" name="password" placeholder="Password" required><br><br>
      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html>
"""


ADMIN_USER_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Create User</title>

  <style>
    body {
        font-family: 'Segoe UI';
        background: linear-gradient(135deg, #dfe3ea, #c4ccd9);
        height: 100vh; margin: 0;
        display: flex; justify-content: center; align-items: center;
    }
    .glass-card {
        width: 90%; max-width: 450px; padding: 35px;
        background: rgba(255,255,255,0.3);
        border-radius: 20px; backdrop-filter: blur(15px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        text-align: center;
    }
    img.logo { width: 100%; border-radius: 15px; margin-bottom: 25px; }
    input, select {
        width: 85%; padding: 14px;
        background: rgba(255,255,255,0.4);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.5);
        margin-bottom: 15px;
        font-size: 16px;
    }
    button {
        background: #c40000; color: white;
        padding: 12px 30px; border-radius: 12px;
        border: none; cursor: pointer;
        font-size: 17px;
    }
    button:hover { background: #900000; transform: scale(1.05); }
    a { color: #005eff; text-decoration:none; font-weight:bold; }
  </style>
</head>

<body>
  <div class="glass-card">
    <img src="/static/logo.png" class="logo">
    <h2>Create User</h2>

    <p>Admin: <b>{{admin}}</b> | <a href="/admin/logout">Logout</a></p>

    <form method="POST">
      <input type="text" name="username" placeholder="New Username" required><br>
      <input type="password" name="password" placeholder="Password" required><br>

      <select name="role" required>
        <option value="user">Normal User</option>
        <option value="admin">Admin</option>
      </select><br>

      <button type="submit">Create User</button>
    </form>
  </div>
</body>
</html>
"""

# ======================================================
# ROUTES — ADMIN LOGIN
# ======================================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return ADMIN_LOGIN_HTML

    username = request.form['username'].strip()
    password = request.form['password']

    print("=== DEBUG: Admin Login Attempt ===")
    print("Username entered:", username)
    print("Password entered:", password)

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, password, role FROM users WHERE username=%s", (username,))
    admin = cur.fetchone()
    cur.close()

    print("DB Returned:", admin)

    if not admin:
        print("DEBUG: No admin user found with this username")
        return "❌ Invalid Admin Credentials"

    # Extract values
    db_id = admin[0]
    db_username = admin[1]
    db_password_hash = admin[2]
    db_role = admin[3]

    print("DB Username:", db_username)
    print("DB Role:", db_role)
    print("DB Password Hash:", db_password_hash)

    # Check role
    if db_role != 'admin':
        print("DEBUG: User exists but role is not admin")
        return "❌ Not an Admin Account"

    # Check password hash
    password_ok = bcrypt.check_password_hash(db_password_hash, password)
    print("Password Match:", password_ok)

    if password_ok:
        print("DEBUG: ADMIN LOGIN SUCCESS")
        session['admin'] = True
        session['admin_username'] = username
        return redirect('/admin/users')

    print("DEBUG: Password mismatch")
    return "❌ Invalid Admin Credentials"

# ======================================================
# ROUTE — ADMIN CREATE USERS
# ======================================================

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if 'admin' not in session:
        return redirect('/admin/login')

    if request.method == 'GET':
        return render_template_string(ADMIN_USER_PAGE, admin=session['admin_username'])

    username = request.form['username']
    password = request.form['password']
    role = request.form['role']  # NEW LINE

    hashed = bcrypt.generate_password_hash(password).decode('utf-8')

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed, role)
        )
        mysql.connection.commit()
    except:
        return "❌ Username already exists"
    finally:
        cur.close()

    return "✅ User Created Successfully! <a href='/admin/users'>Back</a>"


# ======================================================
# USER LOGIN
# ======================================================
@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'GET':
        return USER_LOGIN_HTML

    username = request.form['username']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password FROM users WHERE username=%s AND role='user'", (username,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.check_password_hash(user[1], password):
        session['user_id'] = user[0]
        session['username'] = username
        return redirect('/')

    return "❌ Wrong username or password"


@app.route('/logout')
def user_logout():
    session.clear()
    return redirect('/login')


# ======================================================
# MAIN PAGE
# ======================================================
@app.route('/')
def index():
    return render_template_string(HTML_PAGE, username=session.get('username'))


# ======================================================
# SHORTEN URL
# ======================================================
@app.route('/shorten', methods=['POST'])
def shorten_url():
    if 'user_id' not in session:
        return "❌ Please login first"

    long_url = request.form['long_url']

    if not URL_REGEX.match(long_url):
        return render_template_string(HTML_PAGE, error="Invalid URL format", username=session.get('username'))

    short_code = generate_short_code()

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO urls (long_url, short_code, user_id) VALUES (%s, %s, %s)",
        (long_url, short_code, session['user_id'])
    )
    mysql.connection.commit()
    cur.close()

    return render_template_string(
        HTML_PAGE,
        short_url=request.host_url + short_code,
        username=session.get('username')
    )

ADMIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Admin Dashboard - Asirvad</title>

  <style>
    body {
        font-family: 'Segoe UI';
        background: linear-gradient(135deg, #dfe3ea, #c4ccd9);
        height: 100vh; margin: 0; padding: 30px;
    }

    .glass-card {
        max-width: 900px; margin: auto;
        background: rgba(255,255,255,0.3);
        padding: 30px; border-radius: 20px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }

    h2 { text-align: center; margin-bottom: 20px; }

    table {
        width: 100%; border-collapse: collapse;
        background: rgba(255,255,255,0.4);
        border-radius: 12px; overflow: hidden;
    }

    th, td {
        padding: 14px; border-bottom: 1px solid rgba(0,0,0,0.1);
        text-align: center;
    }

    th {
        background: rgba(255,255,255,0.6);
        font-weight: bold;
    }

    .top-bar {
        display: flex; justify-content: space-between;
        margin-bottom: 20px; font-size: 18px;
    }

    a.btn {
        padding: 10px 20px;
        background: #c40000; color: white;
        border-radius: 10px; text-decoration: none;
        transition: 0.2s;
    }
    a.btn:hover { background: #900000; }
  </style>
</head>

<body>

  <div class="glass-card">
    <div class="top-bar">
      <span>Admin: <b>{{admin}}</b></span>
      <span>
        <a class="btn" href="/admin/users">Create User</a>
        <a class="btn" href="/admin/logout">Logout</a>
      </span>
    </div>

    <h2>User Management Dashboard</h2>

    <table>
      <tr>
        <th>ID</th>
        <th>Username</th>
        <th>Role</th>
        <th>Created At</th>
      </tr>

      {% for u in users %}
      <tr>
        <td>{{u[0]}}</td>
        <td>{{u[1]}}</td>
        <td>{{u[3]}}</td>
        <td>{{u[2]}}</td>
      </tr>
      {% endfor %}
    </table>

  </div>

</body>
</html>
"""
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin/login')

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, created_at, role FROM users ORDER BY id DESC")
    users = cur.fetchall()
    cur.close()

    return render_template_string(ADMIN_DASHBOARD_HTML, users=users, admin=session['admin_username'])
GATEWAY_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Asirvad Access Portal</title>

  <style>
    body {
        font-family: 'Segoe UI';
        background: linear-gradient(135deg, #dde2e8, #c7ccd6);
        height: 100vh; margin: 0;
        display: flex; justify-content: center; align-items: center;
    }

    .glass-card {
        width: 90%; max-width: 500px;
        background: rgba(255,255,255,0.28);
        padding: 40px; border-radius: 20px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.20);
        text-align: center;
    }

    img.logo {
        width: 100%; border-radius: 15px; margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .btn {
        display: block;
        width: 80%;
        margin: 12px auto;
        padding: 14px;
        background: #c40000;
        color: white;
        text-decoration: none;
        font-size: 18px;
        border-radius: 12px;
        transition: 0.2s;
    }

    .btn:hover { background: #900000; transform: scale(1.05); }

    h2 { margin-bottom: 15px; }
  </style>
</head>

<body>
  <div class="glass-card">
    <img src="/static/logo.png" class="logo">

    <h2>Asirvad Login Gateway</h2>

    <a class="btn" href="/login">User Login</a>
    <a class="btn" href="/admin/login">Admin Login</a>

    {% if admin %}
      <a class="btn" href="/admin/dashboard">Admin Dashboard</a>
      <a class="btn" href="/admin/users">Create User</a>
    {% endif %}

    {% if username %}
      <a class="btn" href="/">User URL Shortener</a>
    {% endif %}
  </div>
</body>
</html>
"""
@app.route('/home')
def home():
    return render_template_string(
        GATEWAY_HTML,
        admin=session.get('admin'),
        username=session.get('username')
    )

# ======================================================
# REDIRECT SHORT CODE
# ======================================================
@app.route('/<short_code>')
def redirect_short_url(short_code):
    cur = mysql.connection.cursor()
    cur.execute("SELECT long_url FROM urls WHERE short_code=%s", (short_code,))
    result = cur.fetchone()
    cur.close()

    if result:
        return redirect(result[0])

    return "❌ Invalid or expired URL"

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "username and password required"}), 400

    username = data['username']
    password = data['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password FROM users WHERE username=%s AND role='user'", (username,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.check_password_hash(user[1], password):
        session['user_id'] = user[0]
        session['username'] = username
        return jsonify({"message": "login success", "username": username}), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/shorten', methods=['POST'])
def api_shorten():
    if 'user_id' not in session:
        return jsonify({"error": "Login required"}), 401

    data = request.get_json()
    if not data or 'long_url' not in data:
        return jsonify({"error": "long_url required"}), 400

    long_url = data['long_url']

    if not URL_REGEX.match(long_url):
        return jsonify({"error": "Invalid URL format"}), 400

    short_code = generate_short_code()

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO urls (long_url, short_code, user_id) VALUES (%s, %s, %s)",
        (long_url, short_code, session['user_id'])
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({
        "long_url": long_url,
        "short_url": request.host_url + short_code,
        "short_code": short_code
    }), 200
@app.route('/api/list', methods=['GET'])
def api_list():
    if 'user_id' not in session:
        return jsonify({"error": "Login required"}), 401

    uid = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT long_url, short_code FROM urls WHERE user_id=%s ORDER BY id DESC", (uid,))
    rows = cur.fetchall()
    cur.close()

    output = []
    for r in rows:
        output.append({
            "long_url": r[0],
            "short_url": request.host_url + r[1]
        })

    return jsonify({"urls": output})



# ======================================================
# RUN APPLICATION
# ======================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
