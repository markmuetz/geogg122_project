#!/usr/bin/python
import os.path
import urllib2

DATA_DIR = 'data_files'

FILES = [('http://txpub.usgs.gov/USACE/data/water_resources/Hydrologic_Units.zip', 'Hydrologic_Units.zip'),
	 ('ftp://n5eil01u.ecs.nsidc.org/SAN/MOST/MOD10A1.005/2007.01.01/MOD10A1.A2007001.h00v08.005.2008133193943.hdf', 'MOD10A1.A2007001.h00v08.005.2008133193943.hdf'),
	 ('ftp://n5eil01u.ecs.nsidc.org/SAN/MOST/MOD10A1.005/2007.01.01/MOD10A1.A2007001.h14v04.005.2008133182715.hdf', 'MOD10A1.A2007001.h14v04.005.2008133182715.hdf')]

def download_data():
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
