
from os import system, listdir

from PIL import Image
from pytesseract import image_to_string
import editdistance

from constants import DATA_DIR

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

def setup_ocr(raw_data):
    system("unzip {} -d {}/extract".format(raw_data, DATA_DIR))
    base = DATA_DIR + "/extract/"
    mainfolder = base + listdir(base)[0]
    for index, path in enumerate(sorted(listdir(mainfolder))):
        if index % 100 == 0:
            print("*", end="")
        fullpath = mainfolder + "/" + path
        system("mkdir {}/ocr".format(DATA_DIR))
        basic_format = r"pdftoppm -png -f 3 -l 3 -x 170 -y %s -W 900 -H 100 {} > {}/ocr/%s{}.png" \
            .format(fullpath, DATA_DIR, index)
        system(basic_format % (1030, "left"))
        system(basic_format % (1115, "right"))
