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

def obj3(p, x, y):
    return ((func3(p, x) - y)**2).sum()

def obj4(p, x, y):
    return ((func4(p, x) - y)**2).sum()

def obj5(p, x, y):
    return ((func5(p, x) - y)**2).sum()

def obj6(p, x, y):
    return ((func6(p, x) - y)**2).sum()

def func(p, x):
    return sma.model_accum_exp_decrease(x, p[0], p[1], p[2])

def func2(p, x):
    return sma.model_accum_exp_decrease_with_delay(x, p[0], p[1], p[2], p[3])

def func3(p, x):
    return sma.model_accum_exp_decrease_with_temp_delta(x, p[0], p[1], p[2])

def func4(p, x):
    return sma.model_accum_invgauss_decrease(x, p)

def func5(p, x):
    return sma.model_accum_invgauss_decrease_with_temp_delta(x, p)

def func6(p, x):
    return sma.model_accum_exp_decrease_with_precip(x, p)

FUNCS = (('exp_dec', {'f': func, 'p_guess':[  5.55677672e+00,   1.26624410e-05,   9.72481286e-01], 'o': obj}),
	#('exp_dec_with_delay', {'f': func2, 'p_guess':[8.4, 0.000045, 0.95, 0.00000], 'o': obj2}),
	#('exp_dec_with_temp_delta', {'f': func3, 'p_guess':[8.4, 0.000045, 0.95], 'o': obj3}),
	#('inv_gauss', {'f': func4, 'p_guess':[8.4, 0.000045, 1.35537962e-02,   4.99842790e-04,   2.45289445e+00, -2.81229089e-03,   9.67786847e-03], 'o': obj4}),
	#('inv_gauss_with_temp_delta', {'f': func5, 'p_guess':[8.4, 0.000045, 1.35537962e-02,   4.99842790e-04,   2.45289445e+00, -2.81229089e-03,   9.67786847e-03], 'o': obj5}),
        #('exp_dec_with_precip', {'f': func6, 'p_guess':[8.4, 1, 0.000045, 0.00009, 0.95, 0.99], 'o': obj6}))
        ('exp_dec_with_precip', {'f': func6, 'p_guess':[5.55677672e+00, 1, 1.26624410e-05, 0.00009, 9.72481286e-01, 0.99], 'o': obj6}))

def calibrate_model(data, start_date, end_date):
    discharge   = data['discharge']
    temperature = data['temperature']
    snow_data   = data['snow']
    precip      = data['precip']

    cal_data = {}
    for k, v in FUNCS:
	log.info("Using func %s"%k)
	objective_f, p_guess = v['o'], v['p_guess']
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

	p_est = optimize.fmin_powell(objective_f, p_guess, 
		                     args=(model_data, discharge_for_year),
		                     maxfun=10000, maxiter=10000)
	log.info('powell')
	log.info('  estimated param values: %s'%str(p_est))
	log.info('  difference in squares: %2.1f'%objective_f(p_est,
	                                       model_data, discharge_for_year))

	if False:
	    if k == 'exp_dec':
		grid = ((0, 20, 1), 
			(0.000001, 0.00001, 0.000001), 
			(0.9, 0.99, 0.01))
	    elif k == 'exp_dec_with_precip':
		grid = ((0, 20, 1), 
			(0.000001, 0.00001, 0.000001), 
			(0.9, 0.99, 0.01),
			(0, 20, 1), 
			(0.000001, 0.00001, 0.000001), 
			(0.9, 0.99, 0.01))
	    p_est = optimize.brute(objective_f, grid, 
		                   args=(model_data, discharge_for_year))

	    log.info('brute')
	    log.info('  estimated param values: %s'%str(p_est))
	    log.info('  difference in squares: %2.1f'%objective_f(p_est, 
		                               model_data, discharge_for_year))

	#p_est = optimize.fmin_bfgs(objective_f, p_guess, fprime=None, 
	                            #args=(model_data, discharge_for_year),
		                    #epsilon=1.5e-8, maxiter=10000)
	#p_est = optimize.fmin(objective_f, p_guess, 
	                 #args=(model_data, discharge_for_year), maxiter=10000)

	#log.info('fmin')
	#log.info('  estimated param values: %s'%str(p_est))
	#log.info('  difference in squares: %2.1f'%objective_f(p_est,
					      #model_data, discharge_for_year))

	func_cal_data = {'discharge_for_year': discharge_for_year, 
		    'dates': dates[date_mask], 
		    'model_data': model_data, 
		    'start_date': start_date,
		    'p_est': p_est}
	cal_data[k] = func_cal_data

    return cal_data
