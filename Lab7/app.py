from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os
import bcrypt
import re
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq
import requests


load_dotenv('.env.local')

app = Flask(__name__, static_folder='styles', template_folder='.')
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")


app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST", "localhost")
app.config['MYSQL_PORT'] = int(os.getenv("MYSQL_PORT", 3306))
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER", "root")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD", "")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB", "student_db")

mysql = MySQL(app)


def init_gemini():
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=gemini_api_key)
    return genai.GenerativeModel('gemini-2.0-flash')


def init_groq():
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=groq_api_key)


OLLAMA_API_URL = "http://localhost:11434/api/generate"


def get_ollama_response(query):
    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": f"Convert the following natural language query into a SQL query: {query}. Return ONLY the SQL query, with no additional text, explanations, formatting, comments, or markdown. Do not include any thoughts, notes, or errors. If you cannot generate a valid SQL query, return an empty string.",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()

        sql_query = response.json()["response"].strip()

        if not sql_query.startswith("SELECT") and not sql_query.startswith("INSERT") and not sql_query.startswith("UPDATE") and not sql_query.startswith("DELETE"):
            return ""
        return sql_query
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Ollama. Make sure it's running (ollama run deepseek-r1:1.5b)")
    except Exception as e:
        raise Exception(f"Ollama API error: {str(e)}")


def extract_sql_query(text):
    """Extract SQL query from AI response text."""

    sql_block_pattern = re.compile(r"```sql\s*(.*?)\s*```", re.DOTALL)
    code_block_pattern = re.compile(r"```\s*(.*?)\s*```", re.DOTALL)

    sql_match = sql_block_pattern.search(text)
    if sql_match:
        return sql_match.group(1).strip()

    code_match = code_block_pattern.search(text)
    if code_match:
        return code_match.group(1).strip()

    sql_patterns = [

        re.compile(
            r"(?i)(SELECT\s+.*?FROM\s+.*?(?:WHERE|GROUP BY|ORDER BY|LIMIT|;|$).*)", re.DOTALL),
        re.compile(r"(?i)(INSERT\s+INTO\s+.*?VALUES\s+.*?(?:;|$).*)", re.DOTALL),
        re.compile(r"(?i)(UPDATE\s+.*?SET\s+.*?(?:WHERE|;|$).*)", re.DOTALL),
        re.compile(r"(?i)(DELETE\s+FROM\s+.*?(?:WHERE|;|$).*)", re.DOTALL)
    ]

    for pattern in sql_patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

    return text.strip()


try:
    gemini_model = init_gemini()
    groq_client = init_groq()
except Exception as e:
    print(f"Error initializing AI models: {str(e)}")


