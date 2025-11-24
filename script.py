from datetime import datetime
import pytz

# Malaysia timezone
malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
malaysia_time = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S %Z")

# Append timestamp to output.txt
with open("output.txt", "a") as f:
    f.write(malaysia_time + "\n")

print("Written to output.txt:", malaysia_time)
