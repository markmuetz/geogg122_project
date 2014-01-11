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
    def __init__(self, output_dir, save_pics=True, show_pics=True):
	'''ctor just saevs the output_dir and provides v. basic config.'''
	self.output_dir = output_dir

	self.save_pics = save_pics
	self.show_pics = show_pics

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
	log.info('Generating all results')
	self.generate_model_curves()
	self.generate_snow_data_results()

	#self.generate_preparation_results()
	#self.generate_cal_results()
	#self.generate_app_results()

    def generate_exp_decrease_model_curves(self):
	'''Generates example curves for exp decrease model's NRF.'''
        n = np.arange(60)

	vals = ((1., 0.9), (1., 0.8), (2., 0.9))
	for k, p in vals:
	    # m is an exp decrease.
	    m = k * (p ** n)
	    plt.plot(m, label='k = %1.1f, p = %1.1f'%(k, p))
	
	plt.xlabel('days after response start')
	plt.ylabel('Network Reponse Function')
	plt.legend(loc='best')

	plt.show()

    def generate_snow_data_results(self):
	'''Generate snow data results.

Produces on image with 4 separate figs, each fig is a 
represenation of the catchment one for each season.
'''
	data = self.preparation_data
	snow_data = data['snow']['COMBINED']
	dates = data['snow']['dates']

	im_dates = [dt.datetime(2008, 01, 01),
		    dt.datetime(2008, 04, 11),
		    dt.datetime(2008, 07, 01),
		    dt.datetime(2008, 11, 15)]

	fig = plt.figure()
	subplots = []
	for i, date in enumerate(im_dates):
	    sp = fig.add_subplot(2, 2, i + 1)
	    im = sp.imshow(100 - snow_data[np.where(dates == date)[0][0]])
	    sp.set_title(fmt_date(date))

	cax = fig.add_axes([0.92, 0.1, 0.03, 0.8])
	fig.colorbar(im, cax=cax)

	plt.show()

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

	    plt_data = (('Temperature', temp, 'r-', [-30, 20]),
		        ('Precip.', precip, 'b--', [0, 0.03]),
			('% snow cover', percent_snow, 'c-', [0, 100]),
			('Dischage', discharge, 'b-', [0, 200]))

	    plt_dates = matplotlib.dates.date2num(dates[year_mask])
	    date_fmt = matplotlib.dates.DateFormatter("%b")

	    fig = plt.figure()
	    ax1 = None
	    for i, plt_datum in enumerate(plt_data):
		log.info('   %s max, min, mean: %f, %f, %f'%(plt_datum[0],
		                                           total_snow.max(),
							   total_snow.min(),
							   total_snow.mean()))
		if i == 0:
		    ax = fig.add_subplot(4, 1, i + 1)
		    ax.set_title(year)
		    plt.setp(ax.get_xticklabels(), visible=False)

		    ax1 = ax
		elif i == 3:
		    ax = fig.add_subplot(4, 1, i + 1, sharex=ax1)
		    ax.xaxis.set_major_formatter(date_fmt)
		else:
		    ax = fig.add_subplot(4, 1, i + 1, sharex=ax1)
		    plt.setp(ax.get_xticklabels(), visible=False)

		ax.plot_date(plt_dates, plt_datum[1], plt_datum[2])
		ax.set_ylim(plt_datum[3])

	    #plt.title('All data for year %04i'%(year))
	    #plt.plot_date(plt_dates, temp, 'r-', label='Temperature')
	    #plt.plot_date(plt_dates, 100. * discharge / np.max(discharge),  'b-',label='Discharge')
	    #plt.plot_date(plt_dates, percent_snow,  'c-',label='% Snow Cover')
	    #plt.plot_date(plt_dates, precip,  'r--',label='Precip')
	    #plt.legend(loc='best')
	    if self.save_pics:
		plt.savefig('%s/%s'%(self.output_dir, 'all_prep_data.png'))
	    if self.show_pics:
		plt.show()

    def generate_cal_results(self):
	'''Generate calibration results.

Produces a graph showing obs and mod together, and a graph of obs vs mod
with a linear regression fitted.
'''
	if False:
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

	for k, v in cal.FUNCS:
	    start_date = self.cal_data[k]['start_date']
	    dates = self.cal_data[k]['dates']
	    discharge_for_year = self.cal_data[k]['discharge_for_year']
	    model_data = self.cal_data[k]['model_data']
	    cal_data = self.cal_data[k]
	    a, b = cal_data['a'], cal_data['b']
	    r_val = cal_data['r_val']
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
	    date_fmt = matplotlib.dates.DateFormatter("%b")
	    ax1.xaxis.set_major_formatter(date_fmt)
	    ax1.legend(loc='best')

	    ax2 = fig.add_subplot(1, 2, 2)
	    #ax2.title('Linear regression for year %04i'%start_date.year)
	    ax2.plot(discharge_for_year, func(p_est, model_data), 'kx', label='data')
	    ax2.plot(xs, ys, 'k-', label='r: %2.2f, grad: %2.2f, int: %2.2f'%(r_val, a, b))
	    ax2.set_xlabel(r'Observed discharge ($m^3/s$)')
	    ax2.set_ylabel(r'Modelled discharge ($m^3/s$)')
	    #ax2.legend(loc='best')

	    if self.save_pics:
		plt.savefig('%s/%s_%s'%(self.output_dir, k, 'apply_results2.png'))
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
	    date_fmt = matplotlib.dates.DateFormatter("%b")
	    ax1.xaxis.set_major_formatter(date_fmt)
	    ax1.legend(loc='best')

	    ax2 = fig.add_subplot(1, 2, 2)
	    #ax2.title('Linear regression for year %04i'%start_date.year)
	    ax2.plot(discharge_for_year, func(p_est, model_data), 'kx', label='data')
	    ax2.plot(xs, ys, 'k-', label='r: %2.2f, grad: %2.2f, int: %2.2f'%(r_val, a, b))
	    ax2.set_xlabel(r'Observed discharge ($m^3/s$)')
	    ax2.set_ylabel(r'Modelled discharge ($m^3/s$)')
	    #ax2.legend(loc='best')

	    if self.save_pics:
		plt.savefig('%s/%s_%s'%(self.output_dir, k, 'apply_results2.png'))
	    if self.show_pics:
		plt.show()
