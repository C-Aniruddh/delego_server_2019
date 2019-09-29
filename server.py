from flask import Flask, render_template, url_for, request, session, redirect, send_from_directory, jsonify
from flask_pymongo import PyMongo
from werkzeug import secure_filename
import uuid
import json
import bcrypt
import re
import os
import datetime

app = Flask(__name__)
app.secret_key = 'mysecret'

dir_path = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = str(os.path.join(dir_path, 'static/uploads'))
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


app.config['MONGO_DBNAME'] = 'delego3'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/delego3'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_PATH'] = 8192


mongo = PyMongo(app)
users = mongo.db.users
files = mongo.db.files
speakers = mongo.db.speakers
speaker_preferences = mongo.db.speaker_preferences
shop_items = mongo.db.shop_items
orders = mongo.db.orders



@app.route('/delegate/rd')
def delegate_rd():
    uid = request.args.get('uid')
    find_user = users.find({'uid': uid})
    if find_user.count() > 0:
        users.update({'uid': uid}, {"$set": {'rsvp': 'Arrived'}})
        return json.dumps({'status': 'successful', 'action': 'rsvp'})
    else:
        return json.dumps({'status': 'unsuccessful', 'action': 'rsvp'})

@app.route('/delegate/food')
def delegate_food():
    uid = request.args.get('uid')
    session = request.args.get('session')
    day = request.args.get('day')
    find_user = users.find_one({'uid': uid})
    existing_data = dict(find_user['food_data'])
    new_data = existing_data
    new_data[day][session] = "Checked In"
    users.update({'uid': uid}, {"$set": {'food_data': new_data}})
    return json.dumps({'status': 'successful', 'action': 'food_sessions'})

@app.route('/delegate/eb_attendance')
def eb_attendance():
    uid = request.args.get('uid')
    session = request.args.get('session')
    day = request.args.get('day')
    find_user = users.find_one({'uid': uid})
    existing_data = dict(find_user['committee_data'])
    new_data = existing_data
    new_data[day][session] = "Present"
    users.update({'uid': uid}, {"$set": {'committee_data': new_data}})
    return json.dumps({'status': 'successful', 'action': 'eb_attendance'})


@app.route('/eb/get_list_countries')
def get_list():
    committee = request.args.get('committee')
    users_list = users.find({'committee': committee})
    to_ret = []
    for user in users_list:
        country = user['country']
        committee = user['committee']
        uid = user['uid']
        dic = {'country': country, 'committee': committee, 'uid': uid}
        to_ret.append(dic)

    return json.dumps(to_ret)


