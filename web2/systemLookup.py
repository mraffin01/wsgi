from flask import Flask, redirect, render_template, url_for
#from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
#from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import yaml
import xmlrpc.client
import os
import datetime

def convert_datetime(obj):
    if isinstance(obj, xmlrpc.client.DateTime):
        # Convert xmlrpc.client.DateTime to Python datetime
        return datetime.datetime.strptime(str(obj), "%Y%m%dT%H:%M:%S").isoformat()
    return obj
    
def load_config(file_path='/srv/www/wsgi/web/config.yaml'):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config
    
# Global config variable
config = load_config()  # Load the configuration once when the script runs

# Initialize Flask app
app = Flask(__name__)

def decrypt_password(private_key_path="/srv/www/wsgi/web/private_key.pem", file_path="/srv/www/wsgi/web/.userfile"):
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

#========================================================
# Route for the root URL that redirects to /systems
@app.route('/')
def home():
    return redirect(url_for('systems_page'))  # Redirect to /systems

@app.route('/systems', methods=['GET'])
def systems_page():
    return render_template('loading.html')  # Show splash screen first

@app.route('/systems/data', methods=['GET'])
def systems_data():
  
    client = xmlrpc.client.ServerProxy(config['SUMA_API_URL'], allow_none=True)
    session_key = client.auth.login(config['USERNAME'], decrypt_password())

    try:
        system_data = client.system.listActiveSystems(session_key)
        inactive_systems = client.system.listInactiveSystems(session_key)

        active_systems = []

        for system in system_data:
            system_id = system["id"]
            #system_name = system["name"]
            system_name = system["name"].split('.')[0]
            last_checkin = convert_datetime(system["last_checkin"])  # Convert DateTime
            last_boot = convert_datetime(system["last_boot"])  # Convert DateTime

        #    relevant_errata = client.system.getRelevantErrata(session_key, system_id)
        #    upgradable_packages = client.system.listLatestUpgradablePackages(session_key, system_id)

        #    patch_count = len(relevant_errata)
        #    package_count = len(upgradable_packages)

            active_systems.append({
                "name": system_name,
                "id": system_id,
                "last_checkin": last_checkin,
                "last_boot": last_boot,
        #        "patches_needed": patch_count,
        #        "packages_needed": package_count
            })

        sorted_active_systems = sorted(active_systems, key=lambda sys: sys.get('name', ''))

        sorted_inactive_systems = sorted(
         [
          {
            "name": sys["name"].split('.')[0],  # Safely remove domain if present
            "last_checkin": convert_datetime(sys["last_checkin"]),
            "last_boot": convert_datetime(sys["last_boot"]),
          }
          for sys in inactive_systems
         ], key=lambda sys: sys.get('last_checkin', ''))

    finally:
        client.auth.logout(session_key)

    return {
        "active_systems": sorted_active_systems,
        "inactive_systems": sorted_inactive_systems,
    }

#========================================================
@app.route('/updates/<int:system_id>')
def get_updates(system_id):

    # Get credentials from the file
    #    USERNAME, PASSWORD = credentials.get_credentials(CREDENTIALS_FILE)


    # Ensure credentials were found
    if not config['USERNAME']:
        return "Error: Missing username or password in credentials file", 400


    client = xmlrpc.client.ServerProxy(config['SUMA_API_URL'], allow_none=True)
    session_key = client.auth.login(config['USERNAME'], decrypt_password())

    system_info = client.system.getNetwork(session_key, system_id)
    # Get relevant patches and upgradable packages
    relevant_errata = client.system.getRelevantErrata(session_key, system_id)
    upgradable_packages = client.system.listLatestUpgradablePackages(session_key, system_id)

    client.auth.logout(session_key)
    # Sort patches by patch_type (adjust based on actual field name)
    sorted_patches = sorted(relevant_errata, key=lambda patch: patch.get('advisory_type', ''))
    # Sort packages by name
    sorted_packages = sorted(upgradable_packages, key=lambda package: package.get('name', '').lower())
    # Render the HTML table
    return render_template('updates.html', host=system_info, patches=sorted_patches, packages=sorted_packages)
    
if __name__ == "__main__":
     app.run(debug=True)

