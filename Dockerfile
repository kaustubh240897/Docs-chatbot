# Use the official Python 3.12 base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /opt

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application into the container
COPY . .

ENV PYTHONUNBUFFERED 1

# Set the command to run the bot script
CMD ["python3", "-u", "run_bots.py"]
