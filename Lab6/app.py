from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os
import bcrypt
from dotenv import load_dotenv


load_dotenv('.env.local')

app = Flask(__name__, static_folder='styles', template_folder='.')
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")


app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST", "localhost")
app.config['MYSQL_PORT'] = int(os.getenv("MYSQL_PORT", 3306))
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER", "root")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD", "")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB", "student_db")

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        session['loggedin'] = True
        session['id'] = user['id']
        session['username'] = user['username']

        return jsonify({'success': True, 'redirect': '/grades'})

    return jsonify({'success': False, 'message': 'Incorrect username or password'})


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    fullname = data.get('fullname')
    email = data.get('email')
    password = data.get('password')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    account = cursor.fetchone()

    if account:
        return jsonify({'success': False, 'message': 'Account already exists!'})

    if not fullname or not email or not username or not password:
        return jsonify({'success': False, 'message': 'Please fill in all fields!'})

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute('INSERT INTO users (username, fullname, email, password) VALUES (%s, %s, %s, %s)',
                   (username, fullname, email, hashed_password))
    mysql.connection.commit()

    return jsonify({'success': True, 'redirect': '/'})


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'loggedin' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        data = request.get_json()
        fullname = data.get('fullname')
        email = data.get('email')
        phone = data.get('phone')
        address = data.get('address')
        bio = data.get('bio')

        cursor.execute('''
            UPDATE users 
            SET fullname = %s, email = %s 
            WHERE id = %s
        ''', (fullname, email, session['id']))

        cursor.execute(
            "SELECT id FROM user_details WHERE user_id = %s", (session['id'],))
        existing_entry = cursor.fetchone()

        if existing_entry:

            cursor.execute('''
                UPDATE user_details 
                SET phone = %s, address = %s, bio = %s 
                WHERE user_id = %s
            ''', (phone, address, bio, session['id']))
        else:

            cursor.execute('''
                INSERT INTO user_details (user_id, phone, address, bio) 
                VALUES (%s, %s, %s, %s)
            ''', (session['id'], phone, address, bio))

        mysql.connection.commit()

        cursor.execute('''
            SELECT u.username, u.fullname, u.email, d.phone, d.address, d.bio 
            FROM users u
            LEFT JOIN user_details d ON u.id = d.user_id
            WHERE u.id = %s
        ''', (session['id'],))
        user = cursor.fetchone()

        return jsonify(user)

    cursor.execute('''
        SELECT u.username, u.fullname, u.email, d.phone, d.address, d.bio 
        FROM users u
        LEFT JOIN user_details d ON u.id = d.user_id
        WHERE u.id = %s
    ''', (session['id'],))
    user = cursor.fetchone()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(user)

    return render_template('profile.html', user=user)


@app.route('/grades')
def grades():
    if 'loggedin' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT c.course_code, c.course_name, g.grade, g.marks, g.semester
        FROM grades g
        JOIN courses c ON g.course_id = c.id
        WHERE g.user_id = %s
    ''', (session['id'],))
    grades = cursor.fetchall()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(grades)

    return render_template('grades.html')


@app.route('/reset_password', methods=['POST'])
def reset_password():
    if 'loggedin' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch stored hashed password
    cursor.execute('SELECT password FROM users WHERE id = %s',
                   (session['id'],))
    user = cursor.fetchone()

    if not user or not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})

    # Hash the new password
    hashed_new_password = bcrypt.hashpw(
        new_password.encode('utf-8'), bcrypt.gensalt())

    # Update password in DB
    cursor.execute('UPDATE users SET password = %s WHERE id = %s',
                   (hashed_new_password, session['id']))
    mysql.connection.commit()

    return jsonify({'success': True, 'message': 'Password updated successfully'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
