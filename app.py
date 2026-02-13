from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os
import requests

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY_CHANGE_ME_12345"

BOT_API_BASE_URL = "https://your-bot-project-name.up.railway.app"
BOT_API_PORT = "30151"

# Config file path
CONFIG_FILE = 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        # Default config if file doesn't exist
        default_config = {"EMOTE APP 🇮🇳 SPEED ULTRA FAST"}
        save_config(default_config)
        return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# ---------- ROUTES ----------
@app.route('/')
def home():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/do_login', methods=['POST'])
def do_login():
    discord_pw = request.form.get('discord-pw', '').strip()
    telegram_pw = request.form.get('telegram-pw', '').strip()
    
    config = load_config()
    
    # Check for admin login
    if discord_pw == config['admin_password'] and telegram_pw == config['admin_password']:
        session['admin_logged_in'] = True
        return jsonify({"status": "success", "redirect": "/admin"})
    
    # Check for regular user login
    if discord_pw == config['user_password'] and telegram_pw == config['user_password']:
        session['logged_in'] = True
        return jsonify({"status": "success", "redirect": "/index"})
    
    return jsonify({"status": "error", "message": "Wrong password"}), 401

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login_page'))
    
    config = load_config()
    return render_template('admin.html', 
                         user_password=config['user_password'],
                         admin_password=config['admin_password'])

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    if not session.get('admin_logged_in'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    new_password = request.form.get('new_password', '').strip()
    password_type = request.form.get('password_type', 'user')
    
    if not new_password:
        return jsonify({"status": "error", "message": "Password cannot be empty"})
    
    config = load_config()
    
    if password_type == 'user':
        config['user_password'] = new_password
    elif password_type == 'admin':
        config['admin_password'] = new_password
    
    save_config(config)
    
    return jsonify({"status": "success", "message": f"{password_type.capitalize()} password updated successfully"})

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login_page'))

@app.route('/index')
def index_page():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    
    try:
        with open('emotes.json', 'r') as f:
            emotes = json.load(f)
        return render_template('index.html', emotes=emotes)
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

# ---------- SEND EMOTE ----------
@app.route('/send_emote', methods=['POST'])
def send_emote():
    if not session.get('logged_in'):
        return jsonify({'message': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        team_code = data.get('team_code')
        emote_id = data.get('emote_id')
        uids = data.get('uids', [])

        if not all([team_code, emote_id, uids]):
            return jsonify({'message': 'Error: Missing data'}), 400

        params = {
            'emote_id': emote_id,
            'tc': team_code
        }
        for i, uid in enumerate(uids):
            params[f'uid{i+1}'] = uid

        api_url = f"{BOT_API_BASE_URL}:{BOT_API_PORT}/join"
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()

        return jsonify({
            'message': 'Emote request sent successfully to the bot!',
            'api_response': response.json()
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Error communicating with the bot API: {e}'}), 500
    except Exception as e:
        return jsonify({'message': f'Internal error: {e}'}), 500

if __name__ == "__main__":
    # Ensure config file exists
    load_config()
    app.run(debug=True, host='0.0.0.0', port=5000)