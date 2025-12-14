import os
import requests
from pathlib import Path
import subprocess
import time
import sys

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

# Start PHP server
php_cwd = Path(__file__).parent
process = subprocess.Popen(
    ["php", "-S", "localhost:8000"],
    cwd=php_cwd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
try:
    wait_for_server("http://localhost:8000")
except RuntimeError as e:
    stdout, stderr = process.communicate(timeout=5)
    print("PHP stdout:", stdout.decode(), file=sys.stderr)
    print("PHP stderr:", stderr.decode(), file=sys.stderr)
    process.terminate()
    raise e

# JSON folder
json_folder = Path(__file__).parent / "json"
json_files = sorted(json_folder.glob("*.book.json"))

# Endpoint URL
url = "http://localhost:8000/view.php"

# Languages
languages = ["Text", "English", "ChineseTraditional", "ChineseSimplified"]

# Output folder
output_base = Path(__file__).parent / "output"
output_base.mkdir(parents=True, exist_ok=True)

for file_path in json_files:
    print("="*40)
    print(f"Processing file: {file_path.name}")
    print("="*40)
    for lang in languages:
        print(f"  → Language: {lang}")
        lang_label = "Japanese" if lang == "Text" else lang
        lang_folder = output_base / "".join(c for c in lang_label if c.isalnum() or c in "_-")
        lang_folder.mkdir(parents=True, exist_ok=True)

        form = {"language": lang, "playerName": ""}
        with open(file_path, "rb") as f:
            files = {"jsonFile": f}
            response = requests.post(url, data=form, files=files)
            print(f"    HTTP status: {response.status_code}, Response length: {len(response.text)}")

        output_file = lang_folder / f"{file_path.stem}.html"
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(response.text)
        print(f"    Saved: {output_file}")

print("All files & languages processed!")
process.terminate()
process.wait()

print("PHP server terminated.")


