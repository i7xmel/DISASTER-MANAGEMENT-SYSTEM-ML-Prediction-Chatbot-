from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify 
import requests
import json
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedShuffleSplit
from flask_cors import CORS 
import random
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.neural_network import MLPRegressor
from joblib import dump, load
from datetime import datetime, timedelta

from sklearn.ensemble import RandomForestClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score





import os
if os.path.exists("risk_model.pkl"):
    os.remove("risk_model.pkl")
    print("Old model deleted. Retraining new model...")



app = Flask(__name__)
json_header = 'application/JSON'
api_header = 'application/x-www-form-urlencoded'

def updating_matching(req_id, don_id):
    token = request.cookies.get('JWT')
    pledges = requests.get(
        'http://localhost:5000/api/v1/get_pledges',
        headers={
            'x-auth-token': token
        }
    )
    pledges = json.loads(pledges.text)['pledges']

    res = requests.get(
        'http://localhost:5000/api/v1/donor',
        headers={
            'x-auth-token': token
        }
    )

    donation_requests = json.loads(res.text)['requests']
    req_request = None
    for don_request in donation_requests:
        if int(don_request['id']) == int(req_id):
            don_request['item_quantities'] = don_request['item_quantities'].split(
                '|')
            don_request['item_quantities'] = [
                tuple(item_quan.split(':')) for item_quan in don_request['item_quantities']]
            don_request['item_quantities'] = dict(don_request['item_quantities'])
            req_request = don_request
        
    req_pledge = None    
    for pledge in pledges:
        if int(pledge['id']) == int(don_id):
            pledge['item_quantities'] = pledge['item_quantities'].split(
                '|')
            pledge['item_quantities'] = [
                tuple(item_quan.split(':')) for item_quan in pledge['item_quantities']]
            try:
                pledge['item_quantities'] = dict(
                    pledge['item_quantities'])
            except Exception as e:
                continue
            req_pledge = pledge

    print('Request Data: ', req_request)
    print('Pledge Data: ', req_pledge)
    don_request = req_request
    pledge = req_pledge
    
    updated = False
    for item in don_request['item_quantities']:
        if (item in pledge['item_quantities']) and (int(pledge['item_quantities'][item]) > 0) and (int(don_request['item_quantities'][item]) > 0):
            updated = True
            don_amount = int(don_request['item_quantities'][item])
            pledge_amount = int(pledge['item_quantities'][item])

            don_request['item_quantities'][item] = str(
                don_amount - pledge_amount)

            pledge['item_quantities'][item] = str(
                pledge_amount - don_amount)
    if updated:
        new_pledge_item_quan = []
        for item in pledge['item_quantities']:
            if int(pledge['item_quantities'][item]) > 0:
                new_pledge_item_quan.append(
                    item+":"+pledge['item_quantities'][item])
        new_pledge_item_quan = '|'.join(new_pledge_item_quan)
        data_payload = {
            'id': pledge['id'],
            'item_quantities': new_pledge_item_quan
        }
        res = requests.post(
            'http://localhost:5000/api/v1/update_pledge',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )

        new_donation_item_quan = []
        for item in don_request['item_quantities']:
            if int(don_request['item_quantities'][item]) > 0:
                new_donation_item_quan.append(
                    item+":"+don_request['item_quantities'][item])
        new_donation_item_quan = '|'.join(new_donation_item_quan)

        data_payload = {
            'event_name': don_request['event_name'],
            'donor_email': request.cookies.get('Email'),
            'recipient_email': don_request['email'],
            'items': new_donation_item_quan
        }
        res = requests.post(
            'http://localhost:5000/api/v1/make_donation',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )

@app.route('/match/<req_id>/<don_id>', methods=['GET', 'POST'])
def match(req_id, don_id):
    updating_matching(req_id, don_id)
    response = make_response(redirect('/manual_matching'))
    return response

