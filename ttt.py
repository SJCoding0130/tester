import os
import requests
from pathlib import Path
import subprocess
import time
import sys

# -----------------------------
# Wait until PHP server is ready
# -----------------------------
def wait_for_server(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code < 500:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.2)
    raise RuntimeError(f"PHP server did not start at {url} within {timeout}s")

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).parent.resolve()  # folder containing view.php
JSON_FOLDER = BASE_DIR / "json"
OUTPUT_BASE = BASE_DIR / "output"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Start PHP built-in server
# -----------------------------
php_process = subprocess.Popen(
    ["php", "-S", "localhost:8000"],
    cwd=BASE_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    wait_for_server("http://localhost:8000")
    print("PHP server is ready!")
except RuntimeError as e:
    stdout, stderr = php_process.communicate(timeout=5)
    print("PHP stdout:", stdout.decode(), file=sys.stderr)
    print("PHP stderr:", stderr.decode(), file=sys.stderr)
    php_process.terminate()
    raise e

# -----------------------------
# Endpoint URL
# -----------------------------
URL = "http://localhost:8000/view.php"

# -----------------------------
# Languages
# -----------------------------
LANGUAGES = ["Text", "English", "ChineseTraditional", "ChineseSimplified"]

# -----------------------------
# Process JSON files
# -----------------------------
json_files = sorted(JSON_FOLDER.glob("*.book.json"))

for file_path in json_files:
    print("="*40)
    print(f"Processing file: {file_path.name}")
    print("="*40)

    for lang in LANGUAGES:
        print(f"  : Language: {lang}")
        lang_label = "Japanese" if lang == "Text" else lang
        lang_folder = OUTPUT_BASE / "".join(c for c in lang_label if c.isalnum() or c in "_-")
        lang_folder.mkdir(parents=True, exist_ok=True)

        form = {"language": lang, "playerName": ""}
        with open(file_path, "rb") as f:
            files = {"jsonFile": f}
            response = requests.post(URL, data=form, files=files)

        # Debug: show status
        print(f"    HTTP status: {response.status_code}, Response length: {len(response.text)}")

        # Save output
        output_file = lang_folder / f"{file_path.stem}.html"
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(response.text)
        print(f"    Saved: {output_file}")

# -----------------------------
# Cleanup PHP server
# -----------------------------
php_process.terminate()
php_process.wait()
print("PHP server terminated.")
print("All files & languages processed!")
