import os
import json
def create_case_folder(post_id):
    folder = os.path.join("evidence","reddit", post_id)
    os.makedirs(folder, exist_ok = True)
    return folder
def save_metadata(case_folder, record):
    filepath = os.path.join(case_folder, "metadata.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record.to_dict(), f, indent=4, ensure_ascii=False)
        
