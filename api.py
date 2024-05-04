#flask api
import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
import pymongo
import json
from config import config
from functools import wraps
from datetime import datetime as dt
from flask_cors import CORS
import hashlib

api = Flask(__name__)
cors = CORS(api)
api.config['CORS_HEADERS'] = 'Content-Type'
conf = config()

session = []

def connect_to_database():
    try:
        client = MongoClient(conf.mongo_uri)
        return client['db']
    except Exception as e:
        print(f"Error connecting to database ----> {e}\n\n")
        raise e

def login_required(func): # Wrapper to check if the user is in session if required
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            username_hash = request.headers.get('hash')
            if username_hash not in session:
                return jsonify({'message': 'user not in session'}), 401
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error checking if user is in session ----> {e}\n\n")
            return jsonify({'message': 'error checking if user is in session'}), 500
    return wrapper

def checkPassword(username,password) -> bool: # check if the password is correct
    try:
        database = connect_to_database()
        users_collection = database['Usr']
        user = users_collection.find_one({'name': username})
        if not user:
            return False
        
        hashed_password = user['_password']
            
        if f"{password}" == f"{hashed_password}":
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking password ----> {e}\n\n")
        return False

@api.route('/',methods=['GET'])
def ping():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PIARPIS API</title>
    </head>
    <body>

        <h1>PIARPIS API</h1>
        <p>the WSGI is working and the api is available. Hopefully...</p>

        <iframe style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;" src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1&controls=0&mute=0" title="YouTube video player" frameborder="0" allow="autoplay" allowfullscreen></iframe>
    </body>
    </html>
    """
    return html

@api.route('/login', methods=['POST'])
def login(): #Add user to session
    try:
        username = request.json.get('username')
        password = request.json.get('password')
        
        if checkPassword(username,password):
            username_hash = hashlib.sha256((username + dt.now.__str__()).encode()).hexdigest()
            print(f"------------------User {username} logged in as {username_hash}------------------\n\n")
            session.append(username_hash)
            return jsonify({'secretAuth': username_hash}), 200
        else:
            return jsonify({'message': 'login failed'}), 401
    except Exception as e:
        print(f"Error logging in ----> {e}\n\n")
        return jsonify({'message': 'error logging in'}), 500

@api.route('/logout')
@login_required
def logout(): #Remove user from session
    try:
        username_hash = request.headers.get('hash')
        session.pop(username_hash)
        return jsonify({'message': 'logout successful'}), 200
    except Exception as e:
        print(f"Error logging out ----> {e}\n\n")
        return jsonify({'message': 'error logging out'}), 500

@api.route('/insert', methods=['POST'])
@login_required
def addToDB():
    try:
        name = request.json.get('name')
        plate = request.json.get('plate')
        invoice = request.json.get('invoice')
        inicial_time = request.json.get('inicial_time')
        final_time = request.json.get('final_time')

        database = connect_to_database()
        parking_collection = database['Parkings']
        username = len(parking_collection.data) + 1
        print(f"Adding to parking register ----> {username} {name} {plate} {invoice} {inicial_time} {final_time}\n\n")
        parking_collection.insert_one({'Id': username, 'name': name, 'plate': plate, 'invoice': invoice, 'in_time': inicial_time, 'out_time': final_time, 'status': 'active'})
        return jsonify({'message': 'added to parking register'}), 200 #TODO: search a less silly message
    except Exception as e:
        print(f"Error adding to parking register ----> {e}\n\n")
        return jsonify({'message': 'error adding to parking register'}), 500

@api.route('/get', methods=['GET'])
@login_required
def getParkingDB(): # get all the recipes of the user
    try:
        username = request.headers.get('user')

        database = connect_to_database()
        parking_collection = database['Parkings']
        parkings = parking_collection.data
        if len(parkings) == 0:
            return jsonify({'message': 'No parkings found'}), 404
        
        responseList = []
        
        for i, parking in enumerate(parkings):
            if parking['status'] == 'active':
                responseList.append(parking)

        response = jsonify(responseList)
        return response, 200
    except Exception as e:
        print(f"Error getting parkings ----> {e}\n\n")
        return jsonify({'message': 'error getting parkings'}), 500
    
@api.route('/delete', methods=['POST'])
@login_required
def deleteFromDB():
    try:
        id = request.json.get('Id')

        database = connect_to_database()
        parking_collection = database['Parkings']
        username = len(parking_collection.data) + 1
        #set the status to inactive
        parking_collection.update_one({'Id': id}, {'status': 'inactive'})
        #TODO: check with mongo if this is the correct way to update
        return jsonify({'message': 'deleted from parking register'}), 200 #TODO: search a less silly message
    except Exception as e:
        print(f"Error deleting from parking register ----> {e}\n\n")
        return jsonify({'message': 'error deleting from parking register'}), 500

@api.route('/update', methods=['POST'])
@login_required
def updateDB():
    try:
        id = request.json.get('Id')
        new_name = request.json.get('new_name')
        new_plate = request.json.get('new_plate')
        new_inicial_time = request.json.get('new_inicial_time')
        new_final_time = request.json.get('new_final_time')

        database = connect_to_database()
        parking_collection = database['Parkings']
        username = len(parking_collection.data) + 1
        parking_collection.update_one({'Id': id}, {'name': new_name, 'plate': new_plate, 'in_time': new_inicial_time, 'out_time': new_final_time})
        # TODO: check with mongo if this is the correct way to update
        return jsonify({'message': 'updated parking register'}), 200 #TODO: search a less silly message
    except Exception as e:
        print(f"Error updating parking register ----> {e}\n\n")
        return jsonify({'message': 'error updating parking register'}), 500

if __name__ == '__main__':
    api.run(debug=True, host='0.0.0.0', port=6970)

'''
curl -X POST https://02loveslollipop.pythonanywhere.com/login -H "Content-Type: application/json" -d '{"username": "admin@piarpis.com", "password": "admin"}'

curl -X GET https://02loveslollipop.pythonanywhere.com/logout -H "hash:<replace with the hash from the login response>" #printed in the console when the user logs in

curl -X POST https://02loveslollipop.pythonanywhere.com/insert -H "Content-Type: application/json" -H "hash: <replace with the hash from the login response>" -d '{"Id": "7", "name": "test", "plate": "test", "invoice": "test", "inicial_time": "test", "final_time": "test"}'

curl -X GET https://02loveslollipop.pythonanywhere.com/get -H "hash: <replace with the hash from the login response>"
'''
