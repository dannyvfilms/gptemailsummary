# GPT Email Summary
Uses Gmail and OpenAI's APIs to summarize emails through a python server and iOS Shortcut. This usecase was inspired by Justin Alvey's post on Twitter, which I was unable to find the source code for, and decided to code manually through ChatGPT. https://t.co/TLIoW48rLg

This code uses the Gmail API to call for the latest unread emails from your inbox. It uses HTML and code filtering to avoid hitting OpenAI's token limit for marketing based emails. The contents of those emails are given to OpenAI with pre-written instructions (By Justin Alvey with minor additions) to summarize the emails. That output is given to an iOS Shortcut, which is used on MacOS or iOS to start the process and return the result. Siri will read out the summary, or code has been provided in the Shortcut to integrate with ElevenLabs. All emails will also be marked as read after successfully being sent to OpenAI.

This process requires the python script to be running constantly on a home computer or Raspberry Pi. It has been packaged as a Docker container to be able to run automatically on startup. To run this script outside of your home network, it will also require a (free) Cloudflare Tunnel or something similar. See the instructions below.

## Requirements before Installation:

### Google Cloud Console
1. Watch the Google Cloud Console.mp4 video included in this repo.
2. Go to console.cloud.google.com on your web browser.
3. Click on the "Select a Project" dropdown menu at the top of the page and click "New Project" to create a new project.
4. In the "New Project" window, enter a name for your project, then click "Create".
5. After your project has been created, you will need to enable APIs and services for it. To do this, click on the "Navigation menu" icon (three horizontal lines) in the top-left corner, then click "APIs & Services" and select "Dashboard".
6. Click on "+ ENABLE APIS AND SERVICES" and search for "Gmail API". Click on "Gmail API" in the search results and click the "Enable" button.
7. Once the API is enabled, you will need to create credentials to access it. Click on "Create Credentials".
8. Select the Gmail API, and choose User Data as the type of data you will be accessing.
9. Provide a name, support email, and developer contact information for the OAuth consent screen.
10. Add the scope "Gmail API …/auth/gmail.modify". Click the checkbox for the scope, then "Save and continue".
11. Choose "Desktop app" as the application type and give your OAuth client ID a name, then click "Create".
12. Next, you will need to download your OAuth client ID credentials. Click on "Download" to download the credentials as a JSON file. Rename the file to "credentials.json" and save it in the directory of your Python script.
13. Now, you need to set up the OAuth consent screen. Click on "Configure consent screen" and select "External" as the user type.
14. Add a test user to the OAuth consent screen by clicking on "Add Users" and entering a test email address.

### OpenAI
1. Go to platform.openai.com on your web browser.
2. Create an account by clicking on the "Sign up" button at the top right corner of the page, then follow the prompts to create your account.
3. After your account has been created, click on your account profile at the top-right corner of the page and select "API Keys".
4. Click on "+ Create new secret key" to create a new API key.
5. Copy the API key that appears on the screen and save it in a safe place. This API key is required to authenticate your Python script when making requests to OpenAI's API.

### ElevenLabs
1. Go to https://beta.elevenlabs.io and click your Profile
2. Your API Key is visible there.
3. Go to https://api.elevenlabs.io/docs with your API Key to retrieve your Voice ID using Get Voices
4. Save your API Key and Voice ID for use in the iOS Shortcut.

### iOS Shortcut
1. The iOS Shortcut is the method used to trigger the email summary from your iPhone or Mac. Frankly I have no clue how to control this from Android or Windows, as my knowledge of Python is non-existant and I used ChatGPT to code this.
2. https://www.icloud.com/shortcuts/9d5749b5c54d4162a7a47be6f862cb25
3. The Shortcut includes setup instructions. Enter the port of the computer running this script, or the Cloudflare Tunnel URL. This app uses ```port:1337```

### Cloudflare Tunnel
1. To access your Python Server outside of your home (or any other self-hosted applications you may have running) I recommend using a Cloudflare tunnel as described by Crosstalk Solutions
2. https://www.youtube.com/watch?v=ZvIdFs3M5ic
3. For Home Assistant users, the Cloudflare tunnel can be run as an add-on to your installation
4. https://www.youtube.com/watch?v=xXAwT9N-7Hw

