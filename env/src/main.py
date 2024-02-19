from picamera import PiCamera
from datetime import datetime, timedelta
from orbit import satellite
from pathlib import path
from logzero import logger, logfile
from custom_camera import camera
import numpy as np
import csv
import cv2
from exif import Image
from datetime import datetime
import math

def capture(camera, image):
    iss = satellite(25544)
    iss_lat = iss.lat()
    iss_long = iss.long()

    south, exif_lat = convert(iss_lat)
    west, exif_long = convert(iss_long)

    camera.exif_tags['GPS.GPSLatitude'] = exif_lat
    camera.exif_tags['GPS.GPSLatitudeRed'] = 's' if south else 'n'
    camera.exif_tags['GPS.GPSLongitude'] = exif_long
    camera.exif_tags['GPS.GPSLongitude'] = 'w' if west else 'e'

    camera.capture(image)

def create_csv_file(data_file):
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ('ImageNumber', 'DataTime', 'Latitide', 'Longitude', 'NDVI')
        writer.writerow(header)

def add_csv_data(file):
    with open(file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def prepare_window(image):
    image = np.array(image, dtype = float)/float(255)
    shape = image.shape
    height = int(shape[0] / 2)
    width = int(shape[1] / 2)
    image = cv2.resize(image, (width, height))
    return image

def calculate_ndvi(image):
    blue, green, red = cv2.split(image)
    bottom = (r.astype(float) + b.astype(float))
    bottom[bottom == 0] = 0.01
    ndvi = (b.astype(float) - r) / bottom
    return ndvi

base_folder = Path(__file__).parent.resolve()

logfile(base_folder/"events.log")

camera = PiCamera()
camera.resolution(1296, 972)

data_file = base_folder/"data.csv"
create_csv_file(data_file)

counter = 1
start_time = datetime.now()
current_time = datetime.now()
record_time = datetime.now()

def get_time(image):
    with open(image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
    return time

def get_time_difference(image_1, image_2):
    time_1 = get_time(image_1)
    time_2 = get_time(image_2)
    time_difference = time_2 - time_1
    return time_difference.seconds

def convert_to_cv(image_1, image_2):
    image_1_cv = cv2.imread(image_1, 0)
    image_2_cv = cv2.imread(image_2, 0)
    return image_1_cv, image_2_cv

def calculate_features(image_1, image_2, feature_number):
    orb = cv2.ORB_create(nfeatures = feature_number)
    keypoints_1, descriptors_1 = orb.detectAndCompute(image_1_cv, None)
    keypoints_2, descriptors_2 = orb.detectAndCompute(image_2_cv, None)
    return keypoints_1, keypoints_2, descriptors_1, descriptors_2

def calculate_matches(descriptors_1, descriptors_2):
    brute_force = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = brute_force.match(descriptors_1, descriptors_2)
    matches = sorted(matches, key=lambda x: x.distance)
    return matches

def display_matches(image_1_cv, keypoints_1, image_2_cv, keypoints_2, matches):
    match_img = cv2.drawMatches(image_1_cv, keypoints_1, image_2_cv, keypoints_2, matches[:100], None)
    resize = cv2.resize(match_img, (1600,600), interpolation = cv2.INTER_AREA)
    cv2.imshow('matches', resize)
    cv2.waitKey(0)
    cv2.destroyWindow('matches')

def find_matching_coordinates(keypoints_1, keypoints_2, matches):
    coordinates_1 = []
    coordinates_2 = []
    for match in matches:
        image_1_idx = match.queryIdx
        image_2_idx = match.trainIdx
        (x1,y1) = keypoints_1[image_1_idx].pt
        (x2,y2) = keypoints_2[image_2_idx].pt
        coordinates_1.append((x1,y1))
        coordinates_2.append((x2,y2))
    return coordinates_1, coordinates_2

def calculate_mean_distance(coordinates_1, coordinates_2):
    all_distances = 0
    merged_coordinates = list(zip(coordinates_1, coordinates_2))
    for coordinate in merged_coordinates:
        x_difference = coordinate[0][0] - coordinate[1][0]
        y_difference = coordinate[0][1] - coordinate[1][1]
        distance = math.hypot(x_difference, y_difference)
        all_distances = all_distances + distance
    return all_distances / len(merged_coordinates)

def calculate_speed_in_kmps(feature_distance, GSD, time_difference):
    distance = feature_distance * GSD / 100000
    speed = distance / time_difference
    return speed

# Event loop
while(current_time < start_time + timedelta(minutes = 4.9)):
    try:
        if current_time - record_time >= timedelta(seconds = 5):
            # Speed Stuff
            time_difference = get_time_difference(image_1, image_2) # Get time difference between images
            image_1_cv, image_2_cv = convert_to_cv(image_1, image_2) # Create OpenCV image objects
            keypoints_1, keypoints_2, descriptors_1, descriptors_2 = calculate_features(image_1_cv, image_2_cv, 1000) # Get keypoints and descriptors
            matches = calculate_matches(descriptors_1, descriptors_2) # Match descriptors
            
            display_matches(image_1_cv, keypoints_1, image_2_cv, keypoints_2, matches) # Display matches
            coordinates_1, coordinates_2 = find_matching_coordinates(keypoints_1, keypoints_2, matches)
            average_feature_distance = calculate_mean_distance(coordinates_1, coordinates_2)
            speed = calculate_speed_in_kmps(average_feature_distance, 12648, time_difference)
            print(speed)

            # Actual Project Stuff
            file_name = f"{base_folder}/photo_{counter:03d}.jpeg"
            stream = picamera.array.PiRGBArray(camera)
            camera.capture(stream, format = 'bgr', use_video_port = True)
            original = stream.array
            capture(camera, file_name)
            contrasted = contrast_stretch(original)
            ndvi = contrast_stretch(calculate_ndvi(contrasted))
            prep_ndvi = ndvi.astype(np.uint8)
            colour_ndvi = cv2.applyColorMap(prep_ndvi, custom_camera)
    
            cv2.imwrite(file_name, colour_ndvi)
            logger.info(f"iteration {counter}")
            csv_row = (counter, datetime.today().strftime('%Y-%m-%dT%H:%M:%S'), 10, 10, file_name)
            add_csv_data(data_file, csv_row)
            record_time = datetime.now()
            counter += 1
        current_time = datetime.now()
    except Exception as e:
        print(e)
        logger.error(f'{e.__class__.__name__}: {3}')