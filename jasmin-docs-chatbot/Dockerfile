# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Git and other dependencies
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# Clone the repository to /tmp, and move part we need to /app
RUN git clone https://github.com/cedadev/ai-mini-projects /tmp/ai-mini-projects && \
    mv -f /tmp/ai-mini-projects/jasmin-docs-chatbot/* /app/ && \
    rm -fr /tmp/ai-mini-projects

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME World

# Run the application
CMD ["chainlit", "run", "app.py"]

