# Install required components
from flask import Flask, jsonify, request, render_template
import google.auth
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import httplib2
from httplib2 import Http
import openai
import os
import pickle
import logging
import requests
import base64
import configparser
import re
import logging
import subprocess
import textwrap
import threading
import google.auth.transport.requests as tr_requests

# Enable debug level logging for httplib2
httplib2.debuglevel = 1
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

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
# Check if token.pickle file exists
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # If not, open the authorization URL in the browser
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        auth_url, _ = flow.authorization_url(prompt='consent')
        print(f"Please visit this URL to authorize the app: {auth_url}", flush=True)

    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Create a Gmail service instance
gmail_service = build('gmail', 'v1', credentials=creds)

# List that will store the latest fetched emails
latest_emails = []

# Variable that will store the total number of characters for emails
total_characters = 0
max_characters = int(os.environ.get('EMAIL_MAXCHARACTERS'))

## Commenting out for now. Possible port conflict stops core functionality.
## Route to serve the index.html file at the root URL
#@app.route('/')
#def index():
#    return render_template('index.html')
#
## Start the Flask app on host 0.0.0.0 and port 1337
#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=1337)


# Add the count_characters function
def count_characters(text):
    global total_characters
    char_count = len(text)
    total_characters += char_count
    print(f"Character count for this email: {char_count}", flush=True)
    print(f"Total characters processed so far: {total_characters}", flush=True)
    
def format_text_with_boxes(text, design='shell', padding='a1l2'):
    echo_process = subprocess.Popen(['echo', text], stdout=subprocess.PIPE)
    boxes_process = subprocess.Popen(['boxes', '-d', design, '-p', padding], stdin=echo_process.stdout, stdout=subprocess.PIPE, text=True)

    echo_process.stdout.close()  # Allow echo_process to receive a SIGPIPE if boxes_process exits.
    output = boxes_process.communicate()[0]
    echo_process.wait()
    return output

def fetch_latest_emails():
    global latest_emails, total_characters
    query = "is:unread -category:spam"

    # Initialize an empty list to store the latest emails
    latest_emails = []

    # Initialize a variable to store the total character count
    total_characters = 0
    
    # Read environment variables
    variable_quantity = os.environ.get("EMAIL_VARIABLEQUANTITY", "false").lower() == "true"
    max_emails = int(os.environ.get("EMAIL_MAXEMAILS", 50))

    # Start the while loop
    print("Starting while loop", flush=True)

    # Fetch the full message details and extract label IDs and message headers
    while (variable_quantity and total_characters < max_characters) or len(latest_emails) < max_emails:
        
        # Calculate the remaining emails to fetch
        remaining_emails = max_emails - len(latest_emails)
        results = gmail_service.users().messages().list(userId='me', q=query, maxResults=min(50, remaining_emails) if not variable_quantity else 50).execute()
        messages = results.get('messages', [])

        # Add a log statement to print the number of messages being fetched
        print(f"Fetched {len(messages)} messages", flush=True)

        # If no messages are found, break out of the loop
        if not messages:
            break 

        # Fetch the full message details and extract label IDs and message headers
        for message in messages:
            print("Processing message: ", message['id'], flush=True)
            msg = gmail_service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            labels = msg.get("labelIds", [])
            headers = msg['payload']['headers']
            
            # Extract sender and subject from the headers
            sender, subject = "", ""
            for header in headers:
                if header["name"] == "From":
                    sender = header["value"]
                elif header["name"] == "Subject":
                    subject = header["value"]

            # Add a log statement to print the number of characters for each email
            decoded_body = remove_html_and_links(msg['snippet'])
            decoded_data = f"Sender: {sender}\nSubject: {subject}\nBody: {decoded_body}"
            count_characters(decoded_data)
            print(f"Character count for this email: {len(decoded_data)}", flush=True)

            # Add a log statement to print the total number of characters processed so far
            print(f"Total characters processed so far: {total_characters}", flush=True)

            if 'UNREAD' in labels:
                payload = msg['payload']
                parts = payload.get("parts")
                decoded_data = None

            # Extract the subject from the headers before processing the parts
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')

            # Initialize decoded_data variable for each message
            decoded_data = ""

            # Extract the data from the first part, or the payload itself if there are no parts
            if parts:
                decoded_file_data = None
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

            # Call the count_characters function and pass the decoded_data
            decoded_data = remove_html_and_links(decoded_data)

            # Create a dictionary with email details
            mail_data = {
                'id': msg['id'],
                'subject': subject,  # Use the extracted subject
                'from': sender,
                'body': event_details,
                'internalDate': int(msg['internalDate'])
            }

            # Add the email details to the latest emails list, breaking the loop if the maximum number of characters has been reached
            latest_emails.append(mail_data)
            
            # Call the count_characters function and pass the decoded_data
            count_characters(decoded_data)

            if total_characters >= max_characters:
                break

    # Sort the emails by internal date (oldest first)
    sorted_emails = sorted(latest_emails, key=lambda email: email['internalDate'])

    # Update the latest_emails global variable
    latest_emails = sorted_emails
                
    # Print the latest_emails list to the terminal
    print("\n" + "#" * 45 + "\n    Latest Emails Fetched:   \n" + "#" * 45 + "\n", flush=True)
    print(f"{latest_emails}", flush=True)
    
    return latest_emails

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
    # Convert empty strings
    if text is None:
        text = ""
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

    # Remove a:visited and a:link
    text = re.sub(r'a:visited|a:link', '', text)

    # Remove patterns like a[class="btn"], div[class="column"], etc.
    text = re.sub(r'\w+\[class="[^"]+"\]', '', text)

    # Remove multiple consecutive comment tags
    text = re.sub(r'(<!--\s*)+', '', text)

    # Remove specific words followed by a potential comma
    text = re.sub(r'\b(p|span|font|td|div|li|blockquote|table|img|h1|h2|h3|h4|h5|ol|ul|th)(,)?\b', '', text)

    # Remove consecutive commas
    text = re.sub(r'(,\s*){2,}', ', ', text)

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
def get_emails_summary_route():
    # Fetch the latest emails
    latest_emails = fetch_latest_emails()

    # Call the get_emails_summary function with the latest_emails list
    return get_emails_summary(latest_emails)

