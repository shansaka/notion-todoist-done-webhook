# Notion-Todoist Done Webhook

This project provides a simple webhook service to integrate Notion and Todoist, marking tasks as done in Todoist when triggered from Notion.

## Project Structure

- `main.py`: Main application logic for the webhook service.
- `requirements.txt`: Python dependencies required to run the project.
- `Dockerfile`: Containerization instructions for deploying the service with Docker.

## Features

- Receives webhook events (likely from Notion).
- Updates Todoist tasks as done based on received events.
- Can be deployed easily using Docker.

## Getting Started

### Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/shansaka/notion-todoist-done-webhook.git
   cd notion-todoist-done-webhook
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Usage

Run the webhook service locally:

```powershell
python main.py
```

Or build and run with Docker:

```powershell
# Build the Docker image
docker build -t notion-todoist-done-webhook .

# Run the container
# (You may need to set environment variables for API keys, etc.)
docker run -p 8000:8000 notion-todoist-done-webhook
```

## Configuration

- Set any required environment variables (e.g., Todoist API key, Notion integration token) as needed for your deployment.

## License

MIT

## Author

shansaka
