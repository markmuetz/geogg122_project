#!/usr/bin/python
import os
import pickle
import random
import glob
import logging
import datetime as dt
import pylab as plt
import numpy as np
import numpy.ma as ma
import gdal
from scipy import interpolate

from external.raster_mask import raster_mask2
from external.helpers import daterange

from make_movie import make_movie
import project_settings as settings

log = logging.getLogger('prepare')

def load_snow_hdf_data(start_date, end_date, tile='h09v05', 
        datasets=('AQUA', 'TERRA'), 
        mask_shape_file="Hydrologic_Units/HUC_Polygons.shp",
        force_reload=False, start_doy=0, end_doy=366):
    '''Loads HDF files in settings.DATA_DIR for spec. tile and year. 

    Caches results, and will load this if it exists unless force_reload 
    is True.

    Returns a dict: 'dates' is all dates in range, 'data is a
    masked numpy array of shape (365 * 2, mask.shape[0], mask.shape[1]). 
    Mask is determined by mask_shape_file. Each element is a 2D numpy array
    of the catchment area and the default is to order them so as they go:
    [AQUA, TERRA, AQUA, TERRA...]
    '''
    log.info("  Loading datasets %s for tile %s"%(str(datasets), tile))
    log.info("  Daterange: %s to %s"%(str(start_date), str(end_date)))

    # Loading all the files can take a while. Read from a pickled cache if possible.
    cache_dir = "%s/cache"%settings.DATA_DIR
    cached_data_file = "%s/load_hdf_data_%s-%s.pkl"%(cache_dir, start_date, end_date)
    if os.path.exists(cached_data_file) and not force_reload:
        log.info('  Loading data from cache')
        data = pickle.load(open(cached_data_file, 'rb'))
        return data

    # Template that will be used to grab data.
    hdf_tpl = 'HDF4_EOS:EOS_GRID:"%s":MOD_Grid_Snow_500m:Fractional_Snow_Cover'
    all_frac_snow_data = []

    # Generate a mask based on the catchment area.
    # Pick any hdf file to use as its input.
    file_search_path = '%s/%s_%s_%s/'%(settings.DATA_DIR, datasets[0], tile, start_date.year) +\
                       "*.A%04i???.*.hdf"%(start_date.year)
    file_name = glob.glob(file_search_path)[0]
    hdf_str = hdf_tpl%(file_name)

    # Taken from course notes.
    mask = raster_mask2(hdf_str, 
        target_vector_file="%s/%s"%(settings.DATA_DIR, mask_shape_file),
        attribute_filter=2)

    # Work out mins and maxes based on mask.
    mask_bounds = np.where(mask == False)
    ymin = int(min(mask_bounds[0]))
    ymax = int(max(mask_bounds[0]) + 1)
    xmin = int(min(mask_bounds[1]))
    xmax = int(max(mask_bounds[1]) + 1)

    dates = []
    for date in daterange(start_date, end_date):
        dates.append(date)
        year = date.year
        doy = date.timetuple().tm_yday

        if doy % 10 == 0:
            log.info("    Processing doy: %03i"%doy)

        for dataset in datasets:
            # e.g. '/path/to/data/AQUA_h09v05_2005/
            data_dir  = '%s/%s_%s_%s/'%(settings.DATA_DIR, dataset, tile, year)

            file_names = glob.glob(data_dir + "*.A%04i%03i.*"%(year, doy))
            if len(file_names) == 0:
                log.info("MISSING %s doy %i"%(dataset, doy))
                dummy_data = ma.array(np.zeros((ymax - ymin, xmax - xmin)), 
                                      mask = mask[ymin:ymax, xmin:xmax])
                dummy_data[:, :] = 250 # Missing value code.
                all_frac_snow_data.append(dummy_data)
            else:
                try:
                    file_name = file_names[0]
                    hdf_str = hdf_tpl%(file_name)

                    g = gdal.Open(hdf_str)

                    # Only read the data I want based on mins/maxes.
                    frac_snow_data = g.ReadAsArray(yoff=ymin, ysize=ymax-ymin, 
                                                   xoff=xmin, xsize=xmax-xmin)
                    # alternative, reads whole dataset and slower.
                    # frac_snow_data = g.ReadAsArray() 

                    # Reduce the size of the mask so as it fits the data 
                    # pulled from HDF.
                    masked_frac_snow_data = ma.array(frac_snow_data, 
                                            mask = mask[ymin:ymax, xmin:xmax])
                    all_frac_snow_data.append(masked_frac_snow_data)
                except KeyboardInterrupt:
                    raise
                except:
                    print('COULD NOT LOAD FILE: %s'%(file_name.split('/')[-1]))
                    dummy_data = ma.array(np.zeros((ymax - ymin, xmax - xmin)), 
                                          mask = mask[ymin:ymax, xmin:xmax])
                    dummy_data[:, :] = 250 # Missing value code.
                    all_frac_snow_data.append(dummy_data)

    dates = np.array(dates)
    data = ma.array(all_frac_snow_data)
    return_data = {'dates': dates, 'data': data}

    if True: # caching disabled temporarily.
        try:
            log.info('  Saving data to cache')
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            pickle.dump(return_data, open(cached_data_file, 'wb'))
        except:
            log.error('  Could not save data to cache')
    return return_data

def interp_data_over_time(masked_data, orig_mask, plot_random_values=False):
    '''Takes in masked_data and applies interpolation over the first axis

    First axis is assumed to be time. 
    '''
    # Make an array to stick all the interpolated results into.
    # Note it gets *just* the catchtment area mask, not the QC mask.
    interp_masked_data = ma.array(np.zeros_like(masked_data),  mask=orig_mask)

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
                    interp_f = interpolate.interp1d(x_masked, y_masked, bounds_error=False)
                    interp_masked_data[:, pixel[0], pixel[1]] = interp_f(x)
                    # plots a random interpolation based on a percentage chance.
                    if plot_random_values and random.random() > 0.999:
                        plt.plot(x, interp_f(x))
                        plt.show()
                except Exception, e:
                    print("COULD NOT INTERP PIXEL(%i, %i)"%(pixel[0], pixel[1]))
                    print(e)
                    pass

        if i % 10 == 0:
            log.info("    Done %2.1f percent"%(100.0 * i / masked_data.shape[1]))
    return interp_masked_data

def apply_MODIS_snow_quality_control(data):
    '''Qualitcy control key taken from page 11 of this document:
    http://modis-snow-ice.gsfc.nasa.gov/uploads/sug_c5.pdf

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
    255=fill'''
    data[data == 254] = 100
    return ma.array(data, mask=data > 100)

def prepare_all_snow_data(start_date, end_date, should_make_movie=False, plot_graphs=False):
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
    dates = all_data['dates']
    for dataset in ('AQUA', 'TERRA', 'COMBINED'):
        title = dataset
        if dataset == 'AQUA':
            data = snow_data[::2, :, :] # AQUA
            # Mask out data that is higher than 100: all QC data.
            masked_data = apply_MODIS_snow_quality_control(data)
        elif dataset == 'TERRA':
            data = snow_data[1::2, :, :] # TERRA
            # Mask out data that is higher than 100: all QC data.
            masked_data = apply_MODIS_snow_quality_control(data)
        elif dataset == 'COMBINED':
	    print snow_data.shape
            data = snow_data.reshape(snow_data.shape[0] / 2, 2, snow_data.shape[1], snow_data.shape[2]).mean(axis=1)
            masked_data = apply_MODIS_snow_quality_control(snow_data)
            masked_data = masked_data.reshape(masked_data.shape[0] / 2, 2, masked_data.shape[1], masked_data.shape[2]).mean(axis=1)

        # N.B masked_data has a mask that will has filtered out
        # QC values. I don't want this, so use the original mask.
        log.info('  Interpolating %s data', dataset)
        interp_masked_data = interp_data_over_time(masked_data, data.mask)

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
                percent_snow_cover = 100. * total_snow_cover / np.max(total_snow_cover)

            if plot_graphs:
                plt.plot(percent_snow_cover, label=title)

            all_data["%s_total_snow"%dataset] = total_snow_cover
        except:
            log.warn('Could not produce percent snow cover for %s'%dataset)

    return all_data

def prepare_temperature_data(start_date, end_date, plot_graphs=False):
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
    f = interpolate.interp1d(x[temp_data_in_range], 
                             av_temp_data_in_range[temp_data_in_range],
                             bounds_error=False)

    interp_av_data_in_range = (f(x) - 32) * 5 / 9 # convert to C

    if plot_graphs:
        plt.title('Temperature data from %s to %s'%(start_date, end_date))
        plt.plot(interp_av_data_in_range)

    return interp_av_data_in_range

def is_in_date_range(date_string, start_date, end_date):
    '''Compares a datestring in format %Y-%m-%d with a date range'''
    date = dt.datetime.strptime(date_string, '%Y-%m-%d')
    return start_date < date < end_date + dt.timedelta(1)

# np.where(...) won't work unless you vectorise it first.
vec_is_in_date_range = np.vectorize(is_in_date_range)

def prepare_discharge_data(start_date, end_date, plot_graphs=False):
    '''Loads in discharge data between dates provided.'''
    log.info('Preparing discharge data')
    discharge_data = np.loadtxt('%s/delnorte.dat'%settings.DATA_DIR, usecols=(2, 3), unpack=True, dtype=str)

    date_range = np.where(vec_is_in_date_range(discharge_data[0], start_date, end_date))[0]
    # Convert from cubic feet to m^3
    discharge_data_in_range = discharge_data[1, date_range].astype(float) * 0.028316846 

    if plot_graphs:
        plt.title('Discharge data from %s to %s'%(start_date, end_date))
        plt.plot(100.0 * discharge_data_in_range / np.max(discharge_data_in_range))

    return discharge_data_in_range

def prepare_all_data():
    plot_graphs = True
    start_date = settings.START_DATE
    end_date = settings.END_DATE

    data = {}

    data['temperature'] = prepare_temperature_data(start_date, end_date, plot_graphs)
    data['discharge']   = prepare_discharge_data(start_date, end_date, plot_graphs)
    data['snow']        = prepare_all_snow_data(start_date, end_date, plot_graphs=plot_graphs)

    if plot_graphs:
        plt.show()

    return data

if __name__ == "__main__":
    prepare_all_data()
