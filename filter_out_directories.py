import os
import time

def list_directories_created_after(directory_path, cutoff_date):
    if not os.path.isdir(directory_path):
        print("Invalid directory path.")
        return

    # List all entries in the directory
    entries = os.listdir(directory_path)

    # Filter out directories and their creation times
    directories_with_creation_time = [(entry, os.path.getctime(os.path.join(directory_path, entry))) 
                                      for entry in entries 
                                      if os.path.isdir(os.path.join(directory_path, entry))]

    # Filter directories created after the cutoff date
    directories_after_cutoff = [(directory, creation_time) 
                                for directory, creation_time in directories_with_creation_time 
                                if creation_time > cutoff_date]

    if not directories_after_cutoff:
        print("No directories found in the specified directory created after the specified date.")
        return

    print("Directories created after", time.ctime(cutoff_date), "in", directory_path, ":")
    for directory, creation_time in directories_after_cutoff:
        creation_time_formatted = time.ctime(creation_time)
        print(f"{directory}\tCreated at: {creation_time_formatted}")

if __name__ == "__main__":
    directory_path = input("Enter the directory path: ")

    try:
        cutoff_date_input = input("Enter the cutoff date in YYYY-MM-DD format: ")
        cutoff_date = time.mktime(time.strptime(cutoff_date_input, "%Y-%m-%d"))
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
    else:
        list_directories_created_after(directory_path, cutoff_date)
