#!/usr/bin/python
import logging
import datetime as dt

import matplotlib
import pylab as plt
from scipy import optimize
from scipy.stats import linregress

from external import snow_model_accum as sma

log = logging.getLogger('calibrate')

def obj_exp_dec(p, x, y):
    return ((func_exp_dec(p, x) - y)**2).sum()

def obj_exp_dec_with_precip(p, x, y):
    penalty = 0
    if p[3] < 0:
	penalty = 10000
    return ((func_exp_dec_with_precip(p, x) - y)**2).sum() + penalty

def func_exp_dec(p, x):
    return sma.model_accum_exp_decrease(x, p[0], p[1], p[2])

def func_exp_dec_with_precip(p, x):
    return sma.model_accum_exp_decrease_with_precip(x, p)

FUNCS = (('exponential decay model', 
          {'f': func_exp_dec, 
	   'p_guess':[  5.55677672e+00,   1.26624410e-05,   9.72481286e-01], 
	   'o': obj_exp_dec}),
	 #('inv_gauss', {'f': func4, 'p_guess':[8.4, 0.000045, 1.35537962e-02,   4.99842790e-04,   2.45289445e+00, -2.81229089e-03,   9.67786847e-03], 'o': obj4}),
         ('exponential decay with precip. model', 
          {'f': func_exp_dec_with_precip, 
	   'p_guess':[5.55677672e+00, 1, 1.26624410e-05, 0.00009, 9.72481286e-01, 0.99], 
	   'o': obj_exp_dec_with_precip}))

def calibrate_model(data, start_date, end_date):
    '''Performs a full calibration using the powell method for optimization

Works on as many functions as are provided in FUNCS.
uses data as the input and observed data to calibrate with.
works between start_date and end_date, which define the cal period.

returns a dict with all the calibration info for the functions calibrated.
'''
    discharge   = data['discharge']
    temperature = data['temperature']
    snow_data   = data['snow']
    precip      = data['precip']

    dates = snow_data['dates']
    date_mask = ((dates >= start_date) & (dates <= end_date))

    # If looking at 2009-2010 data, discharge data only runs up to
    # end of 2010, hence it's shorter than dates.
    discharge_for_year = discharge[date_mask[:len(discharge)]]
    temperature_for_year = temperature[date_mask]
    snow_prop_for_year = snow_data['COMBINED_total_snow'][date_mask]
    precip_for_year = precip[date_mask[:len(precip)]]

    # Must make sure that these arrays are all of same length if 
    # discharge data is incomplete (for 2010).
    model_data = {'temp': temperature_for_year[:len(discharge_for_year)], 
		  'snowprop': snow_prop_for_year[:len(discharge_for_year)],
		  'precip': precip_for_year[:len(discharge_for_year)] }

    cal_data = {}
    for k, v in FUNCS:
	log.info("Using func %s"%k)
	objective_f, p_guess = v['o'], v['p_guess']
	func = v['f']
	log.info('  guessed param values: %s'%str(p_guess))

	if False:
	    # Was used initially to find suitable initial guess values for params.
	    if k == 'exponential decay model':
		grid = ((0, 20, 1), 
			(0.0, 0.00001, 0.000001), 
			(0.9, 0.99, 0.01))
	    elif k == 'exponential decay with precip. model':
		grid = ((0, 10, 1), 
			(0.0, 0.00001, 0.000005), 
			(0.9, 0.99, 0.02),
			(0, 10, 1), 
			(0.0, 0.00001, 0.000005), 
			(0.9, 0.99, 0.02))
	    p_est = optimize.brute(objective_f, grid, 
		                   args=(model_data, discharge_for_year))

	    log.info('brute')
	    log.info('  estimated param values: %s'%str(p_est))
	    log.info('  difference in squares: %2.1f'%objective_f(p_est, 
		                               model_data, discharge_for_year))

	p_est = optimize.fmin_powell(objective_f, p_guess, 
		                     args=(model_data, discharge_for_year),
		                     maxfun=10000, maxiter=10000)
	log.info('powell')
	log.info('  estimated param values: %s'%str(p_est))
	log.info('  difference in squares: %2.1f'%objective_f(p_est,
	                                       model_data, discharge_for_year))

	a, b, r_val, p_val, stderr = linregress(discharge_for_year, 
						func(p_est, model_data))

	log.info("Func %s"%k)
	log.info("  slope, intercept: %f, %f"%(a, b))
	log.info("  r-value, p-value: %f, %f"%(r_val, p_val))
	log.info("  Std. err.: %f"%(stderr))

	func_cal_data = {'a': a, 'b': b, 'r_val': r_val, 
		    'discharge_for_year': discharge_for_year, 
		    'dates': dates[date_mask], 
		    'model_data': model_data, 
		    'start_date': start_date,
		    'p_est': p_est}
	cal_data[k] = func_cal_data

    return cal_data
