from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask_cors import CORS
import os
import pandas as pd
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq
import requests
import re

# Load environment variables
load_dotenv('.env.local')

app = Flask(__name__, static_folder='static', template_folder='.')
CORS(app)

DEFAULT_USER_ID = "default_user"

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


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


try:
    gemini_model = init_gemini()
    groq_client = init_groq()
except Exception as e:
    print(f"Error initializing AI models: {str(e)}")


# Helper function to check allowed file extensions


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to get data file path


def get_data_file_path(user_id):
    return os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}_data.json")

# Helper function to load user data


def load_user_data(user_id):
    file_path = get_data_file_path(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {"expenses": [], "categories": {}}

# Helper function to save user data


def save_user_data(user_id, data):
    file_path = get_data_file_path(user_id)
    with open(file_path, 'w') as f:
        json.dump(data, f)


def get_ollama_response(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "deepseek-coder:6.7b",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        return None


def categorize_expenses(descriptions, gemini_model):
    prompt = f"""
    Categorize the following expenses into common budget categories. 
    Return the results as a Python list of categories in the same order as the input.
    Input expenses: {descriptions}
    """
    try:
        response = gemini_model.generate_content(prompt)
        categories = json.loads(response.text)
        return categories
    except Exception as e:
        print(f"Error categorizing expenses: {e}")
        return ["Uncategorized"] * len(descriptions)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/upload', methods=['POST'])
def upload_file():

    user_id = DEFAULT_USER_ID
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Process the file based on its extension
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Process the dataframe
            processed_data = process_expense_data(df, user_id)

            # Remove the temporary file
            os.remove(file_path)

            return jsonify({"success": True, "message": "File processed successfully", "data": processed_data})

        except Exception as e:
            # Remove the temporary file in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "File type not allowed"}), 400


def process_expense_data(df, user_id):
    # Load existing user data
    user_data = load_user_data(user_id)

    # Map common column names to standardized names
    column_mapping = {
        'date': ['date', 'transaction date', 'trans date', 'transaction_date'],
        'description': ['description', 'transaction description', 'details', 'particulars', 'narration'],
        'amount': ['amount', 'transaction amount', 'debit', 'withdrawal', 'debit amount'],
        'category': ['category', 'transaction category', 'type']
    }

    # Standardize column names
    df.columns = df.columns.str.lower().str.strip()

    # Map columns
    for standard_col, possible_cols in column_mapping.items():
        if standard_col not in df.columns:
            for col in possible_cols:
                if col in df.columns:
                    df.rename(columns={col: standard_col}, inplace=True)
                    break

    # Ensure required columns exist
    required_cols = ['date', 'description', 'amount']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in the file")

    # Convert date to standard format
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    # Ensure amount is numeric and positive (expenses are positive)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').abs()

    # Drop rows with missing values in required columns
    df = df.dropna(subset=required_cols)

    # If category column doesn't exist, add it
    if 'category' not in df.columns:
        df['category'] = 'Uncategorized'

    # Use AI to categorize expenses
    descriptions = df['description'].tolist()
    categories = categorize_expenses(descriptions, gemini_model)
    df['category'] = categories

    # Convert DataFrame to list of dictionaries
    new_expenses = df[['date', 'description',
                       'amount', 'category']].to_dict('records')

    # Add unique IDs to new expenses
    for expense in new_expenses:
        expense['id'] = str(uuid.uuid4())
        expense['amount'] = float(expense['amount'])

    # Add new expenses to existing data
    user_data['expenses'].extend(new_expenses)

    # Update category statistics
    update_category_stats(user_data)

    # Save updated data
    save_user_data(user_id, user_data)

    return {"expenses_added": len(new_expenses), "total_expenses": len(user_data['expenses'])}


def update_category_stats(user_data):
    # Initialize categories dictionary if it doesn't exist
    if 'categories' not in user_data:
        user_data['categories'] = {}

    # Reset category statistics
    user_data['categories'] = {}

    # Group expenses by category and calculate statistics
    for expense in user_data['expenses']:
        category = expense['category']
        amount = expense['amount']

        if category not in user_data['categories']:
            user_data['categories'][category] = {
                'total': 0,
                'count': 0,
                'average': 0,
                'min': float('inf'),
                'max': 0
            }

        # Update statistics
        user_data['categories'][category]['total'] += amount
        user_data['categories'][category]['count'] += 1
        user_data['categories'][category]['min'] = min(
            user_data['categories'][category]['min'], amount)
        user_data['categories'][category]['max'] = max(
            user_data['categories'][category]['max'], amount)
        user_data['categories'][category]['average'] = user_data['categories'][category]['total'] / \
            user_data['categories'][category]['count']


@app.route('/api/expenses', methods=['GET'])
def get_expenses():

    user_id = DEFAULT_USER_ID
    user_data = load_user_data(user_id)

    # Get query parameters for filtering
    category = request.args.get('category')
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    expenses = user_data['expenses']

    # Apply filters
    if category and category != 'All':
        expenses = [e for e in expenses if e['category'] == category]

    if search:
        search = search.lower()
        expenses = [e for e in expenses if search in e['description'].lower()]

    if start_date:
        expenses = [e for e in expenses if e['date'] >= start_date]

    if end_date:
        expenses = [e for e in expenses if e['date'] <= end_date]

    # Sort by date (newest first)
    expenses = sorted(expenses, key=lambda x: x['date'], reverse=True)

    return jsonify({"expenses": expenses})


@app.route('/api/categories', methods=['GET'])
def get_categories():

    user_id = DEFAULT_USER_ID
    user_data = load_user_data(user_id)

    return jsonify({"categories": user_data['categories']})


@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():

    user_id = DEFAULT_USER_ID
    user_data = load_user_data(user_id)

    expenses = user_data['expenses']
    categories = user_data['categories']

    # Calculate summary statistics
    total_expenses = sum(e['amount'] for e in expenses)

    # Get monthly expenses
    monthly_expenses = {}
    for expense in expenses:
        month_year = expense['date'][:7]  # Format: YYYY-MM
        if month_year not in monthly_expenses:
            monthly_expenses[month_year] = 0
        monthly_expenses[month_year] += expense['amount']

    # Calculate average monthly expense
    if monthly_expenses:
        avg_monthly_expense = sum(
            monthly_expenses.values()) / len(monthly_expenses)
    else:
        avg_monthly_expense = 0

    # Find top spending category
    top_category = max(categories.items(), key=lambda x: x[1]['total'])[
        0] if categories else "None"

    # Get category distribution for pie chart
    category_distribution = {category: data['total']
                             for category, data in categories.items()}

    # Get monthly trend data for line chart
    monthly_trend = [{"month": month, "amount": amount}
                     for month, amount in monthly_expenses.items()]
    monthly_trend = sorted(monthly_trend, key=lambda x: x['month'])

    # Get category breakdown for bar chart
    category_breakdown = [{"category": category, "amount": data['total']}
                          for category, data in categories.items()]

    # Detect unusual expenses (more than 2x the category average)
    unusual_expenses = []
    for expense in expenses:
        category = expense['category']
        if category in categories and expense['amount'] > 2 * categories[category]['average']:
            unusual_expenses.append(expense)

    # Get monthly category breakdown for stacked bar chart
    monthly_category_breakdown = {}
    for expense in expenses:
        month_year = expense['date'][:7]  # Format: YYYY-MM
        category = expense['category']

        if month_year not in monthly_category_breakdown:
            monthly_category_breakdown[month_year] = {}

        if category not in monthly_category_breakdown[month_year]:
            monthly_category_breakdown[month_year][category] = 0

        monthly_category_breakdown[month_year][category] += expense['amount']

    # Format data for stacked bar chart
    stacked_bar_data = []
    for month, categories_data in monthly_category_breakdown.items():
        data_point = {"month": month}
        data_point.update(categories_data)
        stacked_bar_data.append(data_point)

    stacked_bar_data = sorted(stacked_bar_data, key=lambda x: x['month'])

    dashboard_data = {
        "summary": {
            "total_expenses": total_expenses,
            "avg_monthly_expense": avg_monthly_expense,
            "top_category": top_category,
            "total_transactions": len(expenses)
        },
        "charts": {
            "category_distribution": category_distribution,
            "monthly_trend": monthly_trend,
            "category_breakdown": category_breakdown,
            "stacked_bar_data": stacked_bar_data
        },
        "unusual_expenses": unusual_expenses
    }

    return jsonify(dashboard_data)


@app.route('/api/update-category', methods=['POST'])
def update_category():

    user_id = DEFAULT_USER_ID
    user_data = load_user_data(user_id)

    data = request.json
    expense_id = data.get('expense_id')
    new_category = data.get('category')

    if not expense_id or not new_category:
        return jsonify({"error": "Missing expense_id or category"}), 400

    # Update the category for the specified expense
    for expense in user_data['expenses']:
        if expense['id'] == expense_id:
            expense['category'] = new_category
            break

    # Update category statistics
    update_category_stats(user_data)

    # Save updated data
    save_user_data(user_id, user_data)

    return jsonify({"success": True, "message": "Category updated successfully"})


@app.route('/api/generate-report', methods=['GET'])
def generate_report():

    user_id = DEFAULT_USER_ID
    user_data = load_user_data(user_id)

    # Get query parameters for filtering
    report_type = request.args.get('type', 'monthly')
    month_year = request.args.get(
        'month_year', datetime.now().strftime('%Y-%m'))

    expenses = user_data['expenses']

    # Filter expenses based on report type
    if report_type == 'monthly':
        filtered_expenses = [
            e for e in expenses if e['date'].startswith(month_year)]
    elif report_type == 'yearly':
        year = month_year.split('-')[0]
        filtered_expenses = [e for e in expenses if e['date'].startswith(year)]
    else:
        return jsonify({"error": "Invalid report type"}), 400

    # Calculate report data
    total_amount = sum(e['amount'] for e in filtered_expenses)

    # Group by category
    category_totals = {}
    for expense in filtered_expenses:
        category = expense['category']
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += expense['amount']

    # Sort categories by total amount (descending)
    sorted_categories = sorted(
        category_totals.items(), key=lambda x: x[1], reverse=True)

    report_data = {
        "report_type": report_type,
        "period": month_year,
        "total_amount": total_amount,
        "total_transactions": len(filtered_expenses),
        "category_breakdown": [{"category": cat, "amount": amt} for cat, amt in sorted_categories],
        "expenses": filtered_expenses
    }

    return jsonify(report_data)


@app.route('/api/ai-insights', methods=['GET'])
def ai_insights():

    user_id = DEFAULT_USER_ID
    user_data = load_user_data(user_id)

    expenses = user_data['expenses']
    categories = user_data['categories']

    # Prepare data for AI analysis
    monthly_expenses = {}
    for expense in expenses:
        month_year = expense['date'][:7]  # Format: YYYY-MM
        if month_year not in monthly_expenses:
            monthly_expenses[month_year] = 0
        monthly_expenses[month_year] += expense['amount']

    # Calculate average monthly expense - this was missing
    if monthly_expenses:
        avg_monthly_expense = sum(
            monthly_expenses.values()) / len(monthly_expenses)
    else:
        avg_monthly_expense = 0

    # Sort monthly expenses by date
    sorted_monthly = sorted(monthly_expenses.items())

    # Calculate month-over-month changes
    mom_changes = []
    for i in range(1, len(sorted_monthly)):
        prev_month, prev_amount = sorted_monthly[i-1]
        curr_month, curr_amount = sorted_monthly[i]
        change_pct = ((curr_amount - prev_amount) / prev_amount) * \
            100 if prev_amount > 0 else 0
        mom_changes.append({
            "prev_month": prev_month,
            "curr_month": curr_month,
            "change_pct": change_pct
        })

    # Identify categories with highest variance
    category_variance = {}
    for category, data in categories.items():
        if data['count'] > 1:
            variance = data['max'] - data['min']
            category_variance[category] = variance

    high_variance_categories = sorted(
        category_variance.items(), key=lambda x: x[1], reverse=True)[:3]

    # Generate insights using Gemini
    insights_prompt = f"""
    Analyze the following expense data and provide 3-5 concise, actionable insights:
    
    Monthly Expenses: {sorted_monthly}
    Month-over-Month Changes: {mom_changes}
    Categories with Highest Variance: {high_variance_categories}
    Category Breakdown: {categories}
    
    Focus on spending patterns, anomalies, and potential areas for saving money.
    Keep each insight to 1-2 sentences maximum.
    Format as a JSON list of strings, with each string being one insight.
    """
    try:
        response = gemini_model.generate_content(insights_prompt)
        insights_text = response.text

        # Extract JSON from response
        insights_match = re.search(r'\[.*\]', insights_text, re.DOTALL)
        if insights_match:
            insights_json = insights_match.group(0)
            insights = json.loads(insights_json)
        else:
            # Fallback if JSON extraction fails
            insights = [
                "Based on your spending patterns, consider setting a budget for categories with high variance.",
                "Review your expenses in the top spending category to identify potential areas for savings.",
                "Monitor month-over-month changes to spot unusual spending patterns early."
            ]
    except Exception as e:
        insights = [
            "An error occurred while generating AI insights. Please try again later.",
            f"Error details: {str(e)}"
        ]

    # Generate savings recommendations using Groq
    savings_prompt = f"""
    Based on the following expense data, provide 3 specific, actionable recommendations for saving money:

    Top Spending Categories: {list(categories.keys())[:5]}
    Monthly Expense Trend: {sorted_monthly[-3:]}
    Categories with Highest Variance: {high_variance_categories}

    Format the recommendations as a JSON list of strings.
    """

    try:
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a helpful financial advisor."},
                {"role": "user", "content": savings_prompt}
            ]
        )
        savings_recommendations = json.loads(
            completion.choices[0].message.content)
    except Exception as e:
        savings_recommendations = [
            "An error occurred while generating savings recommendations. Please try again later.",
            f"Error details: {str(e)}"
        ]

    # Generate budget suggestion using Ollama
    budget_prompt = f"""
    Based on the following expense data, suggest a monthly budget allocation:

    Average Monthly Expense: {avg_monthly_expense}
    Category Breakdown: {categories}

    Provide the budget allocation as a JSON object with category names as keys and suggested budget amounts as values.
    """

    try:
        budget_suggestion = json.loads(get_ollama_response(budget_prompt))
    except Exception as e:
        budget_suggestion = {
            "error": "An error occurred while generating the budget suggestion.",
            "details": str(e)
        }

    # Prepare the final response
    ai_analysis = {
        "insights": insights,
        "savings_recommendations": savings_recommendations,
        "budget_suggestion": budget_suggestion
    }

    return jsonify(ai_analysis)

