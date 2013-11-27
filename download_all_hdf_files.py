#!/usr/bin/python
import os
import datetime
from ftplib import FTP
import project_settings as settings

DATA_DIR_TPL = settings.DATA_DIR_TPL

class ModisDataDownloader:
    def __init__(self, mode='AQUA'):
	self.ftp = FTP('n4ftl01u.ecs.nasa.gov')
	self.ftp.login()
	self.mode = mode

	if self.mode == 'AQUA':
	    self.ftp.cwd('/MOSA/MYD10A1.005/')
	elif self.mode == 'TERRA':
	    self.ftp.cwd('/MOST/MOD10A1.005/')

    def download_all_files(self, tile, start_date, end_date):
	self.data_dir = DATA_DIR_TPL%"%s_%s_%i"%(self.mode, tile, start_date.year)
	if not os.path.exists(self.data_dir):
	    os.makedirs(self.data_dir)

	hdf_files_for_tile = []

	daily_dirs = []
	date = start_date
	while date < end_date + datetime.timedelta(1):
	    daily_dirs.append(date.strftime('%Y.%m.%d'))
	    date += datetime.timedelta(1)

	for daily_dir in daily_dirs:
	    print daily_dir
	    self.ftp.cwd(daily_dir)
	    try:
		all_lines = []
		self.ftp.dir(all_lines.append)

		all_files = [l.split()[8] for l in all_lines[1:]]	
		hdf_files = [f for f in all_files if f.split('.')[-1] == 'hdf']
		hdf_file_for_tile = [f for f in hdf_files if f.split('.')[2] == tile]

		if len(hdf_file_for_tile) != 1:
		    print "Problem downloading", hdf_file_for_tile
		    raise Exception('0 or more than one hdf file found')

		hdf_file = hdf_file_for_tile[0]
		hdf_files_for_tile.append(hdf_file)

		if os.path.exists(self.data_dir + hdf_file):
		    print('File already exists')
		else:
		    print('Downloading file %s'%(hdf_file))
		    self.ftp.retrbinary('RETR %s'%(hdf_file), open(self.data_dir + hdf_file, 'wb').write)
	    except Exception, e:
		print e

	    self.ftp.cwd('..')

	return hdf_files_for_tile	

def download_all_files():
    mdd = ModisDataDownloader('TERRA')
    start_date = datetime.datetime(2005, 01, 01)
    end_date = datetime.datetime(2005, 12, 31)
    hdf_files_for_tile = mdd.download_all_files('h09v05', start_date, end_date)

if __name__ == "__main__":
    download_all_files()

