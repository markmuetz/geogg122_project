#!/usr/bin/python
import os
import pickle
import random
import glob
import logging
import datetime as dt
import csv

import pylab as plt
import numpy as np
import numpy.ma as ma
import gdal
from scipy import interpolate
import matplotlib

from external.raster_mask import raster_mask2
from external.helpers import daterange

from make_movie import make_movie
import project_settings as settings

log = logging.getLogger('prepare')

# N.B. all datasets in an HDF gan be found by opening the .hdf file
# using:
# g = gdal.Open(file_name)
# g.GetSubDatasets()
# These MODIS Terra/Aqua HDF files have 4 datasets in them.
# I'm only interested in these 2 though.
FRAC_SNOW_COVER_TPL = 'HDF4_EOS:EOS_GRID:"%s":MOD_Grid_Snow_500m:Fractional_Snow_Cover'
QA_TPL              = 'HDF4_EOS:EOS_GRID:"%s":MOD_Grid_Snow_500m:Snow_Spatial_QA'

def load_snow_hdf_data(start_date, end_date, tile='h09v05', 
        datasets=('AQUA', 'TERRA'), 
        mask_shape_file="Hydrologic_Units/HUC_Polygons.shp",
        start_doy=0, end_doy=366):
    '''Loads HDF files in settings.DATA_DIR for spec. tile and year. 

    Caches results, and will load this if it exists if settings.ENABLE_CACHE 
    is True.

    Returns a dict: 'dates' is all dates in range, 'data is a
    masked numpy array of shape (365 * 2, mask.shape[0], mask.shape[1]). 
    Mask is determined by mask_shape_file. Each element is a 2D numpy array
    of the catchment area and the default is to order them so as they go:
    [AQUA, TERRA, AQUA, TERRA...]
    '''
    log.info("  Loading datasets %s for tile %s"%(str(datasets), tile))
    log.info("  Daterange: %s to %s"%(str(start_date), str(end_date)))

    # Loading all the files can take a while.
    # Read from a pickled cache if possible.
    cache_dir = "%s/cache"%settings.DATA_DIR
    cached_data_file = "%s/load_hdf_data_%s-%s.pkl"%(cache_dir,
	                                             start_date, end_date)
    if os.path.exists(cached_data_file) and settings.ENABLE_CACHE:
        log.info('  Loading data from cache')
        try:
            data = pickle.load(open(cached_data_file, 'rb'))
            return data
        except:
            log.warn("  COULDN'T LOAD DATA FROM CACHE")

    all_frac_snow_data = []
    all_qa_data = []

    # Generate a mask based on the catchment area.
    # Pick any hdf file to use as its input.
    file_search_path = '%s/%s_%s_%s/'%(settings.DATA_DIR, datasets[0], tile, 
		       start_date.year) + "*.A%04i???.*.hdf"%(start_date.year)
    file_name = glob.glob(file_search_path)[0]
    hdf_str = FRAC_SNOW_COVER_TPL%(file_name)

    # Taken from course notes.
    catchment_mask = raster_mask2(hdf_str, 
        target_vector_file="%s/%s"%(settings.DATA_DIR, mask_shape_file),
        attribute_filter=2)

    # Work out mins and maxes based on mask.
    mask_bounds = np.where(catchment_mask == False)
    ymin = int(min(mask_bounds[0]))
    ymax = int(max(mask_bounds[0]) + 1)
    xmin = int(min(mask_bounds[1]))
    xmax = int(max(mask_bounds[1]) + 1)

    # Reduce size of mask so it will fit data I read from HDFs.
    catchment_mask = catchment_mask[ymin:ymax, xmin:xmax]

    dates = []
    for date in daterange(start_date, end_date):
        dates.append(date)
        year = date.year
        doy = date.timetuple().tm_yday

        if doy % 10 == 0:
            log.info("    Processing year, doy: %04i, %03i"%(year, doy))

        for dataset in datasets:
            # e.g. '/path/to/data/AQUA_h09v05_2005/
            data_dir  = '%s/%s_%s_%s/'%(settings.DATA_DIR, dataset, tile, year)

            file_names = glob.glob(data_dir + "*.A%04i%03i.*"%(year, doy))
            read_data_successful = False
            if len(file_names) == 0:
		log.info("MISSING %s year, doy: %04i, %03i"%(dataset, 
		                                             year, doy))
            else:
                try:
                    file_name = file_names[0]
                    frac_snow_data, qa_data = load_hdf_file(file_name, 
			                 catchment_mask, xmin, xmax, ymin, ymax)
                    all_frac_snow_data.append(frac_snow_data)
                    all_qa_data.append(qa_data)
                    read_data_successful = True
                except KeyboardInterrupt:
                    # So as ctrl-c works.
                    raise
                except Exception, e:
		    file_name = file_name.split('/')[-1]
                    log.warn('COULD NOT LOAD FILE: %s'%(file_name))
                    log.warn('Exception: %s'%(e))

            if not read_data_successful:
                dummy_data = \
		    ma.array(np.zeros((ymax - ymin, xmax - xmin)).astype(int), 
                                      mask=catchment_mask)
                dummy_qa_data = \
		    ma.array(np.zeros((ymax - ymin, xmax - xmin)).astype(int), 
                                      mask=catchment_mask)
		# Note to self: settings dummy_data[:, :] = 200 will 
		# get rid of mask entirely and leave you scratching your
		# head as to why this mask doesn't work.
		# Only set the values where the mask is False.
                dummy_data[~catchment_mask]    = 200 # Missing value code.
                dummy_qa_data[~catchment_mask] = 1   # 'Other' quality
                all_frac_snow_data.append(dummy_data)
                all_qa_data.append(dummy_qa_data)


    dates   = np.array(dates)
    data    = ma.array(all_frac_snow_data)
    qa_data = ma.array(all_qa_data)
    return_data = {'dates': dates, 'data': data, 'qa': qa_data}

    if settings.ENABLE_CACHE:
        try:
            log.info('  Saving data to cache')
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            pickle.dump(return_data, open(cached_data_file, 'wb'))
        except:
            log.error('  Could not save data to cache')
    return return_data

