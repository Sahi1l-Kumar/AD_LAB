from flask import Flask, render_template, request, redirect, session, jsonify, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv('.env.local')

app = Flask(__name__, static_folder='styles', template_folder='.')
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# MySQL configuration for localhost:3306
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST", "localhost")
app.config['MYSQL_PORT'] = int(os.getenv("MYSQL_PORT", 3306))
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER", "root")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD", "")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB", "student_grading")

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()

        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            session['email'] = user.get('email', '')

            if request.content_type == 'application/json':
                return jsonify({'success': True, 'redirect': '/grades'})
            return redirect('/grades')
        else:
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'message': 'Incorrect username/password'})
            return "Incorrect username/password"

    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Signup route modification
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = request.get_json()
            username = data.get('username')
            fullname = data.get('fullname')
            email = data.get('email')
            password = data.get('password')
        else:
            username = request.form.get('username')
            fullname = request.form.get('fullname')
            email = request.form.get('email')
            password = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            return jsonify({'success': False, 'message': 'Account already exists!'})

        if not fullname or not email or not username or not password:
            return jsonify({'success': False, 'message': 'Please fill in all fields!'})

        # Updated SQL query to include `fullname`
        cursor.execute('INSERT INTO users (username, fullname, email, password) VALUES (%s, %s, %s, %s)',
                       (username, fullname, email, password))
        mysql.connection.commit()

        return jsonify({'success': True, 'redirect': '/login'})
    return render_template('index.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'loggedin' not in session:
        return redirect('/login')

    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = request.get_json()
            email = data.get('email')
            full_name = data.get('full_name')
        else:
            email = request.form.get('email')
            full_name = request.form.get('full_name')

        cursor = mysql.connection.cursor()
        cursor.execute(
            'UPDATE users SET email = %s WHERE username = %s', (email, session['username']))
        mysql.connection.commit()

        session['email'] = email

        if request.content_type == 'application/json':
            return jsonify({'success': True, 'message': 'Profile updated successfully!'})
        return redirect('/profile')

    return render_template('profile.html', username=session['username'], email=session.get('email', ''))


@app.route('/reset_password', methods=['POST'])
def reset_password():
    if 'loggedin' not in session:
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': 'Please log in first!'})
        return redirect('/login')

    if request.content_type == 'application/json':
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
    else:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

    # Verify current password
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s',
                   (session['username'], current_password))
    user = cursor.fetchone()

    if not user:
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': 'Current password is incorrect!'})
        return "Current password is incorrect!"

    # Update password
    cursor.execute('UPDATE users SET password = %s WHERE username = %s',
                   (new_password, session['username']))
    mysql.connection.commit()

    if request.content_type == 'application/json':
        return jsonify({'success': True, 'message': 'Password updated successfully!'})
    return redirect('/profile')


@app.route('/grades')
def grades():
    if 'loggedin' not in session:
        return redirect('/login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM grades WHERE username = %s',
                   (session['username'],))
    grades = cursor.fetchall()

    return render_template('grades.html', grades=grades, username=session['username'])


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
