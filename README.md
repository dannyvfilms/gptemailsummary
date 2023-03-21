# GPT Email Summary
Uses Gmail and OpenAI's APIs to summarize emails through a python server and iOS Shortcut. This usecase was inspired by Justin Alvey's post on Twitter, which I was unable to find the source code for. https://t.co/TLIoW48rLg

This code uses the Gmail API to call for the latest unread emails from the personal section of your inbox. It avoids reading your entire inbox as marketing emails contain HTML code that will likely hit the token limit for OpenAI. The contents of those emails are then given to OpenAI with pre-written instructions (By Justin Alvey with minor additions) to summarize the emails. That output is given to the Shortcut you triggered the process with, and Siri will read out the summary. iOS Shortcuts exist that can use more advanced voices like those from Elevenlabs.

This process requires the python script to be running constantly on a home computer or Raspberry Pi. Once I figure out how to do that automatically I will update these instructions. To run this script outside of your home network, it will also require a (free) Cloudflare Tunnel or something similar. See the instructions below.

Installation:

Python Script
1. Download the python script from this repository
2. Run this command to download the required components to run the script:

```sudo pip3 install flask google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client openai requests```

3. Choose a folder to run this script in so you can point your terminal to it (e.g. ```Documents/ChatGPT/GmailSummary```)
4. Set your terminal to that folder: ```cd Documents/ChatGPT/GmailSummary```
5. To start the python server: ```python3 gmailsummary.py```
6. Start it later. You don't have everything you need yet.

iOS Shortcut
1. The iOS Shortcut is the method used to trigger the email summary from your iPhone or Mac. Frankly I have no clue how to control this from Android or Windows, as my knowledge of Python is non-existant and I used ChatGPT to code this.
2. https://www.icloud.com/shortcuts/61857d5f16b44c81819af2450b3ca0fc
3. The Shortcut includes setup instructions. Enter the port of the computer running this script, or the Cloudflare Tunnel URL. This app uses ```port:1337```
4. If this port conflicts with something you are using already, modify the port number with a text editor and save the gmailsummary.py file.

Cloudflare Tunnel
1. To access your Python Server outside of your home (or any other self-hosted applications you may have running) I recommend using a Cloudflare tunnel as described by Crosstalk Solutions
2. https://www.youtube.com/watch?v=ZvIdFs3M5ic

Google Cloud Console
1. Go to console.cloud.google.com on your web browser.
2. Click on the "Select a Project" dropdown menu at the top of the page and click "New Project" to create a new project.
3. In the "New Project" window, enter a name for your project, then click "Create".
4. After your project has been created, you will need to enable APIs and services for it. To do this, click on the "Navigation menu" icon (three horizontal lines) in the top-left corner, then click "APIs & Services" and select "Dashboard".
5. Click on "+ ENABLE APIS AND SERVICES" and search for "Gmail API". Click on "Gmail API" in the search results and click the "Enable" button.
6. Once the API is enabled, you will need to create credentials to access it. Click on "Create Credentials".
7. Select the Gmail API, and choose User Data as the type of data you will be accessing.
8. Provide a name, support email, and developer contact information for the OAuth consent screen.
9. Add the scope "Gmail API …/auth/gmail.modify". Click the checkbox for the scope, then "Save and continue".
10. Choose "Desktop app" as the application type and give your OAuth client ID a name, then click "Create".
11. Next, you will need to download your OAuth client ID credentials. Click on "Download" to download the credentials as a JSON file. Rename the file to "credentials.json" and save it in the directory of your Python script.
12. Now, you need to set up the OAuth consent screen. Click on "Configure consent screen" and select "External" as the user type.
13. Add a test user to the OAuth consent screen by clicking on "Add Users" and entering a test email address.

OpenAI
1. Go to platform.openai.com on your web browser.
2. Create an account by clicking on the "Sign up" button at the top right corner of the page, then follow the prompts to create your account.
3. After your account has been created, click on your account profile at the top-right corner of the page and select "API Keys".
4. Click on "+ Create new secret key" to create a new API key.
5. Copy the API key that appears on the screen and save it in a safe place. This API key is required to authenticate your Python script when making requests to OpenAI's API.
6. Edit the gmailsummary.py file in a text editor, and place your API Key inside the ```"empty quotation marks"``` next to ```OPENAI_API_KEY``` in the ```OpenAI API parameters``` section near the top of the document.
