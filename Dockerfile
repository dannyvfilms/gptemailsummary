# Use an official Python runtime as a parent image
FROM python:3.8-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-utils \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        boxes && \
    rm -rf /var/lib/apt/lists/*

# Install packages
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 1337 available to the world outside this container
EXPOSE 1337

# Create /config directory and set it as a volume
RUN mkdir /config
VOLUME ["/config"]

# Define environment variable
ENV OPENAI_API_KEY=""
ENV CUSTOM_PROMPT="Pretend to be a friendly assistant to someone that you know really well. Their name is Daniel, and they have just asked if there are any noteworthy new emails. Respond providing relevant summaries and if there are any important details or followups needed for each of the emails without just reading them out. Maybe slip in a joke if possible, but only if you can make it relate to the content. Give a higher priority to human conversations over notifications or newsletters. Try to be observant of all the details in the data to come across as observant and emotionally intelligent as you can. Don't ask for a followup or if they need anything else. The emails to summarize are included below. Don't include emojis in your response. Write the response in a way that works best spoken, not written. Don't read out URLs or two-factor authentication codes."
ENV OPENAI_ENGINE="gpt-4"
ENV OPENAI_MAX_TOKENS=1000
ENV OPENAI_TEMPERATURE=0.7
ENV EMAIL_MAXCHARACTERS=25000
ENV EMAIL_MAXEMAILS=10
ENV EMAIL_VARIABLEQUANTITY=true
ENV PYTHONUNBUFFERED 1

# Run app.py when the container launches
CMD ["python", "gmailsummary.py"]