@app.route('/upload_files', methods=['POST'])
def handle_files():
    file = request.files['file']
    committee = request.form['committee']
    uid = request.form['uid']
    display_name = request.form['display_name']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        full_path = str(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        files.insert({'display_name': display_name, 'uid': uid, 'committee': committee, 'file_path': full_path})
        return json.dumps({'status': 'successful', 'action': 'upload_file'})


@app.route('/enable_speakers')
def enable_speakers():
    committee = request.args.get('committee')
    find_speaker_preference = speaker_preferences.find({'committee': committee})
    
    if find_speaker_preference.count() == 0:
        speaker_preferences.insert({'committee': committee, 'allowed': 'no'})
    
    speaker_preferences.update({'committee': committee}, {'$set': {'allowed': 'yes'}})
    return json.dumps({'status': 'successful', 'action': 'enable speakers'})

@app.route('/disable_speakers')
def disable_speakers():
    committee = request.args.get('committee')
    find_speaker_preference = speaker_preferences.find({'committee': committee})
    
    if find_speaker_preference.count() == 0:
        speaker_preferences.insert({'committee': committee, 'allowed': 'no'})
    
    speaker_preferences.update({'committee': committee}, {'$set': {'allowed': 'no'}})
    return json.dumps({'status': 'successful', 'action': 'disable speakers'})


@app.route('/add_to_speakers')
def add_to_speakers():
    uid = request.args.get('uid')
    committee = request.args.get('committee')
    find_preference = speaker_preferences.find_one({'committee': committee})
    allowed = find_preference['allowed']
    if allowed == "yes":
        speakers.insert({'uid': uid, 'committee': committee})
        return json.dumps({'status': 'successful', 'action': 'add to speakers'})
    else:
        return json.dumps({'status': 'unsuccessful', 'action': 'add to speakers'})

@app.route('/remove_from_speakers')
def remove_from_speakers():
    uid = request.args.get('uid')
    committee = request.args.get('committee')
    find_preference = speaker_preferences.find_one({'committee': committee})
    allowed = find_preference['allowed']
    if allowed == "yes":
        speakers.remove({'uid': uid, 'committee': committee})
        return json.dumps({'status': 'successful', 'action': 'remove from speakers'})
    else:
        return json.dumps({'status': 'unsuccessful', 'action': 'add to speakers'})


@app.route('/add_to_shop', methods = ['POST'])
def add_to_shop():
    image_url = request.form['image_url']
    image_url2 = request.form['image_url2']
    item_title = request.form['title']
    item_description = request.form['description']
    item_cost = request.form['cost']
    uid = str(uuid.uuid4().hex)
    shop_items.insert({'image_url': image_url, 'image_url2': image_url2, 'title': item_title, 'description': item_description, 'uid': uid, 'cost': item_cost})
    return json.dumps({'status': 'successful', 'action': 'add to shop'})

@app.route('/remove_from_shop')
def remove_from_shop():
    uid = request.args.get('uid')
    shop_items.remove({'uid': uid})


@app.route('/list_items')
def list_items():
    items = shop_items.find()
    return json.dumps(items)

@app.route('/place_order', methods=['POST'])
def place_order():
    user_uid = request.args.get('user_uid')
    item_uid = request.args.get('item_uid')
    timestamp = str(datetime.datetime.now().timestamp())
    order_uid = str(uuid.uuid4().hex)
    orders.insert({'order_uid': order_uid, 'item_uid': item_uid, 'user_uid': user_uid, 'timestamp': timestamp})
    return json.dumps({'status': 'successful', 'action': 'add to order'})

## Routes for resetting values for everyone

@app.route('/update_all_sessions')
def committee():
    all_users = users.find()
    print(all_users.count())
    for user in all_users:
        user_email = user['email']
        food_data = {'day1' : {'session1': 'pending', 'session2': 'pending'}, 'day2' : {'session1': 'pending', 'session2': 'pending', 'session3': 'pending'}, 'day3' : {'session1': 'pending', 'session2': 'pending'}}
        users.update({'email': user_email}, {"$set": {'committee_data': food_data}})
        print("Updated user with id : {}".format(user_email))
    return 'done'


@app.route('/update_all_food')
def update_food():
    all_users = users.find()
    for user in all_users:
        user_email = user['email']
        food_data = {'day1' : {'session1': 'pending', 'session2': 'pending'}, 'day2' : {'session1': 'pending', 'session2': 'pending', 'session3': 'pending'}, 'day3' : {'session1': 'pending', 'session2': 'pending'}}
        users.update({'email': user_email}, {"$set": {'food_data': food_data}})
        print("Updated user with id : {}".format(user_email))
    return 'done'


@app.route('/generate_new_id')
def gen_ids():
    all_users = users.find()
    print(all_users.count())
    count = 1
    for user in all_users:
        generated_id = str(uuid.uuid4().hex)
        users.update({'email': user['email']}, {"$set": {'uid': generated_id}})
        print("Updated user with id : {} - {}".format(user['email'], count))
        count = count + 1

    return 'done'


@app.route('/api/login', methods=['POST'])
def mobilelogin():
    print("Username : " + str(request.form['email']) + "     Password : " + str(request.form['password']))
    login_user = users.find_one({'email': re.compile(request.form['email'], re.IGNORECASE)})
    
    if login_user is None:
       print("Returning invalid email")
       return json.dumps({'status' : 'unsuccessful'})
    
    if login_user:
       if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
            return json.dumps({'status': 'successful', 'action': 'login', 'user_type' : str(login_user['type']), 'user_fullname': str(login_user['name']), 
            'user_phone' : str(login_user['phone']), 'user_country': str(login_user['country']), 'user_committee': str(login_user['committee']), 'uid': login_user['uid']})
    
    return json.dumps({'status': 'unsuccessful'})


@app.route('/generate_passwords')
def generate_passwords():
    all_users = users.find()
    for user in all_users:
        password = 'pass@123'
        hashpass = gen_hashpass(password)
        users.update({'uid': user['uid']}, {'password': hashpass})
        print("Updated user with email : {}".format(user['email']))
    return 'done'

@app.route('/create_oc_account', methods=['POST'])
def create_oc_account():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    committee = 'oc'
    country = 'oc'
    user_type = 'oc'
    rsvp = 'oc'
    committee_data = {}
    food_data = {}
    pas = "oc@2019"
    password = gen_hashpass(pas)
    uid = str(uuid.uuid4().hex)
    users.insert({'name': name, 'email': email, 'phone': phone, 'committee': committee, 'country': country, 'type': user_type, 'rsvp': rsvp, 'committee_data': committee_data, 'food_data': food_data, 'uid': uid, 'password': password})
    return json.dumps({'status': 'successfull', 'action': 'create oc'})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def gen_hashpass(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)