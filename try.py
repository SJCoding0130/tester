import os
import requests
import json
from datetime import datetime

# === CONFIG ===
CHAPTER_LIST_FILE = "chapters.txt"  # output from UnityPy script
TITLE_LIST_FILE = "titles.txt"      # output from UnityPy script
BASE_URL = "https://d15iupkbkbqkwv.cloudfront.net/adv2024/Android/"
CHAPTER_DIR = "downloaded_chapters"
TITLE_DIR = "downloaded_titles"     # single folder for all title assets
META_FILE = "asset_metadata.json"

# Ensure folders exist
os.makedirs(CHAPTER_DIR, exist_ok=True)
os.makedirs(TITLE_DIR, exist_ok=True)

# === UTILITIES ===
def log(message: str):
    """Append message to log file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_metadata(metadata):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


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


def download_assets(asset_list, save_folder, metadata, lump_into_single_folder=False):
    """Download assets from the server with caching via ETag/Last-Modified."""
    updated_metadata = metadata.copy()

    for asset in asset_list:
        # If lumping into single folder, ignore subfolders in asset name
        file_name = os.path.basename(asset) if lump_into_single_folder else asset
        save_path = os.path.join(save_folder, file_name)

        url = BASE_URL + asset

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
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(response.content)
                log(f" DOWNLOADED: {asset}")
                updated_metadata[asset] = {
                    "ETag": etag,
                    "Last-Modified": last_mod,
                }
            else:
                log(f" FAILED: {asset} (HTTP {response.status_code})")
        except Exception as e:
            log(f" ERROR downloading {asset}: {e}")

    return updated_metadata


def extract_assets(file_path):
    if not os.path.exists(file_path):
        log(f" List file not found: {file_path}")
        return []

    assets = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name:
                assets.append(name)

    assets = sorted(set(assets))
    log(f" Found {len(assets)} assets in {file_path}")
    return assets


# === MAIN ===
if __name__ == "__main__":
    log("=== Process started ===")
    metadata = load_metadata()

    # Download chapter assets (keep original structure)
    chapter_assets = extract_assets(CHAPTER_LIST_FILE)
    if chapter_assets:
        metadata = download_assets(chapter_assets, CHAPTER_DIR, metadata)
    else:
        log(" No chapter assets found, skipping.")

    # Download title assets (lump into single folder)
    title_assets = extract_assets(TITLE_LIST_FILE)
    if title_assets:
        metadata = download_assets(title_assets, TITLE_DIR, metadata, lump_into_single_folder=True)
    else:
        log(" No title assets found, skipping.")

    save_metadata(metadata)
    log("=== Process finished ===")
