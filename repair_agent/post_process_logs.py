import os

files = os.listdir("./")

files = [f for f in files if f.startswith("batch_log_")]

for f in files:
    with open(f) as log_file:
        log_content = log_file.read()
    log_content = log_content.replace("""\ Thinking...

             
""", "").replace("""/ Thinking...

             
""", "").replace("""- Thinking...

             
""", "").replace("""| Thinking...

             
""", "")

    with open(f, "w") as log_file:
        log_file.write(log_content)