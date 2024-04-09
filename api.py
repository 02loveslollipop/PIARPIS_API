#flask api
import requests
from flask import Flask, request, jsonify
from mongo import MongoClient
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
    client = MongoClient(conf.mongo_uri)
    return client['db']

def login_required(func): # Wrapper to check if the user is in session if required
    @wraps(func)
    def wrapper(*args, **kwargs):
        username_hash = request.headers.get('hash')
        if username_hash not in session:
            return jsonify({'message': 'user not in session'}), 401
        return func(*args, **kwargs)
    return wrapper

def checkPassword(username,password) -> bool: # check if the password is correct
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
    username = request.json.get('username')
    password = request.json.get('password')
    
    if checkPassword(username,password):
        username_hash = hashlib.sha256((username + dt.now.__str__()).encode()).hexdigest()
        session.append(username_hash)
        return jsonify({'secretAuth': username_hash}), 200
    else:
        return jsonify({'message': 'login failed'}), 401

@api.route('/logout')
@login_required
def logout(): #Remove user from session
    username_hash = request.headers.get('hash')
    session.pop(username_hash)
    return jsonify({'message': 'logout successful'}), 200

@api.route('/insert', methods=['POST'])
@login_required
def addToDB():
    username = request.json.get('Id')
    name = request.json.get('name')
    plate = request.json.get('plate')
    invoice = request.json.get('invoice')
    inicial_time = request.json.get('inicial_time')

    database = connect_to_database()
    parking_collection = database['Parkings']
    parking_collection.insert_one({'Id': username, 'name': name, 'plate': plate, 'invoice': invoice, 'inicial_time': inicial_time})
    return jsonify({'message': 'added to parking register'}), 200 #TODO: search a less silly message

@api.route('/get', methods=['GET'])
@login_required
def getParkingDB(): # get all the recipes of the user
    username = request.headers.get('user')

    database = connect_to_database()
    parking_collection = database['Parkings']
    parkings = parking_collection.data
    if len(parkings) == 0:
        return jsonify({'message': 'No parkings found'}), 404
    
    response = jsonify(parkings)
    return response, 200 
if __name__ == '__main__':
    api.run(debug=True, host='0.0.0.0', port=6970)
    
'''
curl -X POST http://localhost:6970/login -H "Content-Type: application/json" -d '{"username": "admin", "password": "admin"}'

curl -X GET http://localhost:6970/logout -H "hash:<replace with the hash from the login response>" #printed in the console when the user logs in

curl -X POST http://localhost:6970/insert_to_db -H "Content-Type: application/json, hash: <replace with the hash from the login response>" -d '{"Id": "1", "name": "test", "plate": "test", "invoice": "test", "inicial_time": "test"}'

curl -X GET http://localhost:6970/get_parkings_db -H "hash: <replace with the hash from the login response>"
'''
