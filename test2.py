import UnityPy
import sys
import os
import json


def extract_chapter(bundle_path):
    """Logic from common.py"""
    try:
        env = UnityPy.load(bundle_path)
    except Exception as e:
        print(f"[ERROR] Failed to load UnityFS: {e}")
        return

    found = False

    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            mb = obj.read()
            name = getattr(mb, "m_Name", "")

            if name.endswith(".chapter"):
                found = True
                data = obj.read_typetree()

                output = os.path.splitext(bundle_path)[0] + ".json"
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                print(f"[INFO] Extracted CHAPTER → {output}")

    if not found:
        print("[WARNING] No .chapter MonoBehaviour found.")


def extract_book(bundle_path):
    """Logic from story.py"""
    try:
        env = UnityPy.load(bundle_path)
    except Exception as e:
        print(f"[ERROR] Failed to load UnityFS: {e}")
        return

    found = False

    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            mb = obj.read()
            name = getattr(mb, "m_Name", "")

            if name.endswith(".book"):
                found = True
                data = obj.read_typetree()

                output = os.path.splitext(bundle_path)[0] + ".json"
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                print(f"[INFO] Extracted BOOK → {output}")

    if not found:
        print("[WARNING] No .book MonoBehaviour found.")


def auto_extract(bundle_path):
    filename = os.path.basename(bundle_path)

    if filename == "common.chapter.asset":
        print("[INFO] Detected common.chapter.asset → Running CHAPTER extractor")
        extract_chapter(bundle_path)
    else:
        print("[INFO] Running BOOK extractor for:", filename)
        extract_book(bundle_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python combined_extract.py <unity_asset_path>")
    else:
        auto_extract(sys.argv[1])
