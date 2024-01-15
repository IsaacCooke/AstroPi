from picamera import PiCamera
from datetime import datetime, timedelta
from orbit import satellite
from pathlib import path
from logzero import logger, logfile
from custom_camera import camera
import numpy as np
import csv
import cv2

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

# Event loop
while(current_time < start_time + timedelta(minutes = 4.9)):
    try:
        if current_time - record_time >= timedelta(seconds = 5):
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

