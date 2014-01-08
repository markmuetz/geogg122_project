import logging

import matplotlib
import pylab as plt
import numpy as np
from scipy.stats import linregress

import calibrate as cal

log = logging.getLogger('apply_model')

def apply_model(data, cal_data, start_date, end_date):
    """Applies all models found in cal.FUNCS to the given data
    
data: must contain all the discharge, temperature, snow and precip 
      data as produced by prepare.py.
cal_data: all data that calibration produces.
start_date/end_date: date range over which to apply model.

returns the result of applying the model.
"""
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

    model_data = {'temp': temperature_for_year, 
	          'snowprop': snow_prop_for_year,
	          'precip': precip_for_year }

    app_data = {}
    for k, v in cal.FUNCS:
	func = v['f']
	p_est = cal_data[k]['p_est']
	# N.B. a is slope, b is intercept.
	a, b, r_val, p_val, stderr = linregress(discharge_for_year, 
						func(p_est, model_data))

	log.info("Func %s"%k)
	log.info("  slope, intercept: %f, %f"%(a, b))
	log.info("  r-value, p-value: %f, %f"%(r_val, p_val))
	log.info("  Std. err.: %f"%(stderr))
	app_data[k] = {'a': a, 'b': b, 'r_val': r_val, 
	    'dates': dates[date_mask],
	    'discharge_for_year': discharge_for_year,
	    'model_data': model_data,
	    'start_date': start_date }

    return app_data
