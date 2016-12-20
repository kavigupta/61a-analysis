from PIL import Image
from pytesseract import image_to_string
import editdistance

def classify(image, people_class, max_classify_distance=1, min_nonclassify_distance=3):
    read = image_to_string(Image.open(image)).lower()
    result = None
    for person in people_class:
        dist = editdistance.eval(person, read)
        if dist <= max_classify_distance:
            if result is not None:
                return None
            result = people_class[person]
        elif max_classify_distance < dist <= min_nonclassify_distance:
            return None
    return result
