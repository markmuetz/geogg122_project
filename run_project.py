#!/usr/bin/python
import pylab as plt

import project_settings as settings
import download
import prepare
import prepare_time_series_data
from download import ModisDataDownloader

def main():
    if settings.RUN_DOWNLOAD_FILES:
	download.download_data()

    if settings.RUN_DOWNLOAD_HDF_FILES:
	start_date = settings.START_DATE
	end_date = settings.END_DATE

	for dataset in settings.MODIS_DATASETS:
	    mdd = ModisDataDownloader(dataset)
	    hdf_files_for_tile = mdd.download_all_files(settings.TILE, start_date, end_date)
    
    if settings.RUN_DATA_PREPARATION:
	prepare.main()


if __name__ == "__main__":
    main()
