import os
import requests
def download_image(image_url, case_folder, image_number):
    if not image_url:
        return
    
    response = requests.get(image_url, timeout = 15)

    if response.status_code != 200:
        print(f"could not download image:{image_url}")
        return
    extension = os.path.splitext(image_url.split("?")[0])[1]
    filename = f"image_{image_number}{extension}"

    filepath = case_folder + "/" + filename
    with open(filepath, "wb") as file:
        file.write(response.content)
    
    print(f"Saved image: {filepath}")