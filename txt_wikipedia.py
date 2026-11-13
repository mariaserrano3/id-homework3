import wikipedia
import os
import time

wikipedia.set_lang("en")

dataset_dir = "dataset_wikipedia"
if not os.path.exists(dataset_dir):
    os.makedirs(dataset_dir)

topics = [
        "Computer science", 
        "Data engineering", 
        "Information retrieval",
        "History of Rome", 
        "Ancient Rome",
        "Roman Empire"
]

# Count existing files to resume download if interrupted
files_created = len([name for name in os.listdir(dataset_dir) if name.endswith('.txt')])
file_limit = 500

print(f"Starting with {files_created} existing files.")

for topic in topics:
    if files_created >= file_limit:
        break
        
    print(f"Searching for articles about: {topic}")
    
    try:
        titles = wikipedia.search(topic, results=120)
        time.sleep(2) # Pause after the main search
    except Exception:
        print(f"Connection failed when searching {topic}. Skipping...")
        time.sleep(5)
        continue
    
    for title in titles:
        if files_created >= file_limit:
            break
        
        # Clean title to create a valid filename
        filename = "".join([c if c.isalnum() else "_" for c in title]) + ".txt"
        filepath = os.path.join(dataset_dir, filename)
        
        if not os.path.exists(filepath):
            try:
                page = wikipedia.page(title, auto_suggest=False)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(page.content)
                
                files_created += 1
                print(f"[{files_created}/{file_limit}] Saved: {filename}")
                time.sleep(0.5) # Half-second pause between files
                
            except wikipedia.exceptions.DisambiguationError:
                pass
            except wikipedia.exceptions.PageError:
                pass
            except Exception:
                time.sleep(2) # Extra pause for isolated connection blocks
                pass

print(f"Download finished. You have {files_created} files in the '{dataset_dir}' folder.")