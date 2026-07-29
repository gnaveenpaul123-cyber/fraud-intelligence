import os

def save_text_file(case_folder, filename, content):
    """
    Save text evidence into the case folder.
    """

    if not content:
        return

    file_path = os.path.join(case_folder, filename)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Saved: {file_path}")

    return file_path