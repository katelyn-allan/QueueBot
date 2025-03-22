# Configure the base image
FROM python:3.11-alpine

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "core.py"]