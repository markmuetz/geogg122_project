#!/usr/bin/python
import os
import pickle
import random
import gdal
import pylab as plt
import numpy as np
import numpy.ma as ma
from scipy import interpolate
from external.raster_mask import raster_mask2
from make_movie import make_movie
import project_settings as settings

DATA_DIR = settings.DATA_DIR
#SAT_DATA_DIR= '%sAQUA_h09v05_2005/'%DATA_DIR
#SAT_DATA_DIR= '%sTERRA_h09v05_2005/'%DATA_DIR

AQUA_DATA_DIR  = '%sAQUA_h09v05_2005/'%DATA_DIR
TERRA_DATA_DIR = '%sTERRA_h09v05_2005/'%DATA_DIR

def load_hdf_data(limit=365):
    aqua_file_names =  [('AQUA', f)  for f in sorted(os.listdir(AQUA_DATA_DIR)[:limit])]
    terra_file_names = [('TERRA', f) for f in sorted(os.listdir(TERRA_DATA_DIR)[:limit])]
    file_names = aqua_file_names + terra_file_names
    file_names = sorted(file_names, key=lambda f: f[1].split('.')[1])

    # Loading all the files can take a while. Read from a pickled cache if possible.
    cached_data_file = "%scache/load_hdf_data_%s-%s.pkl"%(DATA_DIR, file_names[0], file_names[-1])
    if os.path.exists(cached_data_file):
	print('Loading data from cache')
	data = pickle.load(open(cached_data_file, 'rb'))
	return data

    # Template that will be used to grab data.
    hdf_tpl = 'HDF4_EOS:EOS_GRID:"%s%s":MOD_Grid_Snow_500m:Fractional_Snow_Cover'
    all_frac_snow_data = []
    mask = None

    for file_name in file_names:
	try:
	    print('Loading %s file %s'%(file_name[0], file_name[1]))
	    if file_name[0] == 'AQUA':
		hdf_str = hdf_tpl%(AQUA_DATA_DIR, file_name[1])
	    elif file_name[0] == 'TERRA':
		hdf_str = hdf_tpl%(TERRA_DATA_DIR, file_name[1])

	    # Generate a mask based on the catchment area.
	    if mask == None:
		# Taken from course notes.
		mask = raster_mask2(hdf_str, target_vector_file="data_files/Hydrologic_Units/HUC_Polygons.shp", attribute_filter=2)

	    g = gdal.Open(hdf_str)

	    # Work out mins and maxes based on mask.
	    mask_bounds = np.where(mask == False)
	    ymin = int(min(mask_bounds[0]))
	    ymax = int(max(mask_bounds[0]) + 1)
	    xmin = int(min(mask_bounds[1]))
	    xmax = int(max(mask_bounds[1]) + 1)

	    # Only read the data I want based on mins/maxes.
	    frac_snow_data = g.ReadAsArray(yoff=ymin, ysize=ymax-ymin, xoff=xmin, xsize=xmax-xmin)
	    #frac_snow_data = g.ReadAsArray()

	    # Reduce the size of the mask so as it fits the data I pulled from HDF.
	    masked_frac_snow_data = ma.array(frac_snow_data, mask = mask[ymin:ymax, xmin:xmax])
	    all_frac_snow_data.append(masked_frac_snow_data)
	except:
	    print('COULD NOT LOAD FILE: %s'%(file_name))
    
    data = ma.array(all_frac_snow_data)
    print('Saving data to cache')
    pickle.dump(data, open(cached_data_file, 'wb'))
    return data

def interp_data_over_time(masked_data, orig_mask):
    # Make an array to stick all the interpolated results into.
    # Note it gets *just* the catchtment area mask, not the QC mask.
    interp_masked_data = ma.array(np.zeros_like(masked_data),  mask=orig_mask)

    x = np.arange(len(masked_data))

    # For each pixel in array work out its full interpolated time series.
    for i in range(masked_data.shape[1]):
	for j in range(masked_data.shape[2]):
	    pixel = (i, j)
	    y = masked_data.data[:, pixel[0], pixel[1]]
	    # Mask out values from x, y which are masked in masked_data.
	    y_masked = y[~masked_data.mask[:, pixel[0], pixel[1]]]
	    x_masked = x[~masked_data.mask[:, pixel[0], pixel[1]]]

	    if len(x_masked) > 2:
		try:
		    interp_f = interpolate.interp1d(x_masked, y_masked, bounds_error=False)
		    interp_masked_data[:, pixel[0], pixel[1]] = interp_f(x)
		    # plots a random interpolation based on a percentage chance.
		    #if random.random() > 0.9999:
			#plt.plot(x, interp_f(x))
			#plt.show()
		except Exception, e:
		    print("Could not interp pixel(%i, %i)"%(pixel[0], pixel[1]))
		    print(e)
		    pass

	if i % 10 == 0:
	    print("Done %00f percent"%(100.0 * i / masked_data.shape[1]))
    return interp_masked_data

def apply_quality_control(data):
    return ma.array(data, mask=data > 100)

def main(should_make_movie=False):
    # Returns data that has been masked with catchtment area.
    loaded_data = load_hdf_data(1000)
    all_data = []
    for i in range(0, 3):
	if i == 0:
	    data = loaded_data[::2, :, :] # AQUA
	    # Mask out data that is higher than 100: all QC data.
	    masked_data = apply_quality_control(data)
	    title = 'AQUA'
	elif i == 1:
	    data = loaded_data[1::2, :, :] # TERRA
	    # Mask out data that is higher than 100: all QC data.
	    masked_data = apply_quality_control(data)
	    title = 'TERRA'
	elif i == 2:
	    data = loaded_data.reshape(loaded_data.shape[0] / 2, 2, loaded_data.shape[1], loaded_data.shape[2]).mean(axis=1)
	    masked_data = apply_quality_control(loaded_data)
	    masked_data = masked_data.reshape(masked_data.shape[0] / 2, 2, masked_data.shape[1], masked_data.shape[2]).mean(axis=1)
	    title = 'Combined'

	interp_masked_data = interp_data_over_time(masked_data, data.mask)

	if should_make_movie:
	    make_movie("Snow Cover", "imgs/", "aqua_snow_cover", 100 - interp_masked_data[::2,:,:], 0.0, 100.0)
	
	total_snow_cover = interp_masked_data.sum(axis=2).sum(axis=1)
	#percent_snow_cover = 100. * total_snow_cover / np.max(total_snow_cover)
	percent_snow_cover = 100. * total_snow_cover / np.max(total_snow_cover[~np.isnan(total_snow_cover)])

	plt.plot(percent_snow_cover, label=title)

	all_data.append(interp_masked_data)

    #plt.legend(loc='best')
    #plt.show()

    return all_data


if __name__ == "__main__":
    main(False)
