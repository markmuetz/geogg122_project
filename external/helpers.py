from datetime import timedelta

def daterange(start_date, end_date):
    '''Taken from:
    http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python
    
    usage: 
    #for single_date in daterange(start_date, end_date):
	#print strftime("%Y-%m-%d", single_date.timetuple())'''
    for n in range(int ((end_date - start_date).days + 1)):
	yield start_date + timedelta(n)

