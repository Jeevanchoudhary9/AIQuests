#from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Import CORS
import os

os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"]="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"
os.environ["LANGCHAIN_PROJECT"]="AIQuest"

app=Flask(__name__)
# Initialize CORS for the entire app (allows all domains)
CORS(app)

import config
import models
import routes