## Script Installation
1. Download GmailSummary and put it in a folder of your choice
2. Create Google Authentication pickle: Set your terminal directory with ```cd /home/pi/Documents/GmailSummary```, then run ```python3 generatepickle.py``` to prompt a Google Login page. Allow permission to use the app, and then note the addition of token.pickle to your directory once successful.
3. Install Docker: ```curl -sSL https://get.docker.com | sh```
4. Install Portainer, a GUI interface to manage Docker containers and Environment variables
```sudo docker run -d -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce```
5. Access Portainer and create login to view Docker containers: ```http://localhost:9000```
6. Build the Docker Container: Set your terminal directory with ```cd /home/pi/Documents/GmailSummary```, then run ```sudo docker build -t gmailsummary .``` to build the Docker Container.
7. Modify the following command. Place your OpenAI API Key inside the quotation marks of ```your-api`key```. Choose "gpt-4" or "gpt3.5-turbo" and use that as OPENAI_ENGINE parameter. Example:
```sudo docker run -d --name gmailsummary -p 1337:1337 --restart unless-stopped -e OPENAI_API_KEY="your-api-key" -e OPENAI_ENGINE="gpt-4" gmailsummary```
8. View Container Logs in Portainer: Home > local > Containers > GmailSummary > Quick actions: Logs
9. Run the Script: ```https://www.icloud.com/shortcuts/9d5749b5c54d4162a7a47be6f862cb25```
10. Update Environment Variables: Home > local > Containers > GmailSummary > Duplicate/Edit > Env > Deploy the Container

## Planned Features
1. Support for multiple inboxes
2. WebUI (draft is in repo but incomplete)
3. Dynamically change quantity of emails to fill 90% of OpenAI Token Limit
4. Properly generate a pickle inside the Docker container

## Usage
Configure the following Environment Variables to change results as needed:
1. OPENAI_API_KEY = Default: ```""```. Your API Key from OpenAI.
2. OPENAI_ENGINE = Default: ```gpt-4```. Configure to use ```gpt-4```, ```gpt3.5-turbo```, or a different chat model. This variable should read "Model", will change at some point. 
3. OPENAI_MAX_TOKENS = Default: ```1000```. Use to set the maximum length of the return message. Drastically raising this may result in a 400 error (max tokens) depending on the size of the payload sent. 
4. OPENAI_TEMERATURE = Default: ```0.7```. Temperature controls response randomness and creativity.
5. CUSTOM_PROMPT = Default: 
```Pretend to be a friendly assistant to someone that you know really well. Their name is Daniel, and they have just asked if there are any noteworthy new emails. Respond providing relevant summaries and if there are any important details or followups needed for each of the emails without just reading them out. Maybe slip in a joke if possible. Try to be observant of all the details in the data to come across as observant and emotionally intelligent as you can. Don't ask for a followup or if they need anything else. The emails to summarize are included below. Don't include emojis in your response. Write the response in a way that works best spoken, not written. Don't read out URLs or two-factor authentication codes.```. Customize as needed depending on the content of your inbox. Make sure to update the name in the prompt.
6. EMAIL_MAXCHARACTERS = Default: ```25000```. Sets the maximum amount of characters for a payload to OpenAI when ```EMAIL_VARIABLEQUANTITY=true```. It was easier than calculating tokens, but less precise. Typically it's a 4:1 ratio of characters to tokens, with an 8,000 token limit between the sent and received tokens. A value of 28000 has resulted in a 400 error (max tokens) before, so I lowered the default.
7. EMAIL_MAXEMAILS = Default: ```10```. Sets the maximum amount of emails to use for a payload to OpenAI when ```EMAIL_VARIABLEQUANTITY=false```. This may be useful if you want to ask for more detail about your emails by focusing on a smaller set of data.
8. EMAIL_VARIABLEQUANTITY = Default: ```true```. Sets the script to use a character limit when true, or a fixed number of emails when false to create the OpenAI payload. This functionality is not fully coded, so expect ```true``` in V2 and ```false``` in V1 until a V3 release.
