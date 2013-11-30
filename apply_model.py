import logging

import matplotlib
import pylab as plt

from external import snow_model_accum as sma

log = logging.getLogger('apply_model')

def func(p, x):
    return sma.model_accum_exp_decrease(x, p[0], p[1], p[2])

def apply_model(data, p_est, start_date, end_date):
    discharge   = data['discharge']
    temperature = data['temperature']
    snow_data   = data['snow']

    dates = snow_data['dates']
    date_mask = ((dates >= start_date) & (dates <= end_date))
    discharge_for_year = discharge[date_mask]
    temperature_for_year = temperature[date_mask]
    snow_prop_for_year = snow_data['COMBINED_total_snow'][date_mask]

    model_data = {'temp': temperature_for_year, 'snowprop': snow_prop_for_year }

    plt_dates = matplotlib.dates.date2num(dates[date_mask])
    plt.plot(plt_dates, discharge_for_year, 'k', label='observed')
    plt.plot(plt_dates, func(p_est, model_data), 'k--', label='modelled')
    plt.legend(loc='best')

    plt.plot(discharge_for_year, 'k', label='observed')
    plt.plot(func(p_est, model_data), 'k--', label='modelled')
    plt.legend(loc='best')
    plt.show()
