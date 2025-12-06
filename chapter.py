import UnityPy
import sys
import os

def save_manifest(bundle_path, output_file):
    if not os.path.exists(bundle_path):
        print(f"[ERROR] File does not exist: {bundle_path}")
        return

    try:
        env = UnityPy.load(bundle_path)
    except Exception as e:
        print(f"[ERROR] Failed to load UnityFS file: {e}")
        return

    manifest_found = False
    lines = []

    for obj in env.objects:
        if obj.type.name == "AssetBundleManifest":
            manifest = obj.read()
            manifest_found = True

            # Unity sometimes returns either "name" or [index, name]
            for item in manifest.AssetBundleNames:
                # Handle [index, name] format
                name = item[1] if isinstance(item, (list, tuple)) and len(item) == 2 else item

                # Only add items that end with ".chapter.asset"
                if name.endswith(".chapter.asset"):
                    lines.append(name)

            break

    if not manifest_found:
        print("[WARNING] No AssetBundleManifest found in this file.")
        return

    # Save as plain text (not JSON)
    with open(output_file, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"[INFO] Manifest saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_manifest.py <path_to_unityfs_file>")
    else:
        file_path = sys.argv[1]
        save_manifest(file_path, "output.txt")
