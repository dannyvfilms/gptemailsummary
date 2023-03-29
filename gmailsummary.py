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

# OpenAI API parameters
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
CUSTOM_PROMPT = os.environ.get('CUSTOM_PROMPT')
OPENAI_ENGINE = os.environ.get('OPENAI_ENGINE')
OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS'))
OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE'))

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
        
        # Print the authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        print(f"Please visit this URL to authorize the app: {auth_url}", flush=True)
        

    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Create a Gmail service instance
gmail_service = build('gmail', 'v1', credentials=creds)

# List that will store the latest fetched emails
latest_emails = []

def fetch_latest_emails():
    # Fetch a list of messages matching the query, and extract a list of messages from the results, or an empty list if none were found
    global latest_emails
    query = "is:unread -category:spam"
    results = gmail_service.users().messages().list(userId='me', q=query, maxResults=20).execute()   
    messages = results.get('messages', [])   

    # Initialize an empty list to store the latest emails
    latest_emails = []   

    # Fetch the full message details and extract label IDs and message headers
    for message in messages:
        msg = gmail_service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        labels = msg.get("labelIds", [])
        headers = msg['payload']['headers']

        if 'UNREAD' in labels:
            payload = msg['payload']
            parts = payload.get("parts")
            decoded_data = None

            # Extract the subject from the headers before processing the parts
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')

            # Initialize decoded_data variable for each message
            decoded_data = None

            # Extract the data from the first part, or the payload itself if there are no parts
            if parts:
                for part in parts:
                    content_type = part.get("mimeType", "")
                    file_data = part.get("body", {}).get("data")

                    if file_data:
                        file_data = file_data.replace("-", "+").replace("_", "/")
                        decoded_file_data = base64.b64decode(file_data).decode("utf-8")

                    # If 'multipart/alternative' content type is found, process the subparts
                    if 'multipart/alternative' in content_type:
                        sub_parts = part.get("parts", [])
                        for sub_part in sub_parts:
                            sub_content_type = sub_part.get("mimeType", "")
                            if 'text/plain' in sub_content_type:
                                file_data = sub_part.get("body", {}).get("data")
                                if file_data:
                                    file_data = file_data.replace("-", "+").replace("_", "/")
                                    decoded_data = base64.b64decode(file_data).decode("utf-8")
                                    break
                    elif 'text/calendar' in content_type:
                        decoded_data = decoded_file_data
                        break
            else:
                file_data = payload.get("body", {}).get("data")
                if file_data:
                    file_data = file_data.replace("-", "+").replace("_", "/")
                    decoded_data = base64.b64decode(file_data).decode("utf-8")

            if file_data:   
                file_data = file_data.replace("-", "+").replace("_", "/")   
                decoded_data = base64.b64decode(file_data)   
                if isinstance(decoded_data, bytes):   
                    decoded_data = decoded_data.decode("utf-8")   

            # Check if the message is a calendar event
            sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
            is_calendar_event = False
            event_details = ""

            if parts:
                for part in parts:
                    content_type = part.get("mimeType", "")
                    if 'text/calendar' in content_type:
                        is_calendar_event = True
                        file_data = part.get("body", {}).get("data")
                        break
            else:
                content_type = payload.get("mimeType", "")
                if 'text/calendar' in content_type:
                    is_calendar_event = True
                    file_data = payload.get("body", {}).get("data")

            if is_calendar_event:
                sender = 'Calendar'

                if file_data:
                    file_data = file_data.replace("-", "+").replace("_", "/")
                    decoded_data = base64.b64decode(file_data)
                    event_details = decoded_data.decode('utf-8') if isinstance(decoded_data, bytes) else decoded_data
            else:
                # If the message body is empty or contains no content, set a default value
                if not decoded_data:
                    decoded_data = "No content"
                event_details = decoded_data


            # Create a dictionary with email details
            mail_data = {
                'id': msg['id'],
                'subject': subject,  # Use the extracted subject
                'from': sender,
                'body': event_details,
                'internalDate': int(msg['internalDate'])
            }

            # Add the email details to the latest emails list, stopping the loop if the maximum number of emails has been fetched
            latest_emails.append(mail_data)   
            if len(latest_emails) >= 10:
                break

    # Sort the emails by internal date (oldest first)
    sorted_emails = sorted(latest_emails, key=lambda email: email['internalDate'])

    # Update the latest_emails global variable
    latest_emails = sorted_emails
                
    # Print the latest_emails list to the terminal
    print("\n" + "#" * 45 + "\n    Latest Emails Fetched:   \n" + "#" * 45 + "\n")
    print(f"{latest_emails}")


@app.route('/fetch_emails', methods=['GET'])
def fetch_emails():
    fetch_latest_emails()
    return jsonify(latest_emails)

