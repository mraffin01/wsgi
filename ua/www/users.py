from flask import Flask, request, redirect, render_template, url_for,flash, send_file
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import yaml
import xmlrpc.client
import os
import datetime
import csv
#import pam


#pam_authenticator = pam.pam()
def load_config(file_path='/srv/www/wsgi/ua/www/config.yaml'):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config
    
# Global config variable
config = load_config()  # Load the configuration once when the script runs

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "GssF*x7G^R%@56C7NX0_jyQf0BXOSv8_3jb2y5zkF(Cnx"  # Replace with a secure secret key

def decrypt_password(private_key_path="/srv/www/wsgi/ua/config/private_key.pem", file_path="/srv/www/wsgi/ua/.userfile"):
    with open(private_key_path, "rb") as private_file:
        private_key = serialization.load_pem_private_key(private_file.read(), password=None, backend=default_backend())

    with open(file_path, "rb") as file:
        encrypted_password = file.read()

    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted_password.decode()

# File upload folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads') 
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Allowed file extensions
ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    """Check if the uploaded file is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/l', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Use PAM to authenticate
        if pam_authenticator.authenticate(username, password):
            return jsonify({"message": f"Welcome, {username}!"}), 200
        else:
            return jsonify({"error": "Authentication failed"}), 401

    return render_template('login.html')


@app.route('/download')
def download():
    # Get the file name from the query parameter
    file_name = request.args.get('file')
    if not file_name:
        #abort(400, description="Missing file name")
         flash(f"Error downloading file")
         return redirect(url_for("index"))
    
    # Construct the file path dynamically
    file_path = f'static/{file_name}'
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_name,  # Ensure the downloaded file retains the original name
            mimetype='text/csv'
        )
    except FileNotFoundError as e:
         flash(f"Error downloading file")
         return redirect(url_for("index"))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'file' in request.files:
            # Handle file upload
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(filepath)
                try:
                    add_users_from_file(filepath)
                    flash("Users successfully added from file!")
                except Exception as e:
                    flash(f"Error adding users from file: {e}")
                return redirect(url_for("index"))
        
        elif 'login' in request.form:
            # Handle user addition form
            login = request.form['login']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            vendor = request.form['vendor']
            
            try:
                add_user(login, first_name, last_name, email, vendor)
                flash(f"User {login} successfully added!")
            except Exception as e:
                flash(f"Error adding user {login}: {e}")
            return redirect(url_for("index"))
    return render_template("users.html")

def add_users_from_file(filepath):
    """Add users to SUSE Manager from the uploaded file."""
    # Connect to SUSE Manager API
    client = xmlrpc.client.ServerProxy(config['SUMA_API_URL'], allow_none=True)
    session_key = client.auth.login(config['USERNAME'], decrypt_password())
    
    try:
        # Read the CSV file
        with open(filepath, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(row)  # This will print the entire dictionary for the current row
                
                login = row["login"]
                first_name = row["first_name"]
                last_name = row["last_name"]
                email = row["email"]
                vendor = row['vendor']

                add_user(login, first_name, last_name, email,vendor)
    finally:
        client.auth.logout(session_key)

def add_user(login, first_name, last_name, email, vendor):
    """Add a single user to SUSE Manager."""
    client = xmlrpc.client.ServerProxy(config['SUMA_API_URL'], allow_none=True)
    session_key = client.auth.login(config['USERNAME'], decrypt_password())
    try:
        # Create user account 
        client.user.create(session_key, login.lower(), "", first_name.capitalize(), last_name.capitalize(), email.lower(), 1)
        # Disable email notifications
        client.user.setErrataNotifications(session_key, login, False)
        # Add role
        client.user.addRole(session_key, login, "system_group_admin")
        # Add systems group 
        add_groups (login, vendor)
    finally:
        client.auth.logout(session_key)

def add_groups (login, vendor):
    """Add groups to user."""
    client = xmlrpc.client.ServerProxy(config['SUMA_API_URL'], allow_none=True)
    session_key = client.auth.login(config['USERNAME'], decrypt_password())
    try:
        if vendor == "dxc":
          # Fetch all system groups
          system_groups = client.systemgroup.listAllGroups(session_key)
          group_names = [group['name'] for group in system_groups if group['name'].startswith('x_') or group['name'].startswith('X_')]
          group_names.append('New Server Adds')
          client.user.addAssignedSystemGroups(session_key, login, group_names, False)
        elif vendor == "ibm":
          ibm_groups = ["DXC Onboarding Servers","IBM ANZ"]
          client.user.addAssignedSystemGroups(session_key, login, ibm_groups, False)
        elif vendor == "infosys":
           infosys_groups = ["InfoSys"]
           client.user.addAssignedSystemGroups(session_key, login, infosys_groups, False)          
    finally:
        client.auth.logout(session_key)


@app.errorhandler(500)
def internal_error(error):
    return "An internal server error occurred. Please check your file or input and try again."

if __name__ == "__main__":
    app.run(debug=True)
    #app.run(host="0.0.0.0", port=5000,debug=True)

