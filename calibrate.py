#!/usr/bin/python
import logging
import datetime as dt

import matplotlib
import pylab as plt
from scipy import optimize

from external import snow_model_accum as sma

log = logging.getLogger('calibrate')

def obj(p, x, y):
    return ((func(p, x) - y)**2).sum()

def func(p, x):
    return sma.model_accum_exp_decrease(x, p[0], p[1], p[2])

def calibrate_model(data, start_date, end_date):
    log.info('Calibrating model')
    discharge   = data['discharge']
    temperature = data['temperature']
    snow_data   = data['snow']

    dates = snow_data['dates']
    date_mask = ((dates >= start_date) & (dates <= end_date))
    # If looking at 2009-2010 data, discharge data only runs up to
    # end of 2010, hence it's shorter than dates.
    discharge_for_year = discharge[date_mask[:len(discharge)]]
    temperature_for_year = temperature[date_mask]
    snow_prop_for_year = snow_data['COMBINED_total_snow'][date_mask]

    # Must make sure that these arrays are all of same length if 
    # discharge data is incomplete (for 2010).
    model_data = {'temp': temperature_for_year[:len(discharge_for_year)], 
	          'snowprop': snow_prop_for_year[:len(discharge_for_year)] }

    p_guess = [8.4, 0.000045, 0.95]
    p_est = optimize.fmin(obj, p_guess, args=(model_data, discharge_for_year), maxiter=10000)
    print p_est

    plt_dates = matplotlib.dates.date2num(dates[date_mask])
    # To do with above issue, make sure plt_dates is same length as discharge_for_year.
    plt.plot_date(plt_dates[:len(discharge_for_year)], discharge_for_year, 'k', label='observed')
    plt.plot_date(plt_dates[:len(discharge_for_year)], func(p_est, model_data), 'k--', label='modelled')
    plt.legend(loc='best')
    plt.show()
    return p_est
