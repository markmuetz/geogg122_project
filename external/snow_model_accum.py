import numpy as np
import scipy.stats as stats

def model_accum_exp_decrease(data, tempThresh, k, p):
    '''Implements a simple Network Response Function (NRF) 

Assumes NRF is a decreasing (if p < 1) exponential function.
Taken from P. Lewis' course notes: 6a. Assessed Practical 
http://www2.geog.ucl.ac.uk/~plewis/geogg122_local/geogg122//Chapter6a_Practical/Practical.html
renamed from model_accum to model_accum_exp_decrease to make model used explicit.

Commented to remind me how it works. otherwise unchanged.
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

def model_accum_exp_decrease_with_precip(data, p):
    '''Implements a simple Network Response Function (NRF) 

Assumes NRF is a decreasing (if p < 1) exponential function.

Includes precipitation data in data.

Based on model_accum_exp_decrease by P. Lewis above.
    '''
    tempThresh1 = p[0]
    tempThresh2 = p[1]
    k1 = p[2]
    k2 = p[3]
    p1 = p[4]
    p2 = p[5]
    # Get indices of all days where temp is over threshold.
    meltDays1 = np.where(data['temp'] > tempThresh1)[0]
    meltDays2 = np.where(data['temp'] > tempThresh2)[0]
    accum = data['snowprop']*0.

    for d in meltDays1:
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k1 * data['snowprop'][d]

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(data['snowprop'])) - d

	# m is an exp decrease.
        m = p1 ** n
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)]=0

	# This is like a convolution of each m * water into accum. 
        accum += m * water

    for d in meltDays2:
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
        water = k2 * data['precip'][d]

	# Make a number that runs from e.g. -10 to len(...)
        n = np.arange(len(data['precip'])) - d

	# m is an exp decrease.
        m = p2 ** n
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)]=0

	# This is like a convolution of each m * water into accum. 
        accum += m * water
    return accum

def model_accum_exp_decrease_with_temp_delta(data, tempThresh, k, p):
    '''Implements a simple Network Response Function (NRF) 

Assumes NRF is a decreasing (if p < 1) exponential function.
Assumes that the amount of water will be proportional to the temperature 
difference between the threshold temp and the actual temp.

Based on model_accum_exp_decrease by P. Lewis above.
    '''
    # Get indices of all days where temp is over threshold.
    meltDays = np.where(data['temp'] > tempThresh)[0]
    temp_deltas = data['temp'][data['temp'] > tempThresh] - tempThresh
    accum = data['snowprop']*0.
    for d, temp_delta in zip(meltDays, temp_deltas):
	# Work out water equiv of how much snow has melted.
	# Way of doing this is to multiply total cover by a magic constant.
	# Notice that I'm also multiplying by temp_delta.
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

def model_accum_invgauss_decrease(data, p):
    '''Implements a invgaus Network Response Function (NRF) 

Uses an invguass response function instead if an exp decrease.
Based on model_accum_exp_decrease by P. Lewis above.
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

	# m is an incgauss function.
        m = p[2] * stats.invgauss.pdf(n * p[3], p[4], p[5], p[6])
	# set all m where n is -ve to 0. This makes a function where the value
	# is 0 up until d, where the exp decrease kicks in (see graph in course notes).
        m[np.where(n<0)] = 0

	# This is like a convolution of each m * water into accum. 
        accum += m * water # + base_flow_rate # makes things worse!
    return accum

def model_accum_invgauss_decrease_with_temp_delta(data, p):
    '''Implements a invgauss Network Response Function (NRF) 

Like a combined version of methods above:
Uses invgauss as NRF and adds in a delay to the NRF.

Based on model_accum_exp_decrease by P. Lewis above.
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

def model_accum_exp_decrease_with_delay(data, tempThresh, k, p, delay):
    '''Implements a simple Network Response Function (NRF) 

Assumes NRF is a decreasing (if p < 1) exponential function.

Adds in a delay to the NRF.

Based on model_accum_exp_decrease by P. Lewis above.
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
