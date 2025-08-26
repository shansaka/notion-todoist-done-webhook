from fastapi import FastAPI, Request
import requests
from datetime import datetime, timezone
import os

app = FastAPI()

# -----------------------------
# Credentials
# -----------------------------
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# -----------------------------
# Helper Functions
# -----------------------------
def find_notion_page_by_todoist_id(todoist_id):
    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(query_url, headers=NOTION_HEADERS, json={
        "filter": {"property": "Todoist ID", "rich_text": {"equals": str(todoist_id)}}
    })
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return None
    return results[0]

def mark_notion_task_done(page_id):
    data = {
        "properties": {
            "Done": {"checkbox": True},
            "Last Sync Time": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
        }
    }
    response = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=NOTION_HEADERS, json=data)
    response.raise_for_status()
    return response.json()

# -----------------------------
# Webhook Endpoint
# -----------------------------
@app.post("/todoist-webhook")
async def todoist_webhook(request: Request):
    payload = await request.json()
    task_id = payload.get("task_id")
    if not task_id:
        return {"status": "error", "message": "task_id missing"}

    try:
        page = find_notion_page_by_todoist_id(task_id)
        if not page:
            return {"status": "error", "message": f"No Notion task found for Todoist ID {task_id}"}

        page_id = page["id"]
        mark_notion_task_done(page_id)
        return {"status": "success", "message": f"Task {task_id} marked done in Notion"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -----------------------------
# Run locally (optional)
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
