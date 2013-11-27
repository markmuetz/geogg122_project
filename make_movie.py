import os
import pylab as plt
import project_settings as settings

DATA_DIR= settings.DATA_DIR

def make_movie(title, root, prefix, data, min=None, max=None):
    """Takes a 3D data array (assumed to have len(data) == 12)
    and draws a graph for each one"""
    print("making movie for " + title)

    # Preprocess data to work out max and min if user hasn't entered a value.
    if max == None:
	max = data.max()
    if min == None:
	min = data.min()

    #print("max %s, min %s"%(max, min))

    for i in range(len(data)):
	file_name = "%s%s%s.%03d.jpg"%(DATA_DIR, root, prefix, i)
	img_data = data[i]

	plt.figure()
	plt.clf()
	plt.title(title + " %i"%(i))
	plt.imshow(img_data,interpolation='nearest', vmin=min, vmax=max)

	plt.colorbar()
	plt.savefig(file_name)
	plt.close()

	cmd = 'convert %s %s'%(file_name, file_name.replace('.jpg','.gif'))
	os.system(cmd)
	if i % 10 == 0:
	    print 100.0 * i / len(data), "%"

    cmd = "convert -delay 10 -loop 0 %s%s%s.???.gif %s%s%s_movie.gif"%(DATA_DIR, root, prefix, DATA_DIR, root, prefix)
    os.system(cmd)

def main(make_movies=False):
    if make_movies:
	make_movie("Snow Cover", "imgs/", "albedo", masked_sw_dhr, 0.0, 1.0)
	print("made all movies")

if __name__ == "__main__":
    main()
