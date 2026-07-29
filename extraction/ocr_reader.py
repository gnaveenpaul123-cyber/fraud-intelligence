import easyocr

reader = easyocr.Reader(["en"])

def extract_text_from_image(image_path):
    result = reader.readtext(image_path)
    texts = []
    for item in result:
        texts.append(item[1])
    return "\n".join(texts)