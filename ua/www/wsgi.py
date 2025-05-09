import sys
import os

# Add the directory containing your app to the sys.path
sys.path.insert(0, '/srv/www/wsgi/ua/www')

# Set the Flask app environment variable (if needed)
os.environ['FLASK_APP'] = 'users.py'

from users import app as application
