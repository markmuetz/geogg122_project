import socket
import datetime

hostname = socket.gethostname()
if hostname == 'breakeven-pangolin':
    DATA_DIR= '/media/SAMSUNG/geogg122_data'
elif (len(hostname.split('.')) != 0 and
     ".".join(socket.gethostname().split('.')[1:]) == 'geog.ucl.ac.uk'):
    DATA_DIR= '/data/geospatial_24/ucfamue/geogg122_data'
else:
    print("DATA_DIR needs to be configured on this computer")
    raise Exception('DATA_DIR needs to be configured on this computer\nPlease edit project_settings.py')
    # You can just comment out the next line to have it create a 
    # folder in your home dir. Warning, it can use quite a lot of
    # disk space (~1.5GB for one year's worth of data.
    # DATA_DIR= '~/geogg122_data'

TILE = 'h09v05'
MODIS_DATASETS = ('AQUA', 'TERRA')
#MODIS_DATASETS = ('TERRA',)

START_DATE = datetime.datetime(2008, 12, 01)
END_DATE = datetime.datetime(2011, 01, 31)

CAL_START_DATE = datetime.datetime(2009, 01, 01)
CAL_END_DATE = datetime.datetime(2009, 12, 31)

APP_START_DATE = datetime.datetime(2010, 01, 01)
APP_END_DATE = datetime.datetime(2010, 12, 31)

RUN_DOWNLOAD_FILES = False
RUN_DOWNLOAD_MODIS_FILES = True
RUN_DATA_PREPARATION = True
RUN_MODEL_CALIBRATION = True
RUN_MODEL_APPLICATION = True
