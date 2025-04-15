# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Fly uses 8080 by default)
EXPOSE 8080

# Run the app
CMD ["python", "app.py"]
