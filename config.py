import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

## Connect to the database
SQLALCHEMY_DATABASE_URI = 'postgresql://rzcrebs:l1nds2y@localhost:5432/fyyur_db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