def load_hdf_file(file_name, catchment_mask, xmin, xmax, ymin, ymax):
    array_data = []
    for tpl in (FRAC_SNOW_COVER_TPL, QA_TPL):
        hdf_str = tpl%(file_name)

        g = gdal.Open(hdf_str)

        # Only read the data I want based on mins/maxes.
        data = g.ReadAsArray(yoff=ymin, ysize=ymax-ymin, 
                                       xoff=xmin, xsize=xmax-xmin)
        # alternative, reads whole dataset and slower.
        # frac_snow_data = g.ReadAsArray() 
        masked_data = ma.array(data, mask=catchment_mask)
        array_data.append(masked_data)

    return array_data[0], array_data[1]

def interp_data_over_time(masked_data, qa_data, orig_mask):
    '''Takes in masked_data and applies interpolation over the first axis

    First axis is assumed to be time. 
    '''
    # Make an array to stick all the interpolated results into.
    # Note it gets *just* the catchment area mask, not the QC mask.
    interp_masked_data = ma.array(np.zeros_like(masked_data),  mask=orig_mask)
    qa_mask = qa_data == 1
    masked_data.mask |= qa_mask

    x = np.arange(len(masked_data))

    # For each pixel in array work out its full interpolated time series.
    for i in range(masked_data.shape[1]):
        for j in range(masked_data.shape[2]):
            pixel = (i, j)
            y = masked_data.data[:, pixel[0], pixel[1]]
            # Mask out values from x, y which are masked in data.
            y_masked = y[~masked_data.mask[:, pixel[0], pixel[1]]]
            x_masked = x[~masked_data.mask[:, pixel[0], pixel[1]]]

            if len(x_masked) > 2:
                try:
                    # Turn off bounds errors.
                    interp_f = interpolate.interp1d(x_masked, y_masked, 
			                            bounds_error=False)
                    interp_masked_data[:, pixel[0], pixel[1]] = interp_f(x)
                except Exception, e:
                    log.error("COULD NOT INTERP PIXEL(%i, %i)"%(pixel[0], 
			                                        pixel[1]))
                    log.error(e)

        if i % 10 == 0:
            log.info("    Done %2.1f%%"%(100.0 * i / masked_data.shape[1]))
    return interp_masked_data

def apply_MODIS_snow_quality_control(data, qa_data):
    '''fractional_snow_data key taken from page 11 of this document:
    http://modis-snow-ice.gsfc.nasa.gov/uploads/sug_c5.pdf

    This method prints some interesting stats about the number of 
    data points with given values, sets all saturated values to 100,
    then masks out all low quality data

    fractional_snow_data key:
    0-100=fractional 
    snow, 
    200=missing data, 
    201=no decision, 
    211=night, 
    225=land, 
    237=inland water, 
    239=ocean, 
    250=cloud, 
    254=detector saturated, 
    255=fill
    
    Snow_Cover_Pixel_QA key:
    0=good quality, 
    1=other quality, 
    252=Antarctica mask, 
    253=land mask, 
    254=ocean mask saturated, 
    255=fill 
    '''
    # Log saturated values count.
    log.info("  Saturated value count: %d"%(data == 254).sum()) # == 2138
    # Assume that a saturated detector is full snow cover.
    # TODO: not sure I can justify this.
    data[data == 254] = 100 

    # Log hi/lo quality counts.
    # For our data, hi/lo ~= 20. So there are more
    # high qual data points than lo. I've ignored the low qual
    # values for all subsequent processing, but a more complete
    # way of dealing with them would be to include them, but give
    # them a lower weight.
    hi, lo = (qa_data == 0).sum(), (qa_data == 1).sum()
    log.info("  Hi qual: %d, Low qual: %d, hi/lo: %4.1f"%(hi, lo, 1. * hi / lo))
    # Mask out low quality QA data. 
    # N.B. I've assumed that the dataset Snow_Spatial_QA (g.GetSubDatasets())
    # is the same as Snow_Cover_Pixel_QA (document in function description)
    qa_mask = qa_data == 1

    return ma.array(data, mask=(data > 100) | qa_mask)

def prepare_all_snow_data(start_date, end_date, should_make_movie=False):
    '''Loads and prepares all snow data between date range.
    Can optionally make a movie of the snow data too.

    Calculates 3 datasets: 'AQUA', 'TERRA' and 'COMBINED'
    COMBINED is a daily mean of the first 2.

    All data is additionally masked for Qual. Control, and
    interpolated over to fill in all values for e.g. cloud cover.
    Also produces a summed percent snow cover.

    Returns a dictionary with all relevant data in it.
    '''
    log.info('Preparing all snow data')
    all_data = load_snow_hdf_data(start_date, end_date)
    snow_data = all_data['data']
    qa_data = all_data['qa']
    dates = all_data['dates']
    #for dataset in ('AQUA', 'TERRA', 'COMBINED'):
    for dataset in ('COMBINED',):
        title = dataset
        if dataset == 'AQUA':
            data = snow_data[::2, :, :] # AQUA
            masked_data = apply_MODIS_snow_quality_control(data, qa_data)
        elif dataset == 'TERRA':
            data = snow_data[1::2, :, :] # TERRA
            masked_data = apply_MODIS_snow_quality_control(data, qa_data)
        elif dataset == 'COMBINED':
	    # snow_data is filled with data from AQUA and TERRA, as in e.g.:
	    # AQUA, TERRA, AQUA, TERRA... with shape == (365*2 * w * h)
	    # What I want is to first double up the data so as its shape
	    # becomes (365, 2, w, h), then take a mean over the 2nd axis.
	    # This combines the 2 datasets in a way that preserves the mask,
	    # and if either of the datasets has a value this will be used.
            data = snow_data.reshape(snow_data.shape[0] / 2, 2, 
		     snow_data.shape[1], snow_data.shape[2]).mean(axis=1)

	    # Apply the modeis QC rules.
            masked_data = apply_MODIS_snow_quality_control(snow_data, qa_data)

	    # Same trick as above.
            masked_data = masked_data.reshape(masked_data.shape[0] / 2, 2, 
		      masked_data.shape[1], masked_data.shape[2]).mean(axis=1)

	    # Same trick as above.
            qa_data = qa_data.reshape(qa_data.shape[0] / 2, 2, q
		               a_data.shape[1], qa_data.shape[2]).mean(axis=1)

        # N.B masked_data has a mask that will has filtered out
        # QC values. I don't want this, so use the original mask.
        log.info('  Interpolating %s data', dataset)
        interp_masked_data = interp_data_over_time(masked_data, 
		                                   qa_data, data.mask)

        if should_make_movie and dataset == 'COMBINED':
            # Note you can downscale temporal/spatial dims for speed.
            make_movie("%s Snow Cover"%dataset, "imgs", 
                       "%s_snow_cover"%dataset, 
                       100 - interp_masked_data[:,:,:], 
                       dates, 0.0, 100.0)
        
        all_data[dataset] = interp_masked_data

        total_snow_cover = interp_masked_data.sum(axis=2).sum(axis=1)
        try:
            if dataset == 'COMBINED':
                percent_snow_cover = 100. * total_snow_cover / \
			 np.max(total_snow_cover[~np.isnan(total_snow_cover)])

            else:
                percent_snow_cover = 100. * total_snow_cover / \
			 np.max(total_snow_cover)

            all_data["%s_total_snow"%dataset] = total_snow_cover
            all_data["%s_percent_snow"%dataset] = percent_snow_cover
        except:
            log.warn('Could not produce percent snow cover for %s'%dataset)

    return all_data

def prepare_temperature_data(start_date, end_date):
    '''Loads in temperature data between dates provided.'''
    log.info('Preparing temperature data')
    temp_data = np.loadtxt('%s/delnorteT.dat'%settings.DATA_DIR, 
                           unpack=True, 
                           dtype=str)[:, 1:] # First val should be skipped.
    dates = []
    for i in range(temp_data.shape[1]):
        dates.append("-".join(temp_data[:3, i]))
    dates = np.array(dates)

    date_range = np.where(vec_is_in_date_range(dates, start_date, end_date))[0]
    temp_data_in_range = temp_data[3:5, date_range].astype(float)

    # temp_data_for_year is a min and max: take its average.
    av_temp_data_in_range = temp_data_in_range.mean(axis=0)

    # There are some values that will need interpolation.
    temp_data_in_range = av_temp_data_in_range < 1000
    x = np.arange(len(av_temp_data_in_range))
    # Turn off bounds errors.
    # You need to be a little bit careful with this: it returns nan if 
    # you pass in a value of x that it can't handle. One way of handling this 
    # would be to interp over a slightly larger range, i.e. year +/- 1 month.
    f = interpolate.interp1d(x[temp_data_in_range], 
                             av_temp_data_in_range[temp_data_in_range],
                             bounds_error=False)

    interp_av_data_in_range = (f(x) - 32) * 5 / 9 # convert to C

    return interp_av_data_in_range

def is_in_date_range(date_string, start_date, end_date):
    '''Compares a datestring in format %Y-%m-%d with a date range'''
    date = dt.datetime.strptime(date_string, '%Y-%m-%d')
    return start_date < date < end_date + dt.timedelta(1)

# np.where(...) won't work unless you vectorise it first.
vec_is_in_date_range = np.vectorize(is_in_date_range)

def prepare_discharge_data(start_date, end_date):
    '''Loads in discharge data between dates provided.'''
    log.info('Preparing discharge data')
    discharge_data = np.loadtxt('%s/delnorte.dat'%settings.DATA_DIR, 
	                        usecols=(2, 3), unpack=True, dtype=str)

    date_range = np.where(vec_is_in_date_range(discharge_data[0], 
	                                       start_date, end_date))[0]
    # Convert from cubic feet to m^3
    discharge_data_in_range = discharge_data[1, date_range].astype(float)\
	                      * 0.028316846 

    return discharge_data_in_range

def prepare_precip_data(start_date, end_date):
    '''Loads in precipitation data between dates provided.'''
    log.info('Preparing precipitation data')
    def convert_date(date_str):
        return dt.datetime.strptime(date_str, '%Y%m%d')
    vec_c_d = np.vectorize(convert_date)

    csvr = csv.reader(open('data_files/creede_water_treatment_data.csv', 'r'))

    lines = []
    for line in csvr:
        lines.append(line)
        
    lines = np.array(lines)

    precip = lines[1:, 21].astype(int)
    precip_masked = np.ma.array(precip, mask=precip == -9999)

    dates = vec_c_d(lines[1:, 5])

    date_mask = (dates >= start_date) & (dates <= end_date)

    x = np.arange(len(precip_masked[date_mask]))
    y_masked = precip_masked[date_mask].data[~precip_masked[date_mask].mask]
    x_masked = x[~precip_masked[date_mask].mask]
    f = interpolate.interp1d(x_masked, y_masked, bounds_error=False)
    y = f(x)

    return y

def prepare_all_data():
    """Prepares MODIS, temperature, discharge and snow data
uses settings to get its date ranve. 

returns a dict with the following keys: precip, temperature, discharge and snow.
"""
    start_date = settings.START_DATE
    end_date = settings.END_DATE

    data = {}

    data['precip']      = prepare_precip_data(start_date, end_date)
    data['temperature'] = prepare_temperature_data(start_date, end_date)
    data['discharge']   = prepare_discharge_data(start_date, end_date)
    data['snow']        = prepare_all_snow_data(start_date, end_date)

    return data

if __name__ == "__main__":
    prepare_all_data()
