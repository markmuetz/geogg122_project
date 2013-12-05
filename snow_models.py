import numpy as np
import scipy.stats as stats
import pylab as plt

# Similar to model from course notes. Commented to remind me how it works.
def normal_delay_model(data, tempThresh, k, p, d):
    # Get indices of all days where temp is over threshold.
    meltDays = np.where(data['temp'] > tempThresh)[0]
    accum = data['snowprop']*0.
    for day in meltDays:
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * data['snowprop'][day]

	m = water * stats.norm.pdf((np.arange(-3, 100, 0.1) + 3) / day - 3)/ day
	plt.plot(m)
	plt.show()

	accum += m[:len(accum)]
    return accum

def snow_melt_delta(snow_data, k, p):
    '''Attempt at a model that compares snow cover from one day to the next,
    and uses the delta to try to predict discharge. Turns data into 1D time series
    data before running anlaysis. No fit to observed data.

    snow_data: 3D np.array that contains data.
    k: param that determins overll volume
    p: exponential coeff.
    '''
    total_snow_cover = snow_data.sum(axis=2).sum(axis=1)
    percent_snow_cover = 100. * total_snow_cover / \
                         np.max(total_snow_cover[~np.isnan(total_snow_cover)])
    percent_snow_cover2 = np.zeros_like(percent_snow_cover)
    percent_snow_cover2[1:] = percent_snow_cover[:-1]
    deltas = percent_snow_cover - percent_snow_cover2
    deltas[np.isnan(deltas.data)] = 0
    deltas[deltas > 0 ] = 0

    deltas = -deltas

    accum = np.zeros_like(deltas)

    for i, d in enumerate(deltas.data):
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * d

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(deltas)) - i

	# m is an exp decrease.
        m = p ** n
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)]=0

	# This is like a convolution of each m * water into accum. 
        accum += m * water
    return accum

def snow_melt_delta2(snow_data, k, p):
    '''Attempt at a model that compares snow cover from one day to the next,
    and uses the delta to try to predict discharge. Turns data into 1D time series
    data after running anlaysis. No fit to observed data.

    snow_data: 3D np.array that contains data.
    k: param that determins overll volume
    p: exponential coeff.
    '''
    snow_data2 = np.zeros_like(snow_data)
    snow_data2[1:] = snow_data[:-1]
    deltas = snow_data - snow_data2
    deltas[np.isnan(deltas.data)] = 0
    deltas[deltas > 0 ] = 0
    deltas = -deltas

    accum = np.zeros_like(deltas)

    for i, d in enumerate(deltas.data):
	print(i)
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * d.sum()

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(deltas)) - i

	# m is an exp decrease.
        m = p ** n
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)]=0

	# This is pretty cool: repeat 1D array m and then reshape it to same shape
	# as accum.
        accum += m.repeat(accum.shape[1] * accum.shape[2]).\
	 	 reshape(-1, accum.shape[1], accum.shape[2]) * water
    return accum
