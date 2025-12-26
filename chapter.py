import os
import requests
import UnityPy

URL = "http://d15iupkbkbqkwv.cloudfront.net/adv2024/Android/Android"
BUNDLE_FILE = "Android.bundle"
OUTPUT_FILE = "chapters2.txt"


def download_bundle(url, path):
    if os.path.exists(path):
        return

    r = requests.get(url, stream=True)
    r.raise_for_status()

    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)


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
