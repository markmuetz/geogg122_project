import numpy as np
import scipy.interpolate
import pylab as plt
import datetime
import project_settings as settings

def prepare_temperature_data(year):
    temp_data = np.loadtxt('%sdelnorteT.dat'%settings.DATA_DIR, unpack=True, dtype=str)[:, 1:]
    temp_data_for_year = temp_data[3:5, np.where(temp_data[0] == str(year))[0]].astype(float)

    # temp_data_for_year is a min and max: take its average.
    av_temp_data_for_year = temp_data_for_year.mean(axis=0)

    # There are some values that will need interpolation.
    temp_data_for_year_mask = av_temp_data_for_year < 1000
    x = np.arange(len(av_temp_data_for_year))
    f = scipy.interpolate.interp1d(x[temp_data_for_year_mask], av_temp_data_for_year[temp_data_for_year_mask])

    interp_av_data_for_year = (f(x) - 32) * 5 / 9 # convert to C

    plt.title('Temperature data for %i'%year)
    plt.plot(interp_av_data_for_year)
    #plt.show()


def prepare_discharge_data(year):
    # Create a closure so as there's a function for just the year I want.
    def is_year(date_string):
	return datetime.datetime.strptime(date_string, '%Y-%m-%d').year == year

    # np.where(...) won't work unless you vectorise it first.
    vec_is_year = np.vectorize(is_year)

    discharge_data = np.loadtxt('%sdelnorte.dat'%settings.DATA_DIR, usecols=(2, 3), unpack=True, dtype=str)
    # Needs conversion.
    discharge_data_for_year = discharge_data[1, :][np.where(vec_is_year(discharge_data[0]))[0]].astype(float)

    plt.title('Discharge data for %i'%year)
    plt.plot(100.0 * discharge_data_for_year / np.max(discharge_data_for_year))
    #plt.show()


if __name__ == "__main__":
#    for year in range(2000, 2013):
#	try:
#	    prepare_temperature_data(year)
#	    prepare_discharge_data(year)
#	except:
#	    pass
    year = 2005
    prepare_temperature_data(year)
    prepare_discharge_data(year)
