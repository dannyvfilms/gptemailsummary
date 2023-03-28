# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 1337 available to the world outside this container
EXPOSE 1337

# Define environment variable
ENV OPENAI_API_KEY=""
ENV CUSTOM_PROMPT="Pretend to be a friendly assistant to someone that you know really well. Their name is Daniel, and they have just asked if there are any noteworthy new emails. Respond providing relevant summaries and if there are any important details or followups needed for each of the emails without just reading them out. Maybe slip in a joke if possible. Try to be observant of all the details in the data to come across as observant and emotionally intelligent as you can. Don't ask for a followup or if they need anything else. The emails to summarize are included below. Don't include emojis in your response. Don't write fictional emails. Write the response in a way that works best spoken, not written. If this is the last sentence of the prompt, simply tell the user that there were no emails to summarize right now."
ENV OPENAI_ENGINE="gpt-4"
ENV OPENAI_MAX_TOKENS=1000
ENV OPENAI_TEMPERATURE=0.7

# Run app.py when the container launches
CMD ["python", "gmailsummary.py"]
