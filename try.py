import os
import requests
import json
from datetime import datetime

# === CONFIG ===
CHAPTER_LIST_FILE = "chapters.txt"  # output from UnityPy script
BASE_URL = "https://d15iupkbkbqkwv.cloudfront.net/adv2024/Android/"
SAVE_DIR = "downloaded_assets"

#LOG_FILE = "chapter_asset_log.txt"
META_FILE = "asset_metadata.json"

os.makedirs(SAVE_DIR, exist_ok=True)

# === UTILITIES ===
# === Overwrite log at start of script ===
#with open(LOG_FILE, "w", encoding="utf-8") as f:
#    f.write(f"=== Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

def log(message: str):
    """Append message to log file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
#    with open(LOG_FILE, "a", encoding="utf-8") as f:
#        f.write(line + "\n")

def load_metadata():
    """Load saved metadata (ETag/Last-Modified info) from file."""
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    """Save metadata to disk."""
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

# === STEP 1: Extract chapter asset filenames ===
def extract_chapter_assets():
    if not os.path.exists(CHAPTER_LIST_FILE):
        log(f" Chapter list file not found: {CHAPTER_LIST_FILE}")
        return []

    chapter_assets = []

    with open(CHAPTER_LIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name.endswith(".chapter.asset"):
                chapter_assets.append(name)

    chapter_assets = sorted(set(chapter_assets))
    log(f" Found {len(chapter_assets)} .chapter.asset files from list.")
    return chapter_assets


# === STEP 2: Download assets with caching ===
def get_remote_headers(url):
    """Get ETag and Last-Modified headers from the server."""
    try:
        response = requests.head(url, timeout=15)
        if response.status_code == 200:
            return {
                "ETag": response.headers.get("ETag"),
                "Last-Modified": response.headers.get("Last-Modified"),
            }
        else:
            log(f" HEAD {url} returned HTTP {response.status_code}")
    except Exception as e:
        log(f" HEAD request failed for {url}: {e}")
    return {}

def download_assets(assets):
    metadata = load_metadata()
    updated_metadata = metadata.copy()

    for asset in assets:
        url = BASE_URL + asset
        save_path = os.path.join(SAVE_DIR, asset)

        headers = get_remote_headers(url)
        etag = headers.get("ETag")
        last_mod = headers.get("Last-Modified")

        prev = metadata.get(asset, {})

        # Skip if unchanged
        if (
            (etag and prev.get("ETag") == etag)
            and (last_mod and prev.get("Last-Modified") == last_mod)
        ):
            log(f" SKIPPED (no change): {asset}")
            continue

        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                log(f" DOWNLOADED: {asset}")
                updated_metadata[asset] = {
                    "ETag": etag,
                    "Last-Modified": last_mod,
                    "Last-Checked": datetime.now().isoformat()
                }
            else:
                log(f" FAILED: {asset} (HTTP {response.status_code})")
        except Exception as e:
            log(f" ERROR downloading {asset}: {e}")

    save_metadata(updated_metadata)

# === MAIN ===
if __name__ == "__main__":
    log("=== Process started ===")
    assets = extract_chapter_assets()
    if assets:
        download_assets(assets)
    else:
        log(" No assets found, skipping download.")
    log("=== Process finished ===")







