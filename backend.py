from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
import joblib
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with backend


# Load the trained model and columns
model = joblib.load('transaction_model.pkl')
with open('trained_columns.txt', 'r') as f:
    trained_columns = [line.strip() for line in f]

# Connect to SQLite3 database
def connect_to_db():
    conn = sqlite3.connect("transactions.db")
    return conn

# Initialize database tables
def initialize_database():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Transactions (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         payment_currency TEXT NOT NULL,
                         received_currency TEXT NOT NULL,
                         sender_bank_location TEXT NOT NULL,
                         receiver_bank_location TEXT NOT NULL,
                         payment_type TEXT NOT NULL,
                         amount REAL NOT NULL,
                         is_laundering TEXT NOT NULL
                       );""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS CustomerData (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL,
                         address TEXT NOT NULL,
                         email TEXT NOT NULL,
                         phone TEXT NOT NULL
                       );""")
    conn.commit()
    conn.close()

# Insert a new transaction into the database
def insert_transaction(payment_currency, received_currency, sender_bank_location, receiver_bank_location, payment_type, amount):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO Transactions (payment_currency, received_currency, sender_bank_location, receiver_bank_location, payment_type, amount)
                      VALUES (?, ?, ?, ?, ?, ?);""", (
        payment_currency, received_currency, sender_bank_location, receiver_bank_location, payment_type, amount))
    conn.commit()
    conn.close()

# Fetch transactions from the database
def fetch_transactions():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Transactions;")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Prepare input data for prediction
def prepare_input_data(payment_currency, received_currency, sender_bank_location, receiver_bank_location, payment_type, amount):
    try:
        amount = float(amount)
    except ValueError:
        amount = 0.0

    input_data = {
        'Amount': amount,
        'Payment_currency': payment_currency,
        'Received_currency': received_currency,
        'Sender_bank_location': sender_bank_location,
        'Receiver_bank_location': receiver_bank_location,
        'Payment_type': payment_type
    }

    input_df = pd.DataFrame([input_data])
    input_df_encoded = pd.get_dummies(input_df, columns=['Payment_currency', 'Received_currency', 'Sender_bank_location', 'Receiver_bank_location', 'Payment_type'])

    for col in trained_columns:
        if col not in input_df_encoded.columns:
            input_df_encoded[col] = 0

    input_df_encoded = input_df_encoded[trained_columns]
    return input_df_encoded

# Predict laundering using the trained model
def predict_laundering(payment_currency, received_currency, sender_bank_location, receiver_bank_location, payment_type, amount):
    input_df_encoded = prepare_input_data(payment_currency, received_currency, sender_bank_location, receiver_bank_location, payment_type, amount)
    prediction = model.predict(input_df_encoded)
    return "Laundering" if prediction[0] == 1 else "Not Laundering"

# Generate SARS report as a PDF
def generate_sars_report(transaction):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.drawString(30, 750, f"Transaction ID: {transaction[0]}")
    c.drawString(30, 730, f"Payment Currency: {transaction[1]}")
    c.drawString(30, 710, f"Received Currency: {transaction[2]}")
    c.drawString(30, 690, f"Sender Bank Location: {transaction[3]}")
    c.drawString(30, 670, f"Receiver Bank Location: {transaction[4]}")
    c.drawString(30, 650, f"Payment Type: {transaction[5]}")
    c.drawString(30, 630, f"Amount: {transaction[6]}")
    c.showPage()
    c.save()

    buffer.seek(0)
    pdf_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return pdf_base64

# Flask Routes
@app.route('/')
def home():
    return 'Welcome to the Anti-Money Laundering Project API!'

@app.route('/transactions', methods=['GET'])
def get_transactions():
    transactions = fetch_transactions()
    return jsonify(transactions)

@app.route('/predict', methods=['POST'])
def predict_transaction():
    data = request.get_json()

    # Ensure that the required keys are present
    if not all(key in data for key in ['payment_currency', 'received_currency', 'sender_bank_location', 'receiver_bank_location', 'payment_type', 'amount']):
        return jsonify({'error': 'Missing data fields'}), 400

    payment_currency = data['payment_currency']
    received_currency = data['received_currency']
    sender_bank_location = data['sender_bank_location']
    receiver_bank_location = data['receiver_bank_location']
    payment_type = data['payment_type']
    amount = data['amount']

    prediction = predict_laundering(payment_currency, received_currency, sender_bank_location, receiver_bank_location, payment_type, amount)
    return jsonify({'prediction': prediction})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.get_json()

    # Ensure transaction_id is present
    if 'transaction_id' not in data:
        return jsonify({'error': 'transaction_id is required'}), 400

    transaction_id = data['transaction_id']
    transactions = fetch_transactions()
    transaction = next((tx for tx in transactions if tx[0] == transaction_id), None)

    if transaction:
        pdf_base64 = generate_sars_report(transaction)
        return jsonify({'pdf_base64': pdf_base64})
    else:
        return jsonify({'error': 'Transaction not found'}), 404

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
