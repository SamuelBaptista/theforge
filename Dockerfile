FROM python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Copy the application code
COPY . .

# Install uv
RUN pip install --upgrade pip
RUN pip install uv

# Create and activate a uv environment
RUN uv sync