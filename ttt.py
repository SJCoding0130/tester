import os
import requests
from pathlib import Path
import subprocess

# Start PHP built-in server
subprocess.Popen(
    ["php", "-S", "localhost:8000"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Folder containing .book.json files
json_folder = Path("./json")
json_files = sorted(json_folder.glob("*.book.json"))  # sort files alphabetically

# Endpoint URL
url = "http://localhost:8000/view.php"

# Languages to generate
languages = [
    "Text",
    "English",
    "ChineseTraditional",
    "ChineseSimplified"
]

# Base output folder (absolute path)
output_base = Path("./output").resolve()
output_base.mkdir(parents=True, exist_ok=True)

for file_path in json_files:
    base_name = file_path.stem  # filename without extension

    print("="*40)
    print(f"Processing file: {file_path.name}")
    print("="*40)

    for lang in languages:
        print(f"  → Language: {lang}")

        # Map Text → Japanese for folder only
        lang_label = "Japanese" if lang == "Text" else lang

        # Sanitize folder name (remove invalid characters)
        lang_folder_name = "".join(c for c in lang_label if c.isalnum() or c in "_-")

        # Create language folder inside output_base
        lang_folder = output_base / lang_folder_name
        lang_folder.mkdir(parents=True, exist_ok=True)

        # Prepare form data
        form = {
            "language": lang,
            "playerName": "",
        }

        # PHP endpoint expects file
        with open(file_path, "rb") as f:
            files = {"jsonFile": f}
            response = requests.post(url, data=form, files=files)

        # Output filename inside language folder (keep base name only)
        output_file = lang_folder / f"{file_path.name.replace('.book.json', '.html')}"

        # Write response content
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(response.text)

        print(f"    Saved: {output_file}")

print("All files & languages processed!")

