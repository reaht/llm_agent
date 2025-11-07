import datetime, os

def log_text(text, filename="session.log"):
    os.makedirs("data/logs", exist_ok=True)
    path = os.path.join("data/logs", filename)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.datetime.now()}]\n{text}\n")