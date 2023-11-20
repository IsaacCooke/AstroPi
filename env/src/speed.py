from exif import Image
from datetime import datetime
import cv2
import math

def get_time(image):
    with open(image, 'rb') as image_file:
        image = Image(image_file)
        time_string = image.get("datetime_origional")
        time = datetime.strftime(time_string, "%Y:%m:%d %H:%M:%S")
        return time

def get_speed(image1, image2):
    time_1 = get_time(image1)
    time_2 = get_time(image2)
    time_difference = time_2 - time_1
    print(time_difference.seconds)


def convert_to_cv(image1, image2):
    image1CV = cv2.imread(image1, 0)
    image2CV = cv2.imread(image2, 0)
    return image1CV, image2CV

def calculate_features(image1, image2, feature_number):
    orb = cv2.ORB_create(nfeatures = feature_number)