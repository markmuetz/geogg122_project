import socket
import datetime

if socket.gethostname() == 'breakeven-pangolin':
    DATA_DIR= '/media/E6F08871F08849AF/geogg122_data/'
    DATA_DIR_TPL = '/media/E6F08871F08849AF/geogg122_data/%s/'
else:
    DATA_DIR= 'data_files/'
    DATA_DIR_TPL = 'data_files/%s/'

RUN_DOWNLOAD_FILES = False
RUN_DOWNLOAD_HDF_FILES = False
RUN_DATA_PREPARATION = True

TILE = 'h09v05'
MODIS_DATASETS = ['AQUA', 'TERRA']
#SATELLITE_DATA = ['TERRA']

START_DATE = datetime.datetime(2004, 12, 20)
END_DATE = datetime.datetime(2005, 01, 01)
