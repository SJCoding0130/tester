import os
import requests
import zipfile
import subprocess
import shutil
import glob

# Configuration
asset_ripper_url = "https://github.com/AssetRipper/AssetRipper/releases/download/0.3.4.0/AssetRipper_win_x64.zip"
zip_path = "AssetRipper.zip"
extract_path = "AssetRipper"
input_folder = "downloaded_titles"
output_folder = "extracted"
final_folder = "filtered_assets"

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
print("Extraction done.")

# 5. Create final folder
os.makedirs(final_folder, exist_ok=True)

# 6. Define patterns to keep
patterns = [
    os.path.join(output_folder, "ExportedProject", "Assets", "Texture2D", "*.png"),
    os.path.join(output_folder, "ExportedProject", "Assets", "adv", "resources", "adv", "texture", "bg", "*asset"),
    os.path.join(output_folder, "ExportedProject", "Assets", "adv", "resources", "adv", "texture", "sprite", "*asset"),
    os.path.join(output_folder, "ExportedProject", "Assets", "adv", "resources", "adv", "texture", "bg", "*png"),
]

# 7. Move matching files into one folder
print("Collecting filtered files...")
for pattern in patterns:
    for file_path in glob.glob(pattern, recursive=True):
        filename = os.path.basename(file_path)
        destination = os.path.join(final_folder, filename)

        # Avoid overwriting duplicate names
        counter = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(destination):
            destination = os.path.join(final_folder, f"{base}_{counter}{ext}")
            counter += 1

        shutil.copy2(file_path, destination)

print("Done. Filtered files are in:", final_folder)
