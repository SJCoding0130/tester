from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

# Set Malaysia timezone
malaysia_time = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d %H:%M:%S %Z")

# Append to output.txt
with open("output.txt", "a") as f:
    f.write(malaysia_time + "\n")

print("Written to output.txt:", malaysia_time)
