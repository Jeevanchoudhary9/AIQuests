import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from sqlalchemy import distinct
from app import app
from functools import wraps
from models import db, User, Questions, Plus_ones, Answers,Votes,Organizations,Moderators,Labels,Invites,Keywords, Docs
import random
from langchain_community.llms.ollama import Ollama
import re
import humanize
from transformers import BertTokenizer, BertModel
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import torch
import io
import random
import os
import string
from functools import wraps
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import smtplib
import threading
from flask import jsonify
from keybert import KeyBERT
import json
import datetime
from datetime import timedelta
import random
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from transformers import pipeline