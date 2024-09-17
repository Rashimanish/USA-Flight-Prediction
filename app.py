from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime , timedelta
import pandas as pd
from prediction import feature_engineering_classification, feature_engineering_mcl
from database import Database
import joblib

app = Flask(__name__)
app.secret_key = 'rash123'

db = Database()

# Load classification and mcl models
classification_model = joblib.load('model/classification_model.pkl')
mcl_model = joblib.load('model/mcl_model.pkl')

def is_locked(user):
    if user['attempts'] >= 3:
        last_attempt = user.get('last_attempt')
        if last_attempt:
            unlock_time = last_attempt + timedelta(minutes=5)  
            if datetime.now() < unlock_time:
                flash(f"Account locked. Try again after {unlock_time.strftime('%H:%M:%S')}.", 'error')
                return True
    return False

def validate_user_input(date_str, origin, destination, carrier, crs_dep_time, crs_arr_time):
    # Validate date format
    try:
        flight_date = datetime.strptime(date_str, '%Y-%m-%d')
        month = flight_date.month
        day_of_month = flight_date.day
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'error')
        return False, None

    # Validate origin and destination codes
    valid_airports = {"ATL", "CLT", "DEN", "DFW", "EWR", "IAH", "JFK", "LAS", "LAX", "MCO", "MIA", "ORD", "PHX", "SEA", "SFO"}
    if origin not in valid_airports or destination not in valid_airports:
        flash('Invalid airport code.', 'error')
        return False, None

    # Validate carrier codes
    valid_carriers = {"DL", "AA", "UA", "SW", "AS"}
    if carrier not in valid_carriers:
        flash('Invalid carrier code.', 'error')
        return False, None

    # Validate time formats
    try:
        datetime.strptime(crs_dep_time, '%H:%M')
        datetime.strptime(crs_arr_time, '%H:%M')
    except ValueError:
        flash('Invalid time format. Use HH:MM.', 'error')
        return False, None

    return True, (flight_date, month, day_of_month)

