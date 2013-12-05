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
    def __init__(self):
	self.results_dir = 'results'
	self.output_dir = '%s/%s'%(self.results_dir,
		dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

	self.save_pics = True
	self.show_pics = True

    def set_preparation_data(self, data):
	self.preparation_data = data

    def set_cal_data(self, data):
	self.cal_data = data

    def set_apply_data(self, data):
	self.apply_data = data

    def generate_results(self):
	if not os.path.exists(self.results_dir):
	    os.makedirs(self.results_dir)
	if not os.path.exists(self.output_dir):
	    os.makedirs(self.output_dir)

	self.generate_preparation_results()
	self.generate_cal_results()
	self.generate_app_results()

    def generate_preparation_results(self):
	data = self.preparation_data
	start_date = settings.RESULTS_START_DATE
	end_date = settings.RESULTS_END_DATE

	if end_date.year != start_date.year + 1:
	    raise Exception('settings.RESULTS_END_DATE must be 1 year after settings.RESULTS_START_DATE')

	dates = data['snow']['dates']

	#date_mask = ((dates >= start_date) & (dates <= end_date))

	year_1_mask = ((dates >= start_date) & (dates <= dt.datetime(start_date.year, 12, 31)))
	year_2_mask = ((dates >= dt.datetime(end_date.year, 1, 1)) & (dates <= end_date))

	for year_mask in (year_1_mask, year_2_mask):
	    year = dates[year_mask][0].year
	    log.info('stats for year: %04i'%year)

	    total_snow = data['snow']['COMBINED_total_snow'][year_mask]
	    percent_snow = data['snow']['COMBINED_percent_snow'][year_mask]
	    temp = data['temperature'][year_mask]
	    discharge = data['discharge'][year_mask]

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
	    plt.legend(loc='best')
	    if self.save_pics:
		plt.savefig('%s/%s'%(self.output_dir, 'all_prep_data.png'))
	    if self.show_pics:
		plt.show()

    def generate_cal_results(self):
	start_date = self.cal_data['start_date']
	dates = self.cal_data['dates']
	discharge_for_year = self.cal_data['discharge_for_year']
	model_data = self.cal_data['model_data']
	p_est = self.cal_data['p_est']

	plt_dates = matplotlib.dates.date2num(dates)
	plt.title('Calibration discharge for year %04i'%start_date.year)
	# Make sure plt_dates is same length as discharge_for_year.
	plt.plot_date(plt_dates[:len(discharge_for_year)], discharge_for_year, 'k', label='observed')
	plt.plot_date(plt_dates[:len(discharge_for_year)], cal.func(p_est, model_data), 'k--', label='modelled')
	plt.ylabel(r'Discharge ($m^3$)')
	plt.legend(loc='best')
	if self.save_pics:
	    plt.savefig('%s/%s'%(self.output_dir, 'cal_results.png'))
	if self.show_pics:
	    plt.show()

    def generate_app_results(self):
	start_date = self.apply_data['start_date']
	dates = self.apply_data['dates']
	discharge_for_year = self.apply_data['discharge_for_year']
	model_data = self.apply_data['model_data']
	a, b = self.apply_data['a'], self.apply_data['b']
	p_est = self.cal_data['p_est']

	# Make a linregress line.
	xs = np.array([min(discharge_for_year), max(discharge_for_year)])
	ys = a * xs + b

	plt_dates = matplotlib.dates.date2num(dates)
	plt.title('Modelled discharge for year %04i'%start_date.year)
	# Make sure plt_dates is same length as discharge_for_year.
	plt.plot_date(plt_dates[:len(discharge_for_year)], discharge_for_year, 'k', label='observed')
	plt.plot_date(plt_dates, cal.func(p_est, model_data), 'k--', label='modelled')
	plt.ylabel(r'Discharge ($m^3$)')
	plt.legend(loc='best')
	if self.save_pics:
	    plt.savefig('%s/%s'%(self.output_dir, 'apply_results1.png'))
	if self.show_pics:
	    plt.show()

	plt.title('Linear regression for year %04i'%start_date.year)
	plt.plot(discharge_for_year, cal.func(p_est, model_data), 'kx', label='data')
	plt.plot(xs, ys, 'k-', label='regression, slope: %2.2f, intercept: %2.2f'%(a, b))
	plt.xlabel(r'Observed discharge ($m^3$)')
	plt.ylabel(r'Modelled discharge ($m^3$)')
	plt.legend(loc='best')
	if self.save_pics:
	    plt.savefig('%s/%s'%(self.output_dir, 'apply_results2.png'))
	if self.show_pics:
	    plt.show()
