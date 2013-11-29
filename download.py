#!/usr/bin/python
import os
import datetime
import urllib2
import logging
from ftplib import FTP
from zipfile import ZipFile

import project_settings as settings

log = logging.getLogger('download')

HYDROLOGICAL_UNITS_ZIP = 'Hydrologic_Units.zip'
FILES = [('http://txpub.usgs.gov/USACE/data/water_resources/Hydrologic_Units.zip', HYDROLOGICAL_UNITS_ZIP),
         ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delnorte.dat', 'delnorte.dat'),
         ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delNorteT.dat', 'delnorteT.dat')]

class ModisDataDownloader:
    def __init__(self, dataset='AQUA'):
        self.ftp = FTP('n4ftl01u.ecs.nasa.gov')
        self.ftp.login()
        self.dataset = dataset

        if self.dataset == 'AQUA':
            self.ftp.cwd('/MOSA/MYD10A1.005/')
        elif self.dataset == 'TERRA':
            self.ftp.cwd('/MOST/MOD10A1.005/')

    def download_all_files(self, tile, start_date, end_date):
        log.info('Downloading all HDF files')
        log.info("  Daterange: %s to %s"%(str(start_date), str(end_date)))
        hdf_files_for_tile = []

        daily_dirs = []
        dates = []
        date = start_date
        while date < end_date + datetime.timedelta(1):
            dates.append(date)
            daily_dirs.append(date.strftime('%Y.%m.%d'))
            date += datetime.timedelta(1)

        for date, daily_dir in zip(dates, daily_dirs):
            self.ftp.cwd(daily_dir)
            try:
                all_lines = []
                self.ftp.dir(all_lines.append)

                all_files = [l.split()[8] for l in all_lines[1:]]       
                hdf_files = [f for f in all_files if f.split('.')[-1] == 'hdf']
                hdf_file_for_tile = [f for f in hdf_files if f.split('.')[2] == tile]

                if len(hdf_file_for_tile) != 1:
                    log.warning("PROBLEM FINDING file for %s"%date)
                    log.warning("Found %i files"%len(hdf_file_for_tile))
                    raise Exception('0 or more than one hdf file found')

                hdf_file = hdf_file_for_tile[0]
                hdf_files_for_tile.append(hdf_file)

                data_dir = "%s/%s_%s_%i"%(settings.DATA_DIR, self.dataset, tile, date.year)
                full_file_name = "%s/%s"%(data_dir, hdf_file)
                if os.path.exists(full_file_name):
                    log.info('    %s file %s already exists'%(self.dataset, hdf_file))
                else:
                    log.info('    Downloading %s file %s'%(self.dataset, hdf_file))
                    if not os.path.exists(data_dir):
                        os.makedirs(data_dir)

                    self.ftp.retrbinary('RETR %s'%(hdf_file), open(full_file_name, 'wb').write)
                    log.info('    Downloaded file')
            except Exception, e:
                log.warning(e)

            self.ftp.cwd('..')

        return hdf_files_for_tile       

def download_all_modis_files():
    start_date = settings.START_DATE
    end_date = settings.END_DATE

    for dataset in settings.MODIS_DATASETS:
        log.info("Downloading dataset %s"%dataset)
        mdd = ModisDataDownloader(dataset)
        hdf_files_for_tile = mdd.download_all_files(settings.TILE, start_date, end_date)

def download_data(force_download=False):
    if not os.path.exists(settings.DATA_DIR):
        os.makedirs(settings.DATA_DIR)

    files = []
    files.append(FILES)

    for url, file_name in FILES:
        rel_file_name = '%s/%s'%(settings.DATA_DIR, file_name)

        if os.path.exists(rel_file_name) and not force_download:
            log.info('Already downloaded file: %s'%(file_name))
            continue

        log.info('Downloading file: %s'%(file_name))

        req = urllib2.urlopen(url)
        f = open(rel_file_name, 'w')
        f.write(req.read())
        f.close()

    post_download_actions()

def post_download_actions():
    '''Unzips Hydrologic_Units.zip if necessary'''
    log.info('Extracting contents from zip file')
    rel_file_name = '%s/%s'%(settings.DATA_DIR, HYDROLOGICAL_UNITS_ZIP)
    z = ZipFile(rel_file_name)
    z.extractall(settings.DATA_DIR)
    z.close()

if __name__ == "__main__":
    download_all_modis_files()
    download_data()
