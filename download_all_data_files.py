#!/usr/bin/python
import os.path
import urllib2
from find_all_hdf_files import ModisDataDownloader

DATA_DIR = 'data_files'

FILES = [('http://txpub.usgs.gov/USACE/data/water_resources/Hydrologic_Units.zip', 'Hydrologic_Units.zip'),
	 ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delnorte.dat', 'delnorte.dat'),
	 ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delNorteT.dat', 'delnorteT.dat')]

def download_data():
    if not os.path.exists(DATA_DIR):
	os.makedirs(DATA_DIR)

    files = []
    files.append(FILES)

    for url, file_name in FILES:
	rel_file_name = '%s/%s'%(DATA_DIR, file_name)

	if os.path.exists(rel_file_name):
	    print('Already downloaded file: %s'%(file_name))
	    continue

	print('Downloading file: %s'%(file_name))

	req = urllib2.urlopen(url)
	f = open(rel_file_name, 'w')
	f.write(req.read())
	f.close()

if __name__ == "__main__":
    download_data()