def convert_user_input(flight_date, month, day_of_month, origin, destination, carrier, crs_dep_time, crs_arr_time):
    crs_dep_time_formatted = crs_dep_time.replace(':', '')
    crs_arr_time_formatted = crs_arr_time.replace(':', '')
    origin_carrier = f"{carrier}"
    data = {
        'MONTH': month,
        'DAY_OF_MONTH': day_of_month,
        'FL_DATE': flight_date.strftime('%Y-%m-%d'),
        'ORIGIN': origin,
        'DEST': destination,
        'DISTANCE': None,
        'ORIGIN_CARRIER': origin_carrier,
        'CRS_DEP_TIME': crs_dep_time_formatted,
        'CRS_ARR_TIME': crs_arr_time_formatted
    }
    return data

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form['first_name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('index'))

    if db.find_user_by_email(email):
        flash('Email already exists!', 'error')
        return redirect(url_for('index'))
    
    db.register_user(first_name, email, password)
    flash('Registration successful!', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    user = db.find_user_by_email(email)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('index'))

    if db.is_locked(user):
        flash('Account locked due to too many failed login attempts. Try again later.', 'error')
        return redirect(url_for('index'))

    if db.check_password(user['password'], password):
        session['user_id'] = str(user['_id'])
        flash('Login successful!', 'success')
        return redirect(url_for('predict'))
    else:
        db.users_collection.update_one(
            {"_id": user['_id']},
            {"$inc": {"attempts": 1}, "$set": {"last_attempt": datetime.now()}}
        )
        flash('Incorrect credentials!', 'error')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/predict', methods=['GET'])
def form():
    return render_template('predictionform.html')

@app.route('/predict', methods=['POST'])
def predict():
    user_id = session['user_id']
    
    # Get the form data entered by the user
    date_str = request.form['Date']
    origin = request.form['Origin']
    destination = request.form['Destination']
    carrier = request.form['Carrier']
    crs_dep_time = request.form['CRS_DEP_TIME']
    crs_arr_time = request.form['CRS_ARR_TIME']

    # Validate and convert input data
    is_valid, result = validate_user_input(date_str, origin, destination, carrier, crs_dep_time, crs_arr_time)
    if not is_valid:
        return redirect(url_for('index'))
    
    flight_date, month, day_of_month = result

    # Convert inputs
    flight_data = convert_user_input(flight_date, month, day_of_month, origin, destination, carrier, crs_dep_time, crs_arr_time)
    
    # Get distance from MongoDB 
    distance = db.get_distance(origin, destination)
    if distance is None:
        flash('Distance information not found for the given route.', 'error')
        return redirect(url_for('index'))

    flight_data['DISTANCE'] = distance

    # Convert flight_data dictionary to DataFrame
    flight_data_df = pd.DataFrame([flight_data])
    flight_data_dfm = pd.DataFrame([flight_data])

    crs_arr_time_value = flight_data_df['CRS_ARR_TIME'].values[0]

    # feature engineering for classification model
    classification_data = feature_engineering_classification(flight_data_df)

    # Predict delay using the classification model
    prediction_delayed = classification_model.predict(classification_data)[0]

    #  predict the delay duration using the mcl model
    if prediction_delayed == 1:
    
        flight_data_for_mcl = flight_data_dfm.drop(columns=['CRS_ARR_TIME'], errors='ignore')

        # Perform feature engineering for mcl model
        mcl_data = feature_engineering_mcl(flight_data_for_mcl)

        # Predict delay duration
        delay_time = mcl_model.predict(mcl_data)[0]

        def classify(num):
            if num == 1:
                return "Your flight is likely to be delayed by less than 15 minutes."
            elif num == 2:
                return "Your flight is likely to be delayed by around 20 minutes."
            elif num == 3:
                return "Your flight is likely to be delayed by around 1 hour."
            elif num == 4:
                return "Your flight is likely to be delayed by around 2 hours."
            elif num == 5:
                return "Your flight is likely to be delayed by around 3 hours."
            elif num == 6:
                return "Your flight is likely to be delayed by around 4 hours."
            else:
                return "Your flight is likely to be delayed by more than 5 hours."

        prediction = classify(delay_time)
    else:
        prediction = "Your flight is likely to be on time."

    # Save the prediction data to MongoDB
    db.save_prediction(user_id, date_str, month, day_of_month, origin, destination, carrier, distance, flight_data_df['CRS_DEP_TIME'].values[0], crs_arr_time_value, prediction)

    # Display the prediction result on the result page
    return render_template('result.html', prediction=prediction)

@app.route('/result')
def result():
    return render_template('result.html')
    

@app.route('/history')
def history():
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to be logged in to view your prediction history.', 'error')
        return redirect(url_for('index'))
    predictions = db.predictions_collection.find({'user_id': user_id}, 
                                                 {'_id': 0, 'date': 1, 'origin': 1, 'destination': 1, 'crs_dep_time': 1, 'crs_arr_time': 1, 'prediction': 1})
    predictions_list = list(predictions)
    
    return render_template('history.html', predictions=predictions_list)

@app.route('/travel')
def travel():
    return render_template('travel.html')

if __name__ == '__main__':
    app.run(debug=True)


























































































































'''
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'rash123'

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')
db = client['flightapp']
users_collection = db['users']

# Helper functions
def find_user_by_email(email):
    return users_collection.find_one({'email': email})

def register_user(first_name, email, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({
        'first_name': first_name,
        'email': email,
        'password': hashed,
        'attempts': 0,
        'last_attempt': None
    })

def check_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

def is_locked(user):
    if user['attempts'] >= 3:
        last_attempt = user.get('last_attempt')
        if last_attempt:
            unlock_time = last_attempt + timedelta(seconds=5)
            if datetime.now() < unlock_time:
                return True
        users_collection.update_one({'_id': user['_id']}, {'$set': {'attempts': 0}})
    return False

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form['first_name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('index'))

    if find_user_by_email(email):
        flash('Email already exists!', 'error')
        return redirect(url_for('index'))
    
    register_user(first_name, email, password)
    flash('Registration successful!', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    user = find_user_by_email(email)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('index'))

    if is_locked(user):
        flash('Account locked due to too many failed login attempts. Try again later.', 'error')
        return redirect(url_for('index'))

    if check_password(user['password'], password):
        session['user_id'] = str(user['_id'])
        flash('Login successful!', 'success')
        return redirect(url_for('predict'))
    else:
        users_collection.update_one(
            {"_id": user['_id']},
            {"$inc": {"attempts": 1}, "$set": {"last_attempt": datetime.now()}}
        )
        flash('Incorrect password!', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/predict', methods=['GET'])
def form():
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('predictionform.html') #, min_date=today_date

@app.route('/predict')
def predict():
    return render_template('predictionform.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/travel')
def travel():
    return render_template('travel.html')

@app.route('/result')
def result():
    return render_template('result.html')

if __name__ == '__main__':
    app.run(debug=True)


            # Classify the delay into categories and generate a human-readable prediction result
        def classify(num):
            if num <= 15:
                return "Your flight is likely to be delayed by less than 15 minutes."
            elif num <= 20:
                return "Your flight is likely to be delayed by around 20 minutes."
            elif num <= 60:
                return "Your flight is likely to be delayed by around 1 hour."
            elif num <= 120:
                return "Your flight is likely to be delayed by around 2 hours."
            elif num <= 180:
                return "Your flight is likely to be delayed by around 3 hours."
            elif num <= 240:
                return "Your flight is likely to be delayed by around 4 hours."
            else:
                return "Your flight is likely to be delayed by more than 5 hours."
'''






