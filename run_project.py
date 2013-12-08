#!/usr/bin/python
import os
import logging
import datetime as dt
try:
    import pylab as plt
    import gdal
    import scipy
    import numpy
    import pylab
    from subprocess import check_output
except:
    print("""You will need to install the following libs to run this project
On Ubuntu: 
sudo aptitude install python-gdal python-scipy python-numpy python-matplotlib

To make movies, you also need the imagemagick tools:
sudo aptitude install imagemagick
 """)
    raise

import project_settings as settings
import download
import prepare
import calibrate
import apply_model
from results import Results

log = logging.getLogger('run_project')

def run():
    '''Entry point for project. 
    
    ***Make sure you've set up project_settings.py before calling***

    * Configures logging
    * Downloads all files needed for date range
    * Prepares data
    * Applies model to data
    * Checks model against (dfferent) data
    * Outputs results (graphs/stats etc.)
    '''
    if not os.path.exists('logs'):
	os.makedirs('logs')
    # Configure logging.
    # Taken from: http://docs.python.org/2/howto/logging-cookbook.html 
    logging.basicConfig(filename='logs/geogg122_project.log', 
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        level=logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')

    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    log.info('Started at %s'%dt.datetime.now()) 
    log.info('Using settings:') 
    for prop in dir(settings):
        if prop[0].isupper():
            logging.info('  %s: %s'%(prop, getattr(settings, prop)))
    git_revision = check_output(['git', 'rev-parse', 'HEAD']).strip()
    log.info('git revision: %s'%git_revision)
    if check_output(['git', 'status', '--porcelain']) == '':
        log.info('  No uncommitted changes')
    else:
        log.warn('  Uncommitted changes')

    results = Results()

    if settings.RUN_DOWNLOAD_FILES:
        log.info('Downloading data') 
        download.download_data()

    if settings.RUN_DOWNLOAD_MODIS_FILES:
        log.info('Downloading MODIS files') 
        download.download_all_modis_files()
    
    if settings.RUN_DATA_PREPARATION:
        log.info('Preparing data') 
        data = prepare.prepare_all_data()
	results.set_preparation_data(data)

    if settings.RUN_MODEL_CALIBRATION:
        log.info('Calibrating model')
        cal_data = calibrate.calibrate_model(data, 
		       settings.CAL_START_DATE, settings.CAL_END_DATE)
	results.set_cal_data(cal_data)

    if settings.RUN_MODEL_APPLICATION:
        log.info('Applying model to new data')
        apply_data = apply_model.apply_model(data, cal_data, 
		         settings.APP_START_DATE, settings.APP_END_DATE)
	results.set_apply_data(apply_data)

    results.generate_results()
    return results

if __name__ == "__main__":
    run()
