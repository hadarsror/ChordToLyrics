import requests
import time

# 1. Upload the file
with open("C:\\Users\\hadar\\Downloads\\Ego Death At A Bachelorette Party\\Hayley Williams - Hard.mp3", "rb") as f:
    response = requests.post("http://127.0.0.1:8000/upload", files={"file": f})
    task_id = response.json()["task_id"]
    print(f"Task started! ID: {task_id}")

# 2. Poll for the result
while True:
    res = requests.get(f"http://127.0.0.1:8000/status/{task_id}")
    data = res.json()
    status = data["status"]

    if status == "SUCCESS":
        print("\n--- CHORD SHEET ---\n")
        print(data["result"])
        break
    elif status == "FAILURE":
        print("Processing failed.")
        break

    print(f"Status: {status}... (waiting 5s)")
    time.sleep(5)