def mark_emails_read_in_background(email_ids):
    try:
        mark_emails_read(email_ids)
    except Exception as e:
        print(f"Error marking emails as read: {e}", flush=True)

def get_emails_summary(latest_emails):
    # Get the list of email IDs from the request
    email_ids_string = request.form.get('ids')

    # Split the email IDs string into a list of email IDs
    email_ids = email_ids_string.replace('ids[]=', '').strip('"').split('","')

    # Print the received email IDs
    print(f"Received email IDs: {email_ids}", flush=True)

    # Find the emails with the given ids in the latest_emails list
    emails = [e for e in latest_emails if e['id'] in email_ids and e.get('subject', '') != 'No subject' and e.get('content', '') != 'No content']

    # Get the number of emails summarized
    num_emails = len(emails)

    # Get the unique senders' names
    unique_senders = set([e['from'] for e in emails])
    unique_senders_str = ', '.join(unique_senders)
    
    # Wrap the unique senders' string to 150 characters
    unique_senders_str = textwrap.fill(unique_senders_str, width=150)

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

    # Extract token usage from response JSON
    usage = response_json['usage']
    prompt_tokens = usage['prompt_tokens']
    completion_tokens = usage['completion_tokens']
    total_tokens = usage['total_tokens']

    # Return the summary as plain text instead of JSON
    print("\n" + "#" * 45 + "\n    OpenAI Response:   \n" + "#" * 45 + "\n", flush=True)
    print(summary, flush=True)
    
    # Wrap the summary string to 150 characters per line
    summary_wrapped = textwrap.fill(summary, width=150)

    final_summary = format_text_with_boxes(f"Run Completed Successfully! \n \nAmount: {num_emails}\nSenders: {unique_senders_str}\n \nTokens Sent: {prompt_tokens}\nTokens Received: {completion_tokens}\nTotal Tokens: {total_tokens}\n \nResponse: \n{summary_wrapped}")
    print(final_summary)
    
    statistics = f"Summarized {num_emails} Emails. \n \nTokens Sent: {prompt_tokens}\nTokens Received: {completion_tokens}\nTotal Tokens: {total_tokens} \n \n Senders: {unique_senders_str}"
    
    # Start a separate thread to mark the emails as read
    mark_emails_read_thread = threading.Thread(target=mark_emails_read_in_background, args=(email_ids,))
    mark_emails_read_thread.start()

    return jsonify({"summary": summary, "statistics": statistics})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337)

