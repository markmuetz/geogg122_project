import numpy as np

# Taken from course notes. Commented to remind me how it works.
def model_accum_exp_decrease(data, tempThresh, k, p):
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
