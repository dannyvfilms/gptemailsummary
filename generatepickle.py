# Install required components
from flask import Flask, jsonify, request, render_template
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery
from googleapiclient.discovery import build
import openai
import os
import pickle
import logging
import requests
import base64
import configparser
import re

app = Flask(__name__)

## Commenting out for now. Possible port conflict stops core functionality.
## Route to serve the index.html file at the root URL
#@app.route('/')
#def index():
#    return render_template('index.html')
#
## Start the Flask app on host 0.0.0.0 and port 1337
#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=1337)

## OpenAI API parameters
#OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
#CUSTOM_PROMPT = os.environ.get('CUSTOM_PROMPT')
#OPENAI_ENGINE = os.environ.get('OPENAI_ENGINE')
#OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS'))
#OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE'))
#
## Set up OpenAI API credentials
#openai.api_key = OPENAI_API_KEY

# Set up Google API credentials
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Print the authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        print(f"Please visit this URL to authorize the app: {auth_url}", flush=True)
        

    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Create a Gmail service instance
gmail_service = build('gmail', 'v1', credentials=creds)

# List that will store the latest fetched emails
latest_emails = []

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337)

