#!/usr/bin/python
import pylab as plt

import project_settings as settings
import download_all_data_files
import prepare_hdf_files
import prepare_time_series_data
from download_all_hdf_files import ModisDataDownloader

def main():
    if settings.RUN_DOWNLOAD_FILES:
	download_all_data_files.download_data()

    if settings.RUN_DOWNLOAD_HDF_FILES:
	start_date = settings.START_DATE
	end_date = settings.END_DATE

	for mode in settings.SATELLITE_DATA:
	    mdd = ModisDataDownloader(mode)
	    hdf_files_for_tile = mdd.download_all_files(settings.TILE, start_date, end_date)
    
    if settings.RUN_DATA_PREPARATION:
	prepare_hdf_files.main()
	prepare_time_series_data.prepare_discharge_data(2005)
	prepare_time_series_data.prepare_temperature_data(2005)
	plt.show()


if __name__ == "__main__":
    main()
