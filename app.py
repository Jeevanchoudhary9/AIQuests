#from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Import CORS

app=Flask(__name__)
# Initialize CORS for the entire app (allows all domains)
CORS(app)

import config
import models
import routes
