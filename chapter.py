import os
import requests
import UnityPy

URL = "http://d15iupkbkbqkwv.cloudfront.net/adv2024/Android/Android"
BUNDLE_FILE = "Android.bundle"
CHAPTER_FILE = "chapters.txt"
TITLE_FILE = "titles.txt"  # Combined bg_title and sprite_title


def download_bundle(url, path, etag_file="etag.txt"):
    headers = {}
    if os.path.exists(etag_file):
        with open(etag_file, "r") as f:
            etag = f.read().strip()
            headers["If-None-Match"] = etag

    r = requests.get(url, stream=True, headers=headers)

    if r.status_code == 304:
        print("[INFO] Local file is already the latest version.")
        return

    r.raise_for_status()

    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    if "ETag" in r.headers:
        with open(etag_file, "w") as f:
            f.write(r.headers["ETag"])

    print("[INFO] File downloaded and updated.")


def list_assets(bundle_path, chapter_output, title_output):
    env = UnityPy.load(bundle_path)

    chapters = []
    titles = []

    for obj in env.objects:
        if obj.type.name == "AssetBundleManifest":
            manifest = obj.read()
            for item in manifest.AssetBundleNames:
                name = item[1] if isinstance(item, (list, tuple)) else item

                # Filter chapter assets
                if name.endswith(".chapter.asset"):
                    chapters.append(name)
                # Filter assets containing bg_title or sprite_title
                if "bg_title" in name or "sprite_title" in name or "subtitle" in name:
                    titles.append(name)
            break

    # Sort alphabetically
    chapters.sort()
    titles.sort()

    # Save each list into its respective file
    with open(chapter_output, "w", encoding="utf-8") as f:
        for name in chapters:
            f.write(name + "\n")

    with open(title_output, "w", encoding="utf-8") as f:
        for name in titles:
            f.write(name + "\n")

    print(f"[INFO] {len(chapters)} chapter entries written to {chapter_output}")
    print(f"[INFO] {len(titles)} bg/sprite title entries written to {title_output}")


if __name__ == "__main__":
    download_bundle(URL, BUNDLE_FILE)
    list_assets(BUNDLE_FILE, CHAPTER_FILE, TITLE_FILE)

