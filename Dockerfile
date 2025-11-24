# Use a minimal Python image
FROM python:3.12-slim

# Set a working directory inside the container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install pip packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the script
COPY chi.py .

# Set default command to run your script
CMD ["python", "-u", "chi.py"]