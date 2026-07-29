import os
import requests
def download_image(image_url, case_folder, image_number):
    if not image_url:
        return None
    
    response = requests.get(image_url, timeout = 15)

    if response.status_code != 200:
        print(f"could  not download image:{image_url}")
        return None
    extension = os.path.splitext(image_url.split("?")[0])[1]
    if not extension:
        extension = ".jpg"
    filename = f"image_{image_number}{extension}"

    filepath = os.path.join(case_folder, filename)
    with open(filepath, "wb") as file:
        file.write(response.content)
    
    print(f"Saved image: {filepath}")
    return filepath
