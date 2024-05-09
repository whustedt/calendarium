# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Copy the app directory contents into the container at /app
COPY app app

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV FLASK_APP=app:app
ENV PYTHONPATH=/app

# Run app.py when the container launches
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
