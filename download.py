#!/usr/bin/python
import os
import datetime
import urllib2
from ftplib import FTP
import project_settings as settings

DATA_DIR = settings.DATA_DIR

FILES = [('http://txpub.usgs.gov/USACE/data/water_resources/Hydrologic_Units.zip', 'Hydrologic_Units.zip'),
	 ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delnorte.dat', 'delnorte.dat'),
	 ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delNorteT.dat', 'delnorteT.dat')]

DATA_DIR_TPL = settings.DATA_DIR_TPL

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
	print('Downloading all HDF files')
	print("  Daterange: %s to %s"%(str(start_date), str(end_date)))
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
		    print "PROBLEM DOWNLOADING", hdf_file_for_tile
		    raise Exception('0 or more than one hdf file found')

		hdf_file = hdf_file_for_tile[0]
		hdf_files_for_tile.append(hdf_file)

		data_dir = DATA_DIR_TPL%"%s_%s_%i"%(self.dataset, tile, start_date.year)
		if os.path.exists(data_dir + hdf_file):
		    print('    %s file %s already exists'%(self.dataset, hdf_file))
		else:
		    print('    Downloading %s file %s'%(self.dataset, hdf_file))
		    if not os.path.exists(data_dir):
			os.makedirs(data_dir)

		    self.ftp.retrbinary('RETR %s'%(hdf_file), open(data_dir + hdf_file, 'wb').write)
		    print('    Downloaded file')
	    except Exception, e:
		print e

	    self.ftp.cwd('..')

	return hdf_files_for_tile	

def download_all_modis_files():
    start_date = settings.START_DATE
    end_date = settings.END_DATE

    for dataset in settings.MODIS_DATASETS:
	mdd = ModisDataDownloader(dataset)
	hdf_files_for_tile = mdd.download_all_files(settings.TILE, start_date, end_date)

def download_data(force_download=False):
    if not os.path.exists(DATA_DIR):
	os.makedirs(DATA_DIR)

    files = []
    files.append(FILES)

    for url, file_name in FILES:
	rel_file_name = '%s/%s'%(DATA_DIR, file_name)

	if os.path.exists(rel_file_name) and not force_download:
	    print('Already downloaded file: %s'%(file_name))
	    continue

	print('Downloading file: %s'%(file_name))

	req = urllib2.urlopen(url)
	f = open(rel_file_name, 'w')
	f.write(req.read())
	f.close()


if __name__ == "__main__":
    download_all_modis_files()
    download_data()
