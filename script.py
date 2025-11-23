from datetime import datetime

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open("output.txt", "a") as f:   # append mode
    f.write(current_time + "\n")

print("Written to output.txt:", current_time)