@app.route('/manual_matching', methods=['GET', 'POST'])
def manual_matching():
    if request.method == 'GET':
        token = request.cookies.get('JWT')
        res = requests.get(
            'http://localhost:5000/api/v1/donor',
            headers={
                'x-auth-token': token
            }
        )

        pledges = requests.get(
            'http://localhost:5000/api/v1/get_pledges',
            headers={
                'x-auth-token': token
            }
        )
        pledges = json.loads(pledges.text)['pledges']
        parsed_pledges = []
        for pledge in pledges:
            if pledge['item_quantities'] != '':
                pledge['raw_item_quantities'] = pledge['item_quantities']
                pledge['item_quantities'] = pledge['item_quantities'].split('|')
                pledge['item_quantities'] = [
                    item_quan.split(':') for item_quan in pledge['item_quantities'] if int(item_quan.split(':')[1]) > 0]
                parsed_pledges.append(pledge)

        message = json.loads(res.text)['message']
        if message == "Welcome to Donor Page!":
            name = request.cookies.get('Name')
            donation_requests = json.loads(res.text)['requests']
            parsed_requests = []
            for don_request in donation_requests:
                if don_request['item_quantities'] != '':
                    don_request['raw_item_quantities'] = don_request['item_quantities']
                    don_request['item_quantities'] = don_request['item_quantities'].split(
                        '|')
                    print(don_request['item_quantities'])
                    don_request['item_quantities'] = [
                        item_quan.split(':') for item_quan in don_request['item_quantities'] if int(item_quan.split(':')[1]) > 0]
                    parsed_requests.append(don_request)

            response = make_response(render_template(
                'admin/manual_matching.html', name=name, donation_requests=parsed_requests, pledges=parsed_pledges))
            return response

