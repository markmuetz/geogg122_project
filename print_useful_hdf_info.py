#!/usr/bin/python
import gdal
import pylab as plt

def print_useful_info():
    g = gdal.Open('HDF4_EOS:EOS_GRID:"data_files/MOD10A1.A2007001.h14v04.005.2008133182715.hdf":MOD_Grid_Snow_500m:Fractional_Snow_Cover')
    for k, v in g.GetMetadata().items():
	print k, v

    frac_snow_data = g.ReadAsArray()
    plt.imshow(frac_snow_data)
    plt.show()


if __name__ == "__main__":
    print_useful_info()
