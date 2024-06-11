FROM python:3.8-slim

# Install necessary packages
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium-browser \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install selenium

# Copy the script into the container
COPY your_script.py /your_script.py

# Command to run the script
CMD ["python", "/index.py"]
