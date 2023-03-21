# Install required components
# sudo pip3 install flask google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client openai requests

from flask import Flask, jsonify, request
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

app = Flask(__name__)

# OpenAI API parameters
OPENAI_API_KEY = ""
CUSTOM_PROMPT = "Pretend to be a friendly assistant / motivational coach to someone that you know really well. Their name is Daniel, and they have just asked if there are any noteworthy new emails. Respond providing relevant summaries and if there are any important details or followups needed for each of the emails without just reading them out. Maybe slip in a joke if possible. Try to be observant of all the details in the data to come across as observant and emotionally intelligent as you can. Don't ask for a followup or if they need anything else. The emails are numbered below. Do not include the email numbers in your response. Don't include emojis in your response."
OPENAI_ENGINE = "gpt-4"
OPENAI_MAX_TOKENS = 500
OPENAI_TEMPERATURE = 0.7

# Set up OpenAI API credentials
openai.api_key = OPENAI_API_KEY

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

    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Create a Gmail service instance
gmail_service = build('gmail', 'v1', credentials=creds)

# List that will store the latest fetched emails
latest_emails = []

def fetch_latest_emails():
    global latest_emails
    query = "is:unread category:primary"
    results = gmail_service.users().messages().list(userId='me', q=query, maxResults=20).execute()
    messages = results.get('messages', [])

    latest_emails = []

    for message in messages:
        msg = gmail_service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        labels = msg.get("labelIds", [])
        headers = msg['payload']['headers']

        if 'UNREAD' in labels and 'CATEGORY_PERSONAL' in labels:
            payload = msg['payload']
            parts = payload.get("parts")

            data = parts[0] if parts else payload
            file_data = data.get("body", {}).get("data")
            if file_data:
                file_data = file_data.replace("-", "+").replace("_", "/")
                decoded_data = base64.b64decode(file_data)
            else:
                decoded_data = "No content"

            mail_data = {
                'id': msg['id'],
                'subject': next((header['value'] for header in headers if header['name'] == 'subject'), 'No Subject'),
                'from': next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender'),
                'body': decoded_data.decode("utf-8"),
                'internalDate': int(msg['internalDate'])  # Add the internal date to the mail_data dictionary
            }
            latest_emails.append(mail_data)
            if len(latest_emails) >= 10:
                break

    # Sort the emails by internal date (oldest first)
    sorted_emails = sorted(latest_emails, key=lambda email: email['internalDate'])

    # Update the latest_emails global variable
    latest_emails = sorted_emails
                
    # Print the latest_emails list to the terminal
    print(f"Latest emails fetched: {latest_emails}")

@app.route('/fetch_emails', methods=['GET'])
def fetch_emails():
    fetch_latest_emails()
    return jsonify(latest_emails)

def mark_emails_unread(email_ids):
    """Marks a list of email IDs as unread using the Gmail API."""
    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)

    for email_id in email_ids:
        try:
            service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            print(f"Marked email {email_id} as unread.")
        except Exception as e:
            print(f"An error occurred while marking email {email_id} as unread: {e}")

@app.route('/get_emails_summary', methods=['POST'])
def get_emails_summary():
    # Fetch the latest emails
    fetch_latest_emails()

    # Get the list of email IDs from the request
    email_ids_string = request.form.get('ids')

    # Split the email IDs string into a list of email IDs
    email_ids = email_ids_string.replace('ids[]=', '').strip('"').split('","')

    # Print the received email IDs
    print(f"Received email IDs: {email_ids}")

    # Find the emails with the given ids in the latest_emails list
    emails = [e for e in latest_emails if e['id'] in email_ids]
    
    # Mark the emails as unread
    mark_emails_unread(email_ids)

    # Concatenate the email content
    email_content = ""
    for i, email in enumerate(emails):
        email_content += f"Email {i + 1}:\nSubject: {email['subject']}\nFrom: {email['from']}\n\n{email['body']}\n\n"

    # Generate the prompt for the emails
    prompt = f"{CUSTOM_PROMPT}\n\n{email_content}"

    # Print the prompt to the console
    print("Generated prompt:")
    print(prompt)

    # Generate a summary of the emails using the OpenAI API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    data = {
        "model": OPENAI_ENGINE,
        "messages": [
            {"role": "system", "content": prompt},
        ],
        "max_tokens": OPENAI_MAX_TOKENS,
        "n": 1,
        "temperature": OPENAI_TEMPERATURE,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data,
    )

    response_json = response.json()
    print(response_json)

    if 'error' in response_json:
        print(f"Error: {response_json['error']['message']}")
        return jsonify({"error": response_json["error"]["message"]})

    summary = response_json["choices"][0]["message"]["content"].strip()

    # Return the summary as plain text instead of JSON
    return summary

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337)