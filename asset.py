import os
import requests
import zipfile
import subprocess

# Configuration
asset_ripper_url = "https://github.com/AssetRipper/AssetRipper/releases/download/0.3.4.0/AssetRipper_win_x64.zip"
zip_path = "AssetRipper.zip"
extract_path = "AssetRipper"
input_folder = "downloaded_titles"
output_folder = "repo_b/extracted"

# 1. Download AssetRipper zip
print("Downloading AssetRipper...")
response = requests.get(asset_ripper_url, stream=True)
response.raise_for_status()
with open(zip_path, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
print("Download complete.")

# 2. Extract the zip
print("Extracting AssetRipper...")
with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(extract_path)
print("Extraction complete.")

# 3. Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# 4. Run AssetRipper
asset_ripper_exe = os.path.join(extract_path, "AssetRipper.exe")
cmd = [asset_ripper_exe, input_folder, "-o", output_folder, "-q"]
print(f"Running: {' '.join(cmd)}")
subprocess.run(cmd, check=True)
print("Done.")
