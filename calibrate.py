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

def obj2(p, x, y):
    return ((func2(p, x) - y)**2).sum()

def func(p, x):
    return sma.model_accum_exp_decrease(x, p[0], p[1], p[2])

def func2(p, x):
    return sma.model_accum_exp_decrease_with_delay(x, p[0], p[1], p[2], p[3])

def calibrate_model(data, start_date, end_date):
    discharge   = data['discharge']
    temperature = data['temperature']
    snow_data   = data['snow']

    for objective_f, p_guess in ((obj, [8.4, 0.000045, 0.95]), (obj2, [8.4, 0.000045, 0.95, 0.00000])):
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

	p_est = optimize.fmin_bfgs(objective_f, p_guess, args=(model_data, discharge_for_year), maxiter=10000)

	log.info('  estimated param values: %s'%str(p_est))
	log.info('  difference in squares: %2.1f'%objective_f(p_est, model_data, discharge_for_year))

    cal_data = {'discharge_for_year': discharge_for_year, 
	        'dates': dates[date_mask], 
	        'model_data': model_data, 
		'start_date': start_date,
	        'p_est': p_est}

    return cal_data
