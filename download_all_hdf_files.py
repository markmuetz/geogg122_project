#!/usr/bin/python
import os
from ftplib import FTP

DATA_DIR_TPL = '/media/E6F08871F08849AF/geogg122_data/%s/'

class ModisDataDownloader:
    def __init__(self):
	self.ftp = FTP('n4ftl01u.ecs.nasa.gov')
	self.ftp.login()

	self.ftp.cwd('/MOSA/MYD10A1.005/')

    def download_all_files(self, tile, start_year, end_year):
	self.data_dir = DATA_DIR_TPL%"%s_%s_%s"%(tile, start_year, end_year)
	if not os.path.exists(self.data_dir):
	    os.makedirs(self.data_dir)

	hdf_files_for_tile = []

	dirs = []
	self.ftp.dir(dirs.append)
	years = [str(y) for y in range(start_year, end_year + 1)]
	all_daily_dirs = [l.split()[8] for l in dirs[1:]]
	daily_dirs = [dd for dd in all_daily_dirs if (dd.split('.')[0] in years)]

	for daily_dir in daily_dirs:
	    print daily_dir
	    self.ftp.cwd(daily_dir)
	    all_lines = []
	    self.ftp.dir(all_lines.append)

	    all_files = [l.split()[8] for l in all_lines[1:]]	
	    hdf_files = [f for f in all_files if f.split('.')[-1] == 'hdf']
	    hdf_file_for_tile = [f for f in hdf_files if f.split('.')[2] == tile]

	    if len(hdf_file_for_tile) != 1:
		print hdf_file_for_tile
		raise Exception('0 or more than one hdf file found')

	    hdf_file = hdf_file_for_tile[0]
	    hdf_files_for_tile.append(hdf_file)

	    if os.path.exists(self.data_dir + hdf_file):
		print('File already exists')
	    else:
		print('Downloading file %s'%(hdf_file))
		self.ftp.retrbinary('RETR %s'%(hdf_file), open(self.data_dir + hdf_file, 'wb').write)

	    self.ftp.cwd('..')

	return hdf_files_for_tile	

if __name__ == "__main__":
    mdd = ModisDataDownloader()
    hdf_files_for_tile = mdd.download_all_files('h09v05', 2009, 2010)
