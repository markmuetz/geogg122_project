#!/usr/bin/python
import os.path
import urllib2

DATA_DIR = 'data_files'

FILES = [('http://txpub.usgs.gov/USACE/data/water_resources/Hydrologic_Units.zip', 'Hydrologic_Units.zip'),
	('ftp://n4ftl01u.ecs.nasa.gov/MOSA/MYD10A1.005/2006.01.01/MYD10A1.A2006001.h09v05.005.2008094205217.hdf', 'MYD10A1.A2006001.h09v05.005.2008094205217.hdf'),
	 ('ftp://n5eil01u.ecs.nsidc.org/SAN/MOST/MOD10A1.005/2007.01.01/MOD10A1.A2007001.h00v08.005.2008133193943.hdf', 'MOD10A1.A2007001.h00v08.005.2008133193943.hdf'),
	 ('ftp://n5eil01u.ecs.nsidc.org/SAN/MOST/MOD10A1.005/2007.01.01/MOD10A1.A2007001.h14v04.005.2008133182715.hdf', 'MOD10A1.A2007001.h14v04.005.2008133182715.hdf'),
	 ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delnorte.dat', 'delnorte.dat'),
	 ('http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122/Chapter6a_Practical/data/delNorteT.dat', 'delnorteT.dat')]

def download_data():
    if not os.path.exists(DATA_DIR):
	os.makedirs(DATA_DIR)

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
