from fastapi import FastAPI, Request, BackgroundTasks
import requests
from datetime import datetime, timezone
import os
import traceback
import uuid

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
def find_notion_page_by_todoist_id(todoist_id, req_id):
    print(f"[{req_id}] [INFO] Searching Notion for Todoist ID: {todoist_id}", flush=True)
    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(query_url, headers=NOTION_HEADERS, json={
        "filter": {"property": "Todoist ID", "rich_text": {"equals": str(todoist_id)}}
    })

    if response.status_code != 200:
        print(f"[{req_id}] [ERROR] Failed to query Notion: {response.text}", flush=True)
    response.raise_for_status()

    results = response.json().get("results", [])
    if not results:
        print(f"[{req_id}] [WARN] No matching Notion page for Todoist ID: {todoist_id}", flush=True)
        return None

    print(f"[{req_id}] [INFO] Found Notion page for Todoist ID: {todoist_id}", flush=True)
    return results[0]


def update_notion_done_status(page_id, done_status, req_id):
    print(f"[{req_id}] [INFO] Setting Done={done_status} for Notion task {page_id}", flush=True)
    data = {
        "properties": {
            "Done": {"checkbox": done_status},
            "Last Sync Time": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
        }
    }
    response = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=NOTION_HEADERS, json=data)
    if response.status_code != 200:
        print(f"[{req_id}] [ERROR] Failed to update Notion task {page_id}: {response.text}", flush=True)
    response.raise_for_status()
    print(f"[{req_id}] [INFO] Task {page_id} successfully updated in Notion", flush=True)


def process_webhook(payload, req_id):
    """Process Todoist webhook in background."""
    try:
        event_data = payload.get("event_data", {})
        task_id = event_data.get("id")
        event_name = payload.get("event_name", "unknown")
        task_url = event_data.get("url")
        print(f"[{req_id}] [DEBUG] Processing task_id={task_id}, event={event_name}, URL={task_url}", flush=True)

        if not task_id:
            print(f"[{req_id}] [ERROR] task_id missing in event_data", flush=True)
            return

        page = find_notion_page_by_todoist_id(task_id, req_id)
        if not page:
            print(f"[{req_id}] [WARN] No Notion task found for Todoist ID {task_id}", flush=True)
            return

        page_id = page["id"]

        # Determine Done status based on event
        if event_name == "item:completed":
            done_status = True
        elif event_name == "item:uncompleted":
            done_status = False
        else:
            print(f"[{req_id}] [INFO] Event {event_name} does not change Done status, skipping", flush=True)
            return

        # Update Notion task
        update_notion_done_status(page_id, done_status, req_id)

    except Exception as e:
        print(f"[{req_id}] [ERROR] Exception occurred: {str(e)}", flush=True)
        traceback.print_exc()


# -----------------------------
# Webhook Endpoint
# -----------------------------
@app.post("/todoist-webhook")
async def todoist_webhook(request: Request, background_tasks: BackgroundTasks):
    req_id = uuid.uuid4().hex[:6]  # unique request ID for logs
    print(f"[{req_id}] [INFO] Received webhook from Todoist", flush=True)

    try:
        payload = await request.json()
        print(f"[{req_id}] [DEBUG] Webhook payload: {payload}", flush=True)

        # process in background (avoid Todoist retries)
        background_tasks.add_task(process_webhook, payload, req_id)

        # immediately respond so Todoist doesn't retry
        return {"status": "ok", "req_id": req_id}

    except Exception as e:
        error_msg = f"Exception occurred: {str(e)}"
        print(f"[{req_id}] [ERROR] {error_msg}", flush=True)
        traceback.print_exc()
        return {"status": "error", "message": error_msg, "req_id": req_id}


# -----------------------------
# Run locally (optional)
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    print("[INFO] Starting FastAPI app...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