def mark_emails_read(email_ids):
    # Marks a list of email IDs as read using the Gmail API.
    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)

    for email_id in email_ids:
        try:
            service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            print(f"Marked email {email_id} as read.")
        except Exception as e:
            print(f"An error occurred while marking email {email_id} as read: {e}")

def remove_html_and_links(text):
    # Remove unwanted HTML code
    text = re.sub('<table.*?</table>', '', text, flags=re.DOTALL)
    
    # Remove HTML tags
    text = re.sub('<[^<]+?>', '', text)

    # Remove links
    text = re.sub(r'http\S+', '', text)

    # Remove CSS styles
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', '', text, flags=re.DOTALL)

    # Remove JavaScript code
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)

    # Remove comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Remove consecutive whitespace characters
    text = re.sub('\s+', ' ', text)

    # Remove font code and Unicode code
    text = re.sub(r'(@font-face.*?;})', '', text, flags=re.DOTALL)
    text = re.sub(r'unicode-range:.*?;', '', text)

    # Remove unwanted code
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Remove blocks of code like &nbsp;&zwnj;&nbsp;&zwnj;...
    text = re.sub(r'(&\w+;)*[\u200b\u200c]*[\u00a0\u200b]*', '', text)

    # Remove code blocks
    text = re.sub(r'{[^{}]*}', '', text, flags=re.DOTALL)
    
    # Remove single words that begin with a period, asterisk, hash, hyphen, colon, or at symbol
    matches = list(re.finditer(r'(\s|^)(\.|\*|#|-|:|@)[^\s]+', text))
    if matches:
        offset = 0
        for match in matches:
            start, end = match.span()
            text = text[:start - offset] + text[end - offset:]
            offset += end - start

    # Remove extra spaces and multiple consecutive newline characters
    text = re.sub('\s+', ' ', text)
    text = re.sub('\n{2,}', '\n', text)

    return text.strip()

@app.route('/get_emails_summary', methods=['POST'])
def get_emails_summary():
    # Fetch the latest emails
    fetch_latest_emails()

    # Get the list of email IDs from the request
    email_ids_string = request.form.get('ids')

    # Split the email IDs string into a list of email IDs
    email_ids = email_ids_string.replace('ids[]=', '').strip('"').split('","')

    # Print the received email IDs
    print(f"Received email IDs: {email_ids}", flush=True)

    # Find the emails with the given ids in the latest_emails list
    emails = [e for e in latest_emails if e['id'] in email_ids and e.get('subject', '') != 'No subject' and e.get('content', '') != 'No content']

    # Concatenate the email content
    email_content = ""
    for i, email in enumerate(emails):
        email_content += f"Email {i + 1}:\nSubject: {email['subject']}\nFrom: {email['from']}\n\n{email['body']}\n\n"

    # Remove HTML and links from email content
    email_content = remove_html_and_links(email_content)

    # Generate the prompt for the emails
    prompt = f"{CUSTOM_PROMPT}\n\n{email_content}"

    # Print the prompt to the console
    print("\n" + "#" * 45 + "\n    Generated Prompt:   \n" + "#" * 45 + "\n", flush=True)
    print(prompt, flush=True)

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

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        response_json = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to OpenAI API: {e}", flush=True)
        return jsonify({"error": "Failed to connect to OpenAI API."})
    except ValueError as e:
        print(f"Error parsing OpenAI API response: {e}", flush=True)
        return jsonify({"error": "Failed to parse OpenAI API response."})

    try:
        response_json = response.json()
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return jsonify({"error": str(e)})

    print("\n" + "#" * 45 + "\n    OpenAI Response Payload:   \n" + "#" * 45 + "\n", flush=True)
    print(response_json, flush=True)

    if 'error' in response_json:
        print(f"OpenAI API error: {response_json['error']['message']}", flush=True)
        return jsonify({"error": response_json["error"]["message"]})

    try:
        summary = response_json["choices"][0]["message"]["content"].strip()
    except KeyError:
        print("Error extracting summary from OpenAI API response.", flush=True)
        return jsonify({"error": "Failed to extract summary from OpenAI API response."})
    
    # Mark the emails as read
    print("\n" + "#" * 45 + "\n    Marking emails as read.   \n" + "#" * 45 + "\n", flush=True)
    try:
        mark_emails_read(email_ids)
    except Exception as e:
        print(f"Error marking emails as read: {e}", flush=True)

    # Return the summary as plain text instead of JSON
    print("\n" + "#" * 45 + "\n    OpenAI Response:   \n" + "#" * 45 + "\n", flush=True)
    print(summary, flush=True)
    return jsonify({"summary": summary})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337)

