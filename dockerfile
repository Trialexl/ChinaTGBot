# Use an official Python runtime as the base image
FROM python:3.9

# Create a working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt



# Run the application
CMD ["python","main.py"]