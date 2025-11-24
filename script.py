from datetime import datetime
import pytz
import os

# Malaysia timezone
malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
malaysia_time = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S %Z")

# Absolute path to output.txt in repo folder
output_file = os.path.join(os.environ["GITHUB_WORKSPACE"], "output.txt")

# Append timestamp
with open(output_file, "a") as f:
    f.write(malaysia_time + "\n")

print("Written to output.txt:", malaysia_time)