def process_nlq(query, model="deepseek"):
    """Process natural language query using the specified model."""

    schema_context = """
    Database Schema:
    - users (id INT PRIMARY KEY, username VARCHAR(50), password VARCHAR(255), email VARCHAR(100), fullname VARCHAR(100), created_at TIMESTAMP, updated_at TIMESTAMP)
    - user_details (id INT PRIMARY KEY, user_id INT FOREIGN KEY -> users(id), phone VARCHAR(10), address TEXT, bio TEXT)
    - courses (id INT PRIMARY KEY, course_name VARCHAR(100), course_code VARCHAR(20), description TEXT)
    - grades (id INT PRIMARY KEY, user_id INT FOREIGN KEY -> users(id), course_id INT FOREIGN KEY -> courses(id), grade CHAR(1), marks DECIMAL(5,2), semester VARCHAR(20), created_at TIMESTAMP)
    
    Relationships:
    - Each user has one user_details record (one-to-one)
    - Each user can have multiple grade records (one-to-many)
    - Each grade record belongs to one course (many-to-one)
    - Each course can have multiple grade records (one-to-many)
    
    Example queries:
    1. "Show me all my courses" -> SELECT c.course_code, c.course_name FROM courses c JOIN grades g ON c.id = g.course_id WHERE g.user_id = [current_user_id]
    2. "What's my GPA?" -> SELECT AVG(CASE WHEN g.grade = 'A' THEN 4.0 WHEN g.grade = 'B' THEN 3.0 WHEN g.grade = 'C' THEN 2.0 WHEN g.grade = 'D' THEN 1.0 ELSE 0 END) as GPA FROM grades g WHERE g.user_id = [current_user_id]
    3. "Show students with marks above 80" -> SELECT u.username, c.course_name, g.marks FROM users u JOIN grades g ON u.id = g.user_id JOIN courses c ON g.course_id = c.id WHERE g.marks > 80
    4. "Show my profile details" -> SELECT u.username, u.email, u.fullname, ud.phone, ud.address, ud.bio FROM users u LEFT JOIN user_details ud ON u.id = ud.user_id WHERE u.id = [current_user_id]
    """

    prompt = f"""
    You are an AI assistant that converts natural language queries into SQL queries for a student grade management system.
    
    {schema_context}
    
    Convert the following natural language query into a SQL query that will run on the database described above:
    "{query}"
    
    Important guidelines:
    - Return ONLY the SQL query without any explanation or formatting.
    - The query should be syntactically correct MySQL SQL.
    - For queries about "my" or "me" (the current logged-in user), use the placeholder [current_user_id] in the WHERE clause (exactly as written with the brackets).
    - Always include column names in SELECT statements rather than using SELECT *.
    - Join tables as needed based on the relationships described in the schema.
    - For any queries regarding grades, make sure to include course information by joining with the courses table.
    - Remember to handle NULL values appropriately.
    - Make sure to handle left joins properly when some data might not exist (like user_details).
    """

    try:
        if model == "deepseek":
            payload = {
                "model": "deepseek-r1:1.5b",
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            result = extract_sql_query(response.json()["response"])

        elif model == "gemini":
            response = gemini_model.generate_content(prompt)
            result = extract_sql_query(response.text)

        elif model == "groq":
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an AI assistant that converts natural language to SQL queries for a student database system."},
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",
            )
            result = extract_sql_query(completion.choices[0].message.content)

        else:
            raise ValueError(f"Unsupported model: {model}")

        return result

    except Exception as e:
        raise Exception(f"Error processing with {model}: {str(e)}")


def validate_sql_query(query):
    """Basic validation to ensure the query is safe to execute."""

    dangerous_operations = [
        r"(?i)DROP\s+",
        r"(?i)DELETE\s+",
        r"(?i)UPDATE\s+",
        r"(?i)INSERT\s+",
        r"(?i)ALTER\s+",
        r"(?i)CREATE\s+",
        r"(?i)TRUNCATE\s+",
        r"(?i)GRANT\s+",
        r"(?i)REVOKE\s+",
        r"(?i)COMMIT",
        r"(?i)ROLLBACK",
        r"(?i)INTO\s+OUTFILE",
        r"(?i)INTO\s+DUMPFILE",
        r"(?i)LOAD\s+DATA"
    ]

    if not re.search(r"(?i)^SELECT", query.strip()):
        raise ValueError("Only SELECT queries are allowed")

    for pattern in dangerous_operations:
        if re.search(pattern, query):
            raise ValueError(
                "Potentially dangerous operation detected in query")

    return True


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

    cursor.execute('SELECT password FROM users WHERE id = %s',
                   (session['id'],))
    user = cursor.fetchone()

    if not user or not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})

    hashed_new_password = bcrypt.hashpw(
        new_password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute('UPDATE users SET password = %s WHERE id = %s',
                   (hashed_new_password, session['id']))
    mysql.connection.commit()

    return jsonify({'success': True, 'message': 'Password updated successfully'})


@app.route('/ai')
def ai_page():
    if 'loggedin' not in session:
        return redirect('/')
    return render_template('ai.html')


@app.route('/query', methods=['POST'])
def query():
    if 'loggedin' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json()
    nl_query = data.get('query')
    model = data.get('model', 'deepseek')

    if not nl_query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        print(f"Processing NLQ: {nl_query} using model: {model}")
        sql_query = process_nlq(nl_query, model)
        print(f"Generated SQL query: {sql_query}")

        sql_query = sql_query.replace('[current_user_id]', str(session['id']))

        validate_sql_query(sql_query)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql_query)
        results = cursor.fetchall()

        return jsonify({
            'sql': sql_query,
            'results': results
        })

    except MySQLdb.Error as db_err:
        print(f"MySQL Error: {str(db_err)}")
        return jsonify({'error': f'Database error: {str(db_err)}'}), 500
    except ValueError as e:
        print(f"ValueError: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'error': f'Error processing NLQ: {str(e)}'}), 500


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.clear()
    return redirect('/')


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
