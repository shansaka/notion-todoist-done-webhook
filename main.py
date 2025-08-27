from fastapi import FastAPI, Request
import requests
from datetime import datetime, timezone
import os
import traceback

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
    print(f"[INFO] Searching Notion for Todoist ID: {todoist_id}", flush=True)
    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(query_url, headers=NOTION_HEADERS, json={
        "filter": {"property": "Todoist ID", "rich_text": {"equals": str(todoist_id)}}
    })

    if response.status_code != 200:
        print(f"[ERROR] Failed to query Notion: {response.text}", flush=True)
    response.raise_for_status()

    results = response.json().get("results", [])
    if not results:
        print(f"[WARN] No matching Notion page for Todoist ID: {todoist_id}", flush=True)
        return None

    print(f"[INFO] Found Notion page for Todoist ID: {todoist_id}", flush=True)
    return results[0]


def mark_notion_task_done(page_id):
    print(f"[INFO] Marking Notion task {page_id} as Done", flush=True)
    data = {
        "properties": {
            "Done": {"checkbox": True},
            "Last Sync Time": {"date": {"start": datetime.now(timezone.utc).isoformat()}}
        }
    }
    response = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=NOTION_HEADERS, json=data)

    if response.status_code != 200:
        print(f"[ERROR] Failed to update Notion task {page_id}: {response.text}", flush=True)
    response.raise_for_status()

    print(f"[INFO] Task {page_id} successfully updated in Notion", flush=True)
    return response.json()

# -----------------------------
# Webhook Endpoint
# -----------------------------
@app.post("/todoist-webhook")
async def todoist_webhook(request: Request):
    print("[INFO] Received webhook from Todoist", flush=True)
    try:
        payload = await request.json()
        print(f"[DEBUG] Webhook payload: {payload}", flush=True)

        task_id = payload.get("task_id")
        if not task_id:
            print("[ERROR] task_id missing from webhook payload", flush=True)
            return {"status": "error", "message": "task_id missing"}

        page = find_notion_page_by_todoist_id(task_id)
        if not page:
            msg = f"No Notion task found for Todoist ID {task_id}"
            print(f"[WARN] {msg}", flush=True)
            return {"status": "error", "message": msg}

        page_id = page["id"]
        mark_notion_task_done(page_id)
        success_msg = f"Task {task_id} marked done in Notion"
        print(f"[INFO] {success_msg}", flush=True)
        return {"status": "success", "message": success_msg}

    except Exception as e:
        error_msg = f"Exception occurred: {str(e)}"
        print(f"[ERROR] {error_msg}", flush=True)
        traceback.print_exc()
        return {"status": "error", "message": error_msg}

# -----------------------------
# Run locally (optional)
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    print("[INFO] Starting FastAPI app...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
