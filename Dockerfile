# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the timezone environment variable
ENV TZ=Europe/Berlin

# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app directory contents into the container at /app
COPY app app
COPY migrations migrations
COPY entrypoint.sh entrypoint.sh

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONPATH=/app

# Make the entrypoint script executable and run it
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