@app.route('/edit_event/<event_name>', methods=['GET', 'POST'])
def edit_event(event_name):
    if request.method == 'GET':
        data_payload = {
            'event_name': event_name
        }
        token = request.cookies.get('JWT')
        res = requests.get(
            'http://localhost:5000/api/v1/get_event',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']
        event_details = json.loads(res.text)['event_details']
        event_details['event_date'] = event_details['event_date'].split('T')[0]
        event_details['existing_items'] = ''
        for item in event_details['items'].split(', '):
            event_details['existing_items'] += '<div class="input-group mb-3"> \
                        <div class="input-group-prepend"> \
                            <span class="input-group-text remove_field" id="basic-addon1"><a style="color: red; font-size: 1.5em;" class="fas fa-trash"></a></span> \
                        </div> \
                        <input type="text" class="form-control form-control-user" placeholder="Item name ..." name="mytext[]" value="'+item+'" required> \
                        </div>'
        print(event_details)
        
        response = make_response(render_template(
            'admin/edit_event.html', event=event_details))
        return response

    if request.method == 'POST':
        headers = request.headers
        if headers.get('Content-Type') == json_header:
            data_string = request.get_data()
            form = json.loads(data_string)
        else:
            form = request.form

        event_name = form['event_name']
        disaster_type = form['disaster_type']
        severity = form['severity']
        location = form['location']
        zipcode = form['zipcode']
        event_date = form['event_date']
        if headers.get('Content-Type') == json_header:
            items = form['items']
        else:
            items = form.getlist('mytext[]')
            items = ', '.join(items)

        data_payload = {
            'event_name': event_name,
            'disaster_type': disaster_type,
            'severity': severity,
            'location': location,
            'event_date': str(event_date),
            'zipcode': zipcode,
            'items': items
        }
        token = request.cookies.get('JWT')
        res = requests.post(
            'http://localhost:5000/api/v1/edit_event',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']
        
        response = make_response(redirect('/dashboard'))
        return response

@app.route('/expire_event/<event_name>', methods=['GET'])
def expire_event(event_name):
    if request.method == 'GET':
        
        data_payload = {
            'event_name': event_name
        }
        token = request.cookies.get('JWT')
        res = requests.post(
            'http://localhost:5000/api/v1/expire_event',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']
        response = make_response(redirect('/dashboard'))
        return response

@app.route('/pledge', methods=['POST', 'GET'])
def pledge():
    if request.method == 'GET':
        return render_template('donor/pledge.html')
    elif request.method == 'POST':
        headers = request.headers
        form = request.form
        if headers.get('Content-Type') == json_header:
            items = form['items']
            amounts = form['amounts']
        else:
            items = form.getlist('mytext[]')
            amounts = form.getlist('amounts[]')

        pledge=[]
        for item, amount in zip(items, amounts):
            pledge.append(item+":"+amount)
        pledge = '|'.join(pledge)
        data_payload = {
            'email': request.cookies.get('Email'),
            'item_quantities': pledge
        }
        
        token = request.cookies.get('JWT')
        res = requests.post(
            'http://localhost:5000/api/v1/pledge_resources',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']

        response = make_response(redirect('/dashboard'))
        response.set_cookie('message_donor', message)
        return response

@app.route('/make_donation', methods=['POST'])
def make_donation():
    if request.method == 'POST':
        headers = request.headers
        if headers.get('Content-Type') == json_header:
            data_string = request.get_data()
            form = json.loads(data_string)
        else:
            form = request.form

        data_payload = {
            'event_name': form['event_name'],
            'donor_email': request.cookies.get('Email'),
            'recipient_email': form['recipient_email'],
            'items': []
        }

        items = form['items_quantities']
        
        for item in items.split('|'):
            try:
                item = item.strip().split(':')
            
                item_name = item[0].strip()
                item_required_quantity = item[1].strip()
                give_quantity = form[item_name]
                
                data_payload['items'].append(
                    item_name + ":" + str(int(item_required_quantity) - int(give_quantity)))
            except Exception as e:
                print(e)
        
        data_payload['items'] = '|'.join(data_payload['items'])
        print(data_payload)
        token = request.cookies.get('JWT')
        res = requests.post(
            'http://localhost:5000/api/v1/make_donation',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']
        
        response = make_response(redirect('/dashboard'))
        response.set_cookie('message_donor', message)
        return response

@app.route('/request_resources', methods=['POST'])
def request_resources():
    if request.method == 'POST':
        headers = request.headers
        if headers.get('Content-Type') == json_header:
            data_string = request.get_data()
            form = json.loads(data_string)
        else:
            form = request.form

        data_payload = {
            'event_name': form['event_name'],
            'email': request.cookies.get('Email'),
            'items': []
        }

        items = form['items']
        for item in items.split(', '):
            quantity = form[item]
            data_payload['items'].append(item + ":" + str(quantity))
        
        data_payload['item_quantities'] = '|'.join(data_payload['items'])
        
        token = request.cookies.get('JWT')
        res = requests.post(
            'http://localhost:5000/api/v1/request_resources',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']

        response = make_response(redirect('/dashboard'))
        response.set_cookie('message_recipient', message)
        return response    

@app.route('/create_event', methods=['POST', 'GET'])
def create_event():
    if request.method == 'GET':
        return render_template('admin/create_event.html')
    elif request.method == 'POST':
        headers = request.headers
        if headers.get('Content-Type') == json_header:
            data_string = request.get_data()
            form = json.loads(data_string)
        else:
            form = request.form

        event_name = form['event_name']
        disaster_type = form['disaster_type']
        severity = form['severity']
        location = form['location']
        zipcode = form['zipcode']
        event_date = form['event_date']
        if headers.get('Content-Type') == json_header:
            items = form['items']
        else:
            items = form.getlist('mytext[]')
            items = ', '.join(items)
        
        data_payload = {
            'event_name': event_name,
            'disaster_type': disaster_type,
            'severity': severity,
            'location': location,
            'event_date': str(event_date),
            'zipcode': zipcode,
            'items': items
        }
        token = request.cookies.get('JWT')
        res = requests.post(
            'http://localhost:5000/api/v1/create_event',
            headers={
                'Content-Type': api_header,
                'x-auth-token': token
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']

        if message == 'Event Created!':
            response = make_response(redirect('/dashboard'))
            return response
        elif message == "Cannot create event at the moment!" or message == "Event already exists!":
            return render_template('admin/create_event.html', message = message)
        else:
            response = make_response(redirect('/'))
            response.set_cookie('JWT', '')
            response.set_cookie('message', message)
            return response

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if request.method == 'GET':
        response = make_response(redirect(url_for('login')))
        response.set_cookie('JWT', '')
        response.delete_cookie('Name')
        response.delete_cookie('Role')
        response.delete_cookie('Zipcode')
        response.delete_cookie('Email')
        return response

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        headers = request.headers
        if headers.get('Content-Type') == json_header:
            data_string = request.get_data()
            form = json.loads(data_string)
        else:
            form = request.form

        email = form['email']
        password = form['password']
        role = form['options']
        fullname = form['name']
        zipcode = form['zipcode']

        data_payload = {
            'email': email,
            'password': password,
            'fullName': fullname,
            'role': role,
            'zipcode': zipcode
        }
        
        res = requests.post(
            'http://localhost:5000/api/v1/register',
            headers={
                'Content-Type': api_header,
            },
            data=data_payload
        )
        message = json.loads(res.text)['message']
        response = make_response(redirect('/'))
        response.set_cookie('message', message)
        return response

    else:
        return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        headers = request.headers
        if headers.get('Content-Type') == json_header:
            data_string = request.get_data()
            form = json.loads(data_string)
        else:
            form = request.form
        
        email = form['email']
        password = form['password']

        res = requests.post(
            'http://localhost:5000/api/v1/login',
            headers={
                'Content-Type': api_header
            },
            data={
                'email': email,
                'password': password
            }
        )
        
        message = json.loads(res.text)['message']
        if message == "Email or password does not match!":
            return render_template('login.html', message=message)
        else:
            token = json.loads(res.text)['token']
            user = json.loads(res.text)['payload']['user']
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('JWT', token)
            response.set_cookie('Name', user['name'])
            response.set_cookie('Role', user['role'])
            response.set_cookie('Zipcode', user['zipcode'])
            response.set_cookie('Email', user['email'])
            return response

    else:
        token = request.cookies.get('JWT')
        if token=='':
            return render_template('login.html')
        else:
            return redirect(url_for('dashboard'))
    
def admin_dashboard(token):
    res = requests.get(
        'http://localhost:5000/api/v1/admin',
        headers={
                    'x-auth-token': token
                }
    )
    message = json.loads(res.text)['message']
    if message == "Welcome to Admin Page!":
        events = json.loads(res.text)['events']
        parsed_events = []
        for event in events:
            event['event_date'] = event['event_date'].split('T')[0]
            parsed_events.append(event)
        name = request.cookies.get('Name')
        response = make_response(render_template(
            'admin/dashboard.html', name=name, events=parsed_events))
        response.set_cookie('JWT', token)
        return response
    else:
        response = make_response(redirect('/'))
        response.set_cookie('JWT', '')
        response.set_cookie('message', message)
        return response

def update_pledges(token):
    pledges = requests.get(
        'http://localhost:5000/api/v1/get_pledges',
        headers={
            'x-auth-token': token
        }
    )
    pledges = json.loads(pledges.text)['pledges']

    res = requests.get(
        'http://localhost:5000/api/v1/donor',
        headers={
            'x-auth-token': token
        }
    )

    donation_requests = json.loads(res.text)['requests']
    for don_request in donation_requests:
        print(don_request)
        don_request['item_quantities'] = don_request['item_quantities'].split('|')
        don_request['item_quantities'] = [
            tuple(item_quan.split(':')) for item_quan in don_request['item_quantities']]
        don_request['item_quantities'] = dict(don_request['item_quantities'])
        for pledge in pledges:
            pledge['item_quantities'] = pledge['item_quantities'].split(
                '|')
            pledge['item_quantities'] = [
                tuple(item_quan.split(':')) for item_quan in pledge['item_quantities']]
            try:
                pledge['item_quantities'] = dict(
                    pledge['item_quantities'])
            except Exception as e:
                continue
            
            updated=False
            for item in don_request['item_quantities']:
                if (item in pledge['item_quantities']) and (int(pledge['item_quantities'][item]) > 0) and (int(don_request['item_quantities'][item]) > 0):
                    updated=True
                    don_amount = int(don_request['item_quantities'][item])
                    pledge_amount = int(pledge['item_quantities'][item])
                    
                    don_request['item_quantities'][item] = str(
                        don_amount - pledge_amount)
                    
                    pledge['item_quantities'][item] = str(
                        pledge_amount - don_amount)
            if updated:
                new_pledge_item_quan = []
                for item in pledge['item_quantities']:
                    if int(pledge['item_quantities'][item]) > 0:
                        new_pledge_item_quan.append(
                            item+":"+pledge['item_quantities'][item])
                new_pledge_item_quan = '|'.join(new_pledge_item_quan)
                data_payload = {
                    'id': pledge['id'],
                    'item_quantities': new_pledge_item_quan
                }
                res = requests.post(
                    'http://localhost:5000/api/v1/update_pledge',
                    headers={
                        'Content-Type': api_header,
                        'x-auth-token': token
                    },
                    data=data_payload
                )

                new_donation_item_quan = []
                for item in don_request['item_quantities']:
                    if int(don_request['item_quantities'][item]) > 0:
                        new_donation_item_quan.append(
                            item+":"+don_request['item_quantities'][item])
                new_donation_item_quan = '|'.join(new_donation_item_quan)
                
                data_payload = {
                    'event_name': don_request['event_name'],
                    'donor_email': request.cookies.get('Email'),
                    'recipient_email': don_request['email'],
                    'items': new_donation_item_quan
                }
                res = requests.post(
                    'http://localhost:5000/api/v1/make_donation',
                    headers={
                        'Content-Type': api_header,
                        'x-auth-token': token
                    },
                    data=data_payload
                )
                update_pledges(token)
        
def donor_dashboard(token, display_message=""):
    # update_pledges(token)
    res = requests.get(
        'http://localhost:5000/api/v1/donor',
        headers={
                        'x-auth-token': token
                    }
    )
    message = json.loads(res.text)['message']
    if message == "Welcome to Donor Page!":
        name = request.cookies.get('Name')
        donation_requests = json.loads(res.text)['requests']
        parsed_requests = []
        for don_request in donation_requests:
            if don_request['item_quantities'] != '':
                don_request['raw_item_quantities'] = don_request['item_quantities']
                don_request['item_quantities'] = don_request['item_quantities'].split('|')
                don_request['item_quantities'] = [
                    item_quan.split(':') for item_quan in don_request['item_quantities'] if int(item_quan.split(':')[1]) > 0]
                parsed_requests.append(don_request)

        response = make_response(
            render_template('donor/dashboard.html', name=name, donation_requests=parsed_requests, message=display_message))
        response.set_cookie('JWT', token)
        return response
    else:
        response = make_response(redirect('/'))
        response.set_cookie('JWT', '')
        response.set_cookie('message', message)
        return response

def recipient_dashboard(token, display_message=""):
    res = requests.get(
        'http://localhost:5000/api/v1/recipient',
        headers={
                        'x-auth-token': token
                    }
    )

    message = json.loads(res.text)['message']
    if message == "Welcome to Recipient Page!":
        events = json.loads(res.text)['events']
        parsed_events = []
        for event in events:
            event['item_names'] = event['items'].split(', ')
            event['event_date'] = event['event_date'].split('T')[0]
            parsed_events.append(event)
        name = request.cookies.get('Name')
        response = make_response(
            render_template('recipient/dashboard.html', name=name, events=parsed_events, message=display_message))
        response.set_cookie('JWT', token)
        return response
    else:
        response = make_response(redirect('/'))
        response.set_cookie('JWT', '')
        response.set_cookie('message', message)
        return response

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if request.method == 'GET':
        token = request.cookies.get('JWT')
        
        if token == '':
            response = make_response(redirect('/'))
            response.set_cookie('JWT', '')
            response.set_cookie('message', 'Only Logged In Users have Access')
            return response
        role = request.cookies.get('Role')
        if role == 'admin':  
            return admin_dashboard(token)
        elif role == 'donor':
            if 'message_donor' in request.cookies:
                message = request.cookies.get('message_donor')
            else:
                message=""
            return donor_dashboard(token, message)
        elif role == 'recipient':
            if 'message_recipient' in request.cookies:
                message = request.cookies.get('message_recipient')
            else:
                message = ""
            return recipient_dashboard(token, message)






@app.route('/')
def dams_homepage():
    message = request.cookies.get('message')
    response = make_response(render_template('home.html', message=message))
    if 'JWT' not in request.cookies:
        response.set_cookie('JWT', '')
    if 'message' in request.cookies:
        response.set_cookie('message', '')
    return response

@app.route('/groq-api', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        
        if not user_message:
            return jsonify({"response": "Please provide a message"}), 400

        headers = {
            "Authorization": "",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        response.raise_for_status()  # Raises an HTTPError for bad responses
        response_data = response.json()

        bot_reply = response_data["choices"][0]["message"]["content"]
        return jsonify({"response": bot_reply})

    except requests.exceptions.RequestException as e:
        return jsonify({"response": f"Network error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500
    
    
    
    
    
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   




CORS(app)  # Enable CORS for all routes

# 🔹 API KEYS
API_KEY_OPENWEATHER = ""
API_KEY_NASA = ""
USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
CITIES = ["Kochi", "Bengaluru", "Guwahati", "Kolkata", "Mumbai"]

# 🔹 Initialize all models and scalers
models = {
    'weather': None,
    'flood': None,
    'storm': None,
    'earthquake': None,
    'wildfire': None
}

scalers = {
    'weather': None,
    'flood': None,
    'storm': None,
    'earthquake': None,
    'wildfire': None
}

# 🔹 Training Data for each disaster type
def generate_training_data():
    # Weather Risk Model (existing)
    X_weather = np.array([
        [42, 90, 18], [40, 85, 15], [38, 80, 12],  # Very High
        [36, 75, 10], [34, 70, 9], [32, 65, 8],    # High
        [30, 60, 6], [28, 55, 5], [27, 50, 4],     # Moderate
        [25, 45, 3], [22, 40, 3], [20, 35, 2],     # Low
        [18, 30, 2], [16, 25, 1], [14, 20, 1]      # Very Low
    ])
    y_weather = [
        "Very High", "Very High", "Very High",
        "High", "High", "High",
        "Moderate", "Moderate", "Moderate",
        "Low", "Low", "Low",
        "Very Low", "Very Low", "Very Low"
    ]

    # Flood Risk Model (rainfall, humidity, elevation, soil_moisture)
    X_flood = np.random.rand(200, 4) * np.array([300, 100, 1000, 100])  # mm, %, m, %
    y_flood = (X_flood[:, 0] * 0.6 + X_flood[:, 1] * 0.3 + (100 - X_flood[:, 3]) * 0.1) / 100
    y_flood = np.where(y_flood > 0.7, "High", np.where(y_flood > 0.4, "Medium", "Low"))

    # Storm Risk Model (wind_speed, pressure_change, temperature_diff, humidity)
    X_storm = np.random.rand(200, 4) * np.array([50, 30, 20, 100])  # m/s, hPa, °C, %
    y_storm = (X_storm[:, 0] * 0.5 + X_storm[:, 1] * 0.3 + X_storm[:, 2] * 0.2) / 30
    y_storm = np.where(y_storm > 0.7, "High", np.where(y_storm > 0.4, "Medium", "Low"))

    # Earthquake Risk Model (magnitude, depth, distance, population_density)
    X_earthquake = np.random.rand(150, 4) * np.array([10, 200, 500, 10000])  # Richter, km, km, people/km²
    y_earthquake = (X_earthquake[:, 0] * 0.7 + (100 - X_earthquake[:, 1]/2) * 0.2 + X_earthquake[:, 3]/10000 * 0.1) / 10
    y_earthquake = np.where(y_earthquake > 0.7, "High", np.where(y_earthquake > 0.4, "Medium", "Low"))

    # Wildfire Risk Model (temp, humidity, vegetation, drought_index)
    X_wildfire = np.random.rand(200, 4) * np.array([50, 100, 1, 5])  # °C, %, index (0-1), index (0-5)
    y_wildfire = (X_wildfire[:, 0] * 0.5 + (100 - X_wildfire[:, 1]) * 0.3 + X_wildfire[:, 2] * 0.1 + X_wildfire[:, 3] * 0.1) / 5
    y_wildfire = np.where(y_wildfire > 0.7, "High", np.where(y_wildfire > 0.4, "Medium", "Low"))

    return {
        'weather': (X_weather, y_weather),
        'flood': (X_flood, y_flood),
        'storm': (X_storm, y_storm),
        'earthquake': (X_earthquake, y_earthquake),
        'wildfire': (X_wildfire, y_wildfire)
    }

# 🔹 Load or Train Model Function
def load_or_train_model(model_type, model_filename, train_data, train_labels):
    if os.path.exists(model_filename):
        try:
            with open(model_filename, "rb") as f:
                scaler, model = pickle.load(f)
                print(f"✅ {model_type} model loaded successfully.")
                return scaler, model
        except Exception as e:
            print(f"⚠ Error loading {model_type} model: {e}. Retraining...")
    
    # Train New Model
    scaler = StandardScaler()
    train_data = scaler.fit_transform(train_data)
    
    # Split data for validation
    X_train, X_test, y_train, y_test = train_test_split(train_data, train_labels, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=200, min_samples_split=5, random_state=42)
    model.fit(X_train, y_train)
    
    # Validate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ New {model_type} model trained. Accuracy: {accuracy:.2f}")
    
    # Save Model
    with open(model_filename, "wb") as f:
        pickle.dump((scaler, model), f)
    
    return scaler, model

# Initialize all models
def initialize_models():
    training_data = generate_training_data()
    
    for model_type in models.keys():
        X, y = training_data[model_type]
        scaler, model = load_or_train_model(
            model_type, 
            f"{model_type}_model.pkl", 
            X, 
            y
        )
        scalers[model_type] = scaler
        models[model_type] = model

initialize_models()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/hotspot-prediction')
def get_hotspots():
    hotspots = []
    for city in CITIES:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY_OPENWEATHER}&units=metric"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if response.status_code != 200 or "main" not in data:
                print(f"⚠ No valid weather data for {city}")
                continue
            
            temp = data["main"].get("temp", 0)
            humidity = data["main"].get("humidity", 0)
            wind_speed = data["wind"].get("speed", 0)
            
            # Normalize input
            scaled_features = scalers['weather'].transform([[temp, humidity, wind_speed]])
            
            # Predict Risk Level
            risk_level = models['weather'].predict(scaled_features)[0]
            
            hotspots.append({
                "city": city,
                "temperature": temp,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "risk_level": risk_level
            })
        
        except Exception as e:
            print(f"❌ Error fetching data for {city}: {e}")
    
    return jsonify({"hotspots": hotspots})

# ML-based risk prediction functions
def predict_flood_risk(rainfall, humidity, elevation=50, soil_moisture=50):
    try:
        scaled_input = scalers['flood'].transform([[rainfall, humidity, elevation, soil_moisture]])
        risk_level = models['flood'].predict(scaled_input)[0]
        return {"High": 0.8, "Medium": 0.5, "Low": 0.2}[risk_level]
    except Exception as e:
        print(f"Error in flood prediction: {e}")
        return min(max((rainfall * 0.7 + humidity * 0.3) / 100, 0), 1)

def predict_storm_risk(wind_speed, pressure, temp_diff=5, humidity=50):
    try:
        pressure_change = abs(1010 - pressure)
        scaled_input = scalers['storm'].transform([[wind_speed, pressure_change, temp_diff, humidity]])
        risk_level = models['storm'].predict(scaled_input)[0]
        
        # More dynamic risk values based on actual conditions
        if wind_speed > 15:  # High wind speed
            return min(0.7 + (wind_speed - 15) * 0.02, 0.9)
        elif pressure_change > 15:  # Significant pressure change
            return min(0.6 + pressure_change * 0.01, 0.8)
        else:
            return {"High": 0.6, "Medium": 0.35, "Low": 0.15}[risk_level]
            
    except Exception as e:
        print(f"Error in storm prediction: {e}")
        # More responsive fallback calculation
        storm_score = (wind_speed * 0.5 + abs(1010 - pressure) * 0.3) / 25
        return min(max(storm_score, 0.1), 0.8)

def predict_earthquake_risk(magnitude=None, depth=None, distance=50, population_density=1000):
    try:
        if magnitude is None:
            return random.uniform(0, 0.3)
        
        scaled_input = scalers['earthquake'].transform([[magnitude, depth, distance, population_density]])
        risk_level = models['earthquake'].predict(scaled_input)[0]
        return {"High": 0.85, "Medium": 0.55, "Low": 0.25}[risk_level]
    except Exception as e:
        print(f"Error in earthquake prediction: {e}")
        return min(max((magnitude * 0.8 + (100 - depth) * 0.2) / 10, 0), 1)

def predict_wildfire_risk(temp, humidity, lat=None, lon=None, vegetation=0.5, drought_index=2):
    try:
        scaled_input = scalers['wildfire'].transform([[temp, humidity, vegetation, drought_index]])
        risk_level = models['wildfire'].predict(scaled_input)[0]
        
        # Adjusted base risk values
        base_risk = {
    "High": 0.45,    # Reduced from 0.65 (45% instead of 65%)
    "Medium": 0.25,  # Reduced from 0.35 (25% instead of 35%) 
    "Low": 0.05      # Reduced from 0.1 (5% instead of 10%)
}[risk_level]
        
        if lat is not None and lon is not None:
            try:
                nasa_url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{API_KEY_NASA}/VIIRS_SNPP_NRT/world/1/{lat}/{lon}/{lat}/{lon}"
                nasa_response = requests.get(nasa_url, timeout=5)
                
                if nasa_response.ok:
                    wildfire_data = nasa_response.text.splitlines()
                    if len(wildfire_data) > 1:
                        fire_count = len(wildfire_data) - 1
                        # Reduced impact of active fires
                        risk_increase = min(fire_count * 0.02, 0.15)  # Max 15% increase
                        return min(base_risk + risk_increase, 0.8)  # Cap at 80%
            
            except requests.exceptions.RequestException as e:
                print(f"NASA API request failed: {e}")
        
        return base_risk
    
    except Exception as e:
        print(f"Error in wildfire prediction: {e}")
        # More conservative fallback
        return min(max((temp * 0.5 + (100 - humidity) * 0.3) / 100, 0), 0.7)

@app.route('/disaster-risk', methods=['GET'])
def predict_disaster():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    try:
        # 1. Fetch weather data from OpenWeatherMap
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY_OPENWEATHER}&units=metric"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        if weather_response.status_code != 200:
            return jsonify({
                "error": "Failed to fetch weather data",
                "details": weather_data.get("message", "Unknown error")
            }), 500

        # Extract weather parameters
        rainfall = weather_data.get("rain", {}).get("1h", 0)
        humidity = weather_data["main"].get("humidity", 50)
        temp = weather_data["main"].get("temp", 20)
        wind_speed = weather_data["wind"].get("speed", 0)
        pressure = weather_data["main"].get("pressure", 1010)

        # 2. Fetch earthquake data from USGS (last 30 days within 500km)
        earthquake_url = f"{USGS_API_URL}?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&starttime=-30days&minmagnitude=2.5"
        earthquake_response = requests.get(earthquake_url)
        earthquake_data = earthquake_response.json()

        # Get the most significant recent earthquake
        recent_quake = None
        if earthquake_data.get("features"):
            recent_quake = max(earthquake_data["features"], 
                              key=lambda x: x["properties"]["mag"], 
                              default=None)

        # Calculate risks using ML models
        flood_risk = predict_flood_risk(rainfall, humidity)
        storm_risk = predict_storm_risk(wind_speed, pressure)
        
        if recent_quake:
            earthquake_risk = predict_earthquake_risk(
                recent_quake["properties"]["mag"], 
                recent_quake["geometry"]["coordinates"][2]
            )
        else:
            earthquake_risk = predict_earthquake_risk()
            
        wildfire_risk = predict_wildfire_risk(temp, humidity)

        return jsonify({
            "latitude": lat,
            "longitude": lon,
            "flood_risk": round(flood_risk, 2),
            "storm_risk": round(storm_risk, 2),
            "earthquake_risk": round(earthquake_risk, 2),
            "wildfire_risk": round(wildfire_risk, 2)
        })
    
    except requests.exceptions.RequestException as e:
        print(f"Network error in disaster prediction: {e}")
        return jsonify({"error": "Network error fetching data"}), 500
    except Exception as e:
        print(f"Error in disaster prediction: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)