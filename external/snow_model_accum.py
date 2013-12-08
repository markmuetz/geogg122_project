import numpy as np
import scipy.stats as stats

# Taken from course notes. Commented to remind me how it works.
def model_accum_exp_decrease(data, tempThresh, k, p):
    '''Implements a simple Network Response Function (NRF) 

    Assumes NRF is a decreasing (if p < 1) exponential function.
    '''
    # Get indices of all days where temp is over threshold.
    meltDays = np.where(data['temp'] > tempThresh)[0]
    accum = data['snowprop']*0.
    for d in meltDays:
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * data['snowprop'][d]

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(data['snowprop'])) - d

	# m is an exp decrease.
        m = p ** n
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)]=0

	# This is like a convolution of each m * water into accum. 
        accum += m * water
    return accum

# Taken from course notes. Commented to remind me how it works.
def model_accum_exp_decrease_with_temp_delta(data, tempThresh, k, p):
    '''Implements a simple Network Response Function (NRF) 

    Assumes NRF is a decreasing (if p < 1) exponential function.
    '''
    # Get indices of all days where temp is over threshold.
    meltDays = np.where(data['temp'] > tempThresh)[0]
    temp_deltas = data['temp'][data['temp'] > tempThresh] - tempThresh
    accum = data['snowprop']*0.
    for d, temp_delta in zip(meltDays, temp_deltas):
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * data['snowprop'][d] * temp_delta

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(data['snowprop'])) - d

	# m is an exp decrease.
        m = p ** n
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)]=0

	# This is like a convolution of each m * water into accum. 
        accum += m * water
    return accum

# Taken from course notes. Commented to remind me how it works.
def model_accum_invgauss_decrease(data, p):
    '''Implements a simple Network Response Function (NRF) 

    Assumes NRF is a decreasing (if p < 1) exponential function.
    '''
    #base_flow_rate = p[7]
    tempThresh = p[0]
    k          = p[1]
    # Get indices of all days where temp is over threshold.
    meltDays = np.where(data['temp'] > tempThresh)[0]
    temp_deltas = data['temp'][data['temp'] > tempThresh] - tempThresh
    accum = data['snowprop']*0.
    for d, temp_delta in zip(meltDays, temp_deltas):
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * data['snowprop'][d]

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(data['snowprop'])) - d

	# m is an exp decrease.
        m = p[2] * stats.invgauss.pdf(n * p[3], p[4], p[5], p[6])
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)] = 0

	# This is like a convolution of each m * water into accum. 
        accum += m * water # + base_flow_rate # makes things worse!
    return accum

def model_accum_invgauss_decrease_with_temp_delta(data, p):
    '''Implements a simple Network Response Function (NRF) 

    Assumes NRF is a decreasing (if p < 1) exponential function.
    '''
    #base_flow_rate = p[7]
    tempThresh = p[0]
    k          = p[1]
    # Get indices of all days where temp is over threshold.
    meltDays = np.where(data['temp'] > tempThresh)[0]
    temp_deltas = data['temp'][data['temp'] > tempThresh] - tempThresh
    accum = data['snowprop']*0.
    for d, temp_delta in zip(meltDays, temp_deltas):
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * data['snowprop'][d] * temp_delta

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(data['snowprop'])) - d

	# m is an exp decrease.
        m = p[2] * stats.invgauss.pdf(n * p[3], p[4], p[5], p[6])
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)] = 0

	# This is like a convolution of each m * water into accum. 
        accum += m * water # + base_flow_rate # makes things worse!
    return accum

# Taken from course notes. Modified to add in delay.
def model_accum_exp_decrease_with_delay(data, tempThresh, k, p, delay):
    '''Implements a simple Network Response Function (NRF) 

    Assumes NRF is a decreasing (if p < 1) exponential function.
    '''
    # Get indices of all days where temp is over threshold.
    meltDays = np.where(data['temp'] > tempThresh)[0]
    accum = data['snowprop']*0.
    for d in meltDays:
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k * data['snowprop'][d]

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(data['snowprop'])) - d - int(delay * 100000)

	# m is an exp decrease.
        m = p ** n
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)]=0

	# This is like a convolution of each m * water into accum. 
        accum += m * water
    return accum
