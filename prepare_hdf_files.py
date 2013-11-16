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


DATA_DIR= '/media/E6F08871F08849AF/geogg122_data/h09v05_2009_2010/'

def load_hdf_data(limit=365):
    file_names = sorted(os.listdir(DATA_DIR)[:limit])

    # Loading all the files can take a while. Read from a pickled cache if possible.
    cached_data_file = "cache/load_hdf_data_%s-%s.pkl"%(file_names[0], file_names[-1])
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
	    print('Loading file %s'%(file_name))
	    hdf_str = hdf_tpl%(DATA_DIR, file_name)
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

def main(show_graph=False):
    # Returns data that has been masked with catchtment area.
    data = load_hdf_data(1000)

    masked_data = apply_quality_control(data)
    # Mask out data that is higher than 100: all QC data.
    # Prints out all masked data.
    #for d in masked_data:
	#plt.imshow(d)
	#plt.show()

    interp_masked_data = interp_data_over_time(masked_data, data.mask)

    if show_graph:
	for i, d in enumerate(interp_masked_data):
	    plt.imshow(d)
	    plt.title(i)
	    plt.colorbar()
	    plt.show()
    
    total_snow_cover = interp_masked_data.sum(axis=2).sum(axis=1)
    percent_snow_cover = 100. * total_snow_cover / np.max(total_snow_cover)

    plt.plot(percent_snow_cover)
    plt.show()

    plt.plot(100 - percent_snow_cover)
    plt.show()


if __name__ == "__main__":
    main(False)