# Add a new route for receipt tracking


@app.route('/api/upload-receipt', methods=['POST'])
def upload_receipt():

    user_id = DEFAULT_USER_ID
    if 'receipt' not in request.files:
        return jsonify({"error": "No receipt file provided"}), 400

    receipt_file = request.files['receipt']

    if receipt_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if receipt_file and allowed_file(receipt_file.filename):
        filename = secure_filename(receipt_file.filename)
        file_path = os.path.join(
            app.config['UPLOAD_FOLDER'], f"receipt_{user_id}_{filename}")
        receipt_file.save(file_path)

        # Process the receipt using OCR (you'll need to implement this function)
        receipt_data = process_receipt(file_path)

        # Add receipt data to user's expenses
        user_data = load_user_data(user_id)
        user_data['expenses'].append(receipt_data)
        update_category_stats(user_data)
        save_user_data(user_id, user_data)

        # Remove the temporary file
        os.remove(file_path)

        return jsonify({"success": True, "message": "Receipt processed successfully", "data": receipt_data})

    return jsonify({"error": "File type not allowed"}), 400

# Helper function to process receipt using OCR (you'll need to implement this)


def process_receipt(file_path):
    # Implement OCR logic here
    # For now, we'll return a dummy receipt data
    return {
        "id": str(uuid.uuid4()),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "description": "Receipt upload",
        "amount": 0,
        "category": "Uncategorized"
    }


if __name__ == '__main__':
    app.run(debug=True)
