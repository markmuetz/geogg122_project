import os

import numpy as np
import pylab as plt
import matplotlib
import datetime as dt
import logging

import calibrate as cal
import apply_model as app
import project_settings as settings

log = logging.getLogger('results')

def fmt_date(date):
    return date.strftime('%Y/%m/%d')

class Results:
    def __init__(self, output_dir):
	'''ctor just saevs the output_dir and provides v. basic config.'''
	self.output_dir = output_dir

	self.save_pics = True
	self.show_pics = True

    def set_preparation_data(self, data):
	'''Stores the preparation data for future use.'''
	self.preparation_data = data

    def set_cal_data(self, data):
	'''Stores the calibration data for future use.'''
	self.cal_data = data

    def set_apply_data(self, data):
	'''Stores the model run data for future use.'''
	self.apply_data = data

    def generate_results(self):
	'''Use all stored data to generate results.'''
	self.generate_preparation_results()
	self.generate_cal_results()
	self.generate_app_results()

    def generate_preparation_results(self):
	'''Generate preperation results.

Logs all needed values, and produces a graph for cal and app periods.
'''
	data = self.preparation_data
	start_date = settings.RESULTS_START_DATE
	end_date = settings.RESULTS_END_DATE

	if end_date.year != start_date.year + 1:
	    raise Exception('settings.RESULTS_END_DATE must be 1 year after settings.RESULTS_START_DATE')

	dates = data['snow']['dates']

	year_1_mask = ((dates >= start_date) & (dates <= dt.datetime(start_date.year, 12, 31)))
	year_2_mask = ((dates >= dt.datetime(end_date.year, 1, 1)) & (dates <= end_date))

	for year_mask in (year_1_mask, year_2_mask):
	    year = dates[year_mask][0].year
	    log.info('stats for year: %04i'%year)

	    total_snow = data['snow']['COMBINED_total_snow'][year_mask]
	    percent_snow = data['snow']['COMBINED_percent_snow'][year_mask]
	    temp = data['temperature'][year_mask]
	    discharge = data['discharge'][year_mask]
	    precip = data['precip'][year_mask]

	    log.info('   snow max, min, mean: %f, %f, %f'%(total_snow.max(),
							   total_snow.min(),
							   total_snow.mean()))
	    log.info('   disc max, min, mean: %f, %f, %f'%(discharge.max(),
							   discharge.min(),
							   discharge.mean()))
	    log.info('   temp max, min, mean: %f, %f, %f'%(temp.max(),
							   temp.min(),
							   temp.mean()))

	    plt_dates = matplotlib.dates.date2num(dates[year_mask])
	    plt.title('All data for year %04i'%(year))
	    plt.plot_date(plt_dates, temp, 'r-', label='Temperature')
	    plt.plot_date(plt_dates, 100. * discharge / np.max(discharge),  'b-',label='Discharge')
	    plt.plot_date(plt_dates, percent_snow,  'c-',label='% Snow Cover')
	    plt.plot_date(plt_dates, precip,  'r--',label='Precip')
	    plt.legend(loc='best')
	    if self.save_pics:
		plt.savefig('%s/%s'%(self.output_dir, 'all_prep_data.png'))
	    if self.show_pics:
		plt.show()

    def generate_cal_results(self):
	'''Generate calibration results.

Produces a graph showing obs and mod together, and a graph of obs vs mod
with a linear regression fitted.
'''
	for k, v in cal.FUNCS:
	    start_date = self.cal_data[k]['start_date']
	    dates = self.cal_data[k]['dates']
	    discharge_for_year = self.cal_data[k]['discharge_for_year']
	    model_data = self.cal_data[k]['model_data']
	    apply_data = self.cal_data[k]
	    p_est = self.cal_data[k]['p_est']
	    func = v['f']

	    plt_dates = matplotlib.dates.date2num(dates)
	    plt.title('Calibration discharge for year %04i, func %s'%(start_date.year, k))
	    # Make sure plt_dates is same length as discharge_for_year.
	    plt.plot_date(plt_dates[:len(discharge_for_year)], discharge_for_year, 'k', label='observed')
	    plt.plot_date(plt_dates[:len(discharge_for_year)], func(p_est, model_data), 'k--', label='modelled')
	    plt.ylabel(r'Discharge ($m^3/s$)')
	    plt.legend(loc='best')
	    if self.save_pics:
		plt.savefig('%s/%s_%s'%(self.output_dir, k, 'cal_results.png'))
	    if self.show_pics:
		plt.show()

    def generate_app_results(self):
	'''Generate model application results.

Produces a graph showing obs and mod together, and a graph of obs vs mod
with a linear regression fitted.
'''
	for k, v in cal.FUNCS:
	    start_date = self.apply_data[k]['start_date']
	    dates = self.apply_data[k]['dates']
	    discharge_for_year = self.apply_data[k]['discharge_for_year']
	    model_data = self.apply_data[k]['model_data']
	    apply_data = self.apply_data[k]
	    a, b = apply_data['a'], apply_data['b']
	    r_val = apply_data['r_val']
	    p_est = self.cal_data[k]['p_est']
	    func = v['f']

	    # Make a linregress line.
	    xs = np.array([min(discharge_for_year), max(discharge_for_year)])
	    ys = a * xs + b

	    fig = plt.figure(figsize=(12, 6))
	    ax1 = fig.add_subplot(1, 2, 1)
	    plt_dates = matplotlib.dates.date2num(dates)
	    #ax1.title('Modelled discharge for year %04i, func %s'%(start_date.year, k))
	    # Make sure plt_dates is same length as discharge_for_year.
	    ax1.plot_date(plt_dates[:len(discharge_for_year)], discharge_for_year, 'k', label='observed')
	    ax1.plot_date(plt_dates, func(p_est, model_data), 'k--', label='modelled')
	    ax1.set_ylabel(r'Discharge ($m^3/s$)')
	    ax1.legend(loc='best')

	    ax2 = fig.add_subplot(1, 2, 2)
	    #ax2.title('Linear regression for year %04i'%start_date.year)
	    ax2.plot(discharge_for_year, func(p_est, model_data), 'kx', label='data')
	    ax2.plot(xs, ys, 'k-', label='r: %2.2f, grad: %2.2f, int: %2.2f'%(r_val, a, b))
	    ax2.set_xlabel(r'Observed discharge ($m^3/s$)')
	    ax2.set_ylabel(r'Modelled discharge ($m^3/s$)')
	    ax2.legend(loc='best')

	    if self.save_pics:
		plt.savefig('%s/%s_%s'%(self.output_dir, k, 'apply_results2.png'))
	    if self.show_pics:
		plt.show()
