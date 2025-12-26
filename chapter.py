import os
import requests
import UnityPy

URL = "http://d15iupkbkbqkwv.cloudfront.net/adv2024/Android/Android"
BUNDLE_FILE = "Android.bundle"
OUTPUT_FILE = "chapters.txt"


def download_bundle(url, path, etag_file="etag.txt"):
    headers = {}
    # If we have a saved ETag, send it to check freshness
    if os.path.exists(etag_file):
        with open(etag_file, "r") as f:
            etag = f.read().strip()
            headers["If-None-Match"] = etag

    r = requests.get(url, stream=True, headers=headers)

    if r.status_code == 304:
        print("[INFO] Local file is already the latest version.")
        return

    r.raise_for_status()

    # Save the new file
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    # Save the new ETag if provided
    if "ETag" in r.headers:
        with open(etag_file, "w") as f:
            f.write(r.headers["ETag"])

    print("[INFO] File downloaded and updated.")



def list_chapter_assets(bundle_path, output_file):
    env = UnityPy.load(bundle_path)

    results = []

    for obj in env.objects:
        if obj.type.name == "AssetBundleManifest":
            manifest = obj.read()

            for item in manifest.AssetBundleNames:
                name = item[1] if isinstance(item, (list, tuple)) else item
                if name.endswith(".chapter.asset"):
                    results.append(name)
            break

    # 🔽 SORT ALPHABETICALLY
    results.sort()

    with open(output_file, "w", encoding="utf-8") as f:
        for name in results:
            f.write(name + "\n")

    print(f"[INFO] {len(results)} entries written (sorted)")


if __name__ == "__main__":
    download_bundle(URL, BUNDLE_FILE)
    list_chapter_assets(BUNDLE_FILE, OUTPUT_FILE)


