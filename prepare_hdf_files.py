#!/usr/bin/python
import os
import gdal
import pylab as plt
import numpy as np
import numpy.ma as ma
from scipy import interpolate
from external.raster_mask import raster_mask2


DATA_DIR= '/media/E6F08871F08849AF/geogg122_data/h09v05_2009_2010/'

def load_hdf_data(limit=365):
    hdf_tpl = 'HDF4_EOS:EOS_GRID:"%s%s":MOD_Grid_Snow_500m:Fractional_Snow_Cover'
    all_frac_snow_data = []
    mask = None

    for file_name in sorted(os.listdir(DATA_DIR)[:limit]):
	try:
	    print('Loading file %s'%(file_name))
	    hdf_str = hdf_tpl%(DATA_DIR, file_name)
	    if mask == None:
		mask = raster_mask2(hdf_str, target_vector_file="data_files/Hydrologic_Units/HUC_Polygons.shp", attribute_filter=2)
	    g = gdal.Open(hdf_str)

	    mask_bounds = np.where(mask == False)
	    ymin = int(min(mask_bounds[0]))
	    ymax = int(max(mask_bounds[0]) + 1)
	    xmin = int(min(mask_bounds[1]))
	    xmax = int(max(mask_bounds[1]) + 1)
	    #print xmin, xmax, ymin, ymax

	    frac_snow_data = g.ReadAsArray(yoff=ymin, ysize=ymax-ymin, xoff=xmin, xsize=xmax-xmin)
	    #frac_snow_data = g.ReadAsArray()

	    masked_frac_snow_data = ma.array(frac_snow_data, mask = mask[ymin:ymax, xmin:xmax])
	    all_frac_snow_data.append(masked_frac_snow_data)
	except:
	    print('COULD NOT LOAD FILE: %s'%(file_name))
    #return ma.array(all_frac_snow_data, mask=all_frac_snow_data > 100)
    return ma.array(all_frac_snow_data)


if __name__ == "__main__":
    data = load_hdf_data(10)
    masked_data = ma.array(data, mask=data > 100)
    #for d in masked_data:
	#plt.imshow(d)
	#plt.show()

    x = np.arange(len(data))

    interp_masked_data = data.copy()

    for i in range(masked_data.shape[1]):
	for j in range(masked_data.shape[2]):
	    pixel = (i, j)
	    y = masked_data.data[:, pixel[0], pixel[1]]
	    y_masked = y[~masked_data.mask[:, pixel[0], pixel[1]]]
	    x_masked = x[~masked_data.mask[:, pixel[0], pixel[1]]]

	    try:
		interp_f = interpolate.interp1d(x_masked, y_masked)
		interp_masked_data[:, pixel[0], pixel[1]] = interp_f(x)
		#plt.plot(x, interp_f(x))
		#plt.show()
	    except:
		#print("Could not interp pixel(%i, %i)"%(pixel[0], pixel[1]))
		pass
	print(i)

    for i, d in enumerate(interp_masked_data):
	plt.imshow(d)
	plt.title(i)
	plt.colorbar()
	plt.show()


