FROM python:3.11-bullseye

# get portaudio and ffmpeg
RUN apt-get update \
        && apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev libasound-dev libsndfile1-dev -y
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

WORKDIR /code

# Copy requirements and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py /code/main.py
COPY speller_agent.py /code/speller_agent.py
COPY memory_config.py /code/memory_config.py
COPY events_manager.py /code/events_manager.py
COPY config.py /code/config.py
COPY instructions.txt /code/instructions.txt

# Copy session scheduling system files
COPY firebase_config.py /code/firebase_config.py
COPY session_agent.py /code/session_agent.py
COPY outbound_session_calls.py /code/outbound_session_calls.py
COPY appointment_agent.py /code/appointment_agent.py
COPY appointment_scheduler.py /code/appointment_scheduler.py
COPY outbound_appointment_calls.py /code/outbound_appointment_calls.py

# Create necessary directories
RUN mkdir -p /code/call_transcripts
RUN mkdir -p /code/db

# Copy the utils directory (and its contents) into the container
COPY ./utils /code/utils

# Use port 8000 to match render.yaml
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]