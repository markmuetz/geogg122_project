import os
import logging
import pylab as plt
import project_settings as settings

log = logging.getLogger('make_movie')

def make_movie(title, root, prefix, data, dates, min=None, max=None):
    """Takes a 3D data array (assumed to have len(data) == 12)
    and draws a graph for each one"""
    log.info("Making movie for " + title)

    # Preprocess data to work out max and min if user hasn't entered a value.
    if max == None:
        max = data.max()
    if min == None:
        min = data.min()

    data_dir = "%s/%s"%(settings.DATA_DIR, root)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    for i in range(len(data)):
        file_name = "%s/%s.%03d.jpg"%(data_dir, prefix, i)
        img_data = data[i]
        date = dates[i]

        plt.figure()
        plt.clf()
        plt.title("%s %s"%(title, date))
        plt.imshow(img_data,interpolation='nearest', vmin=min, vmax=max)

        plt.colorbar()
        plt.savefig(file_name)
        plt.close()

        cmd = 'convert %s %s'%(file_name, file_name.replace('.jpg','.gif'))
        os.system(cmd)
        if i % 10 == 0:
            log.debug("    Done %2.1f Percent"%(100.0 * i / len(data)))

    movie_name = "%s/%s_movie.gif"%(data_dir, prefix)
    cmd = "convert -delay 10 -loop 0 %s/%s.???.gif %s"%(data_dir, prefix, movie_name)
    os.system(cmd)
    log.info("Made movie %s"% movie_name)

def main(make_movies=False):
    if make_movies:
        make_movie("Snow Cover", "imgs/", "albedo", masked_sw_dhr, 0.0, 1.0)
        log.info("made all movies")

if __name__ == "__main__":
    main()
