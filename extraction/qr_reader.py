import cv2
from pyzbar.pyzbar import decode


def extract_qr_text(image_path):

    image = cv2.imread(image_path)

    results = decode(image)

    qr_texts = []

    for result in results:
        qr_texts.append(result.data.decode("utf-8"))

    return "\n".join(qr_texts)