from pymongo import MongoClient
import os
import bcrypt
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        self.db = self.client['flightapp']
        self.predictions_collection = self.db['predictions']
        self.distances_collection = self.db['distances']
        self.users_collection = self.db['users']

    def get_distance(self, origin, destination):
        try:
            distance_record = self.distances_collection.find_one({'ORIGIN': origin, 'DEST': destination})
            if distance_record:
                return distance_record['DISTANCE IN MILES']
            return None
        except Exception as e:
            print(f"Error retrieving distance: {e}")
            return None

    def save_prediction(self, user_id, date, month, day, origin, destination, carrier, distance, crs_dep_time, crs_arr_time_value, prediction):
        try:
            distance = int(distance) if distance is not None else None
            crs_dep_time = str(crs_dep_time)
            crs_arr_time_value = str(crs_arr_time_value)
            prediction = str(prediction)
            
            self.predictions_collection.insert_one({
                'user_id': user_id,
                'date': date,
                'month': month,
                'day': day,
                'origin': origin,
                'destination': destination,
                'carrier': carrier,
                'distance': distance,
                'crs_dep_time': crs_dep_time,
                'crs_arr_time': crs_arr_time_value,
                'prediction': prediction
            })
            print("Prediction saved successfully.")
        except Exception as e:
            print(f"Error saving prediction: {e}")
            

    def find_user_by_email(self, email):
        return self.users_collection.find_one({'email': email})

    def register_user(self, first_name, email, password):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.users_collection.insert_one({
            'first_name': first_name,
            'email': email,
            'password': hashed,
            'attempts': 0,
            'last_attempt': None
        })

    def check_password(self, stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

    def is_locked(self, user):
        if user['attempts'] >= 3:
            last_attempt = user.get('last_attempt')
            if last_attempt:
                unlock_time = last_attempt + timedelta(seconds=5)
                if datetime.now() < unlock_time:
                    return True
        self.users_collection.update_one({'_id': user['_id']}, {'$set': {'attempts': 0}})
        return False