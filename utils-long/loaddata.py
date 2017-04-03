#!/usr/bin/env python
##############################################################################
#
# diffpy.pdfgetx    by DANSE Diffraction group
#                   Simon J. L. Billinge
#                   (c) 2008 Trustees of the Columbia University
#                   in the City of New York.  All rights reserved.
#
# File coded by:    Pavol Juhas
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSENOTICE.txt for license information.
#
##############################################################################

"""Program for quick plotting of text data files.
"""

import sys
import os
import warnings
from diffpy.pdfgetx.log import plog

# suppress deprecation warning that shows in IPython.iplib module
warnings.filterwarnings('ignore',
        module='matplotlib.backends.backend_gtk', category=DeprecationWarning)

# Constants ------------------------------------------------------------------

_PLOTDATA_BANNER = '''\
Use "plotdata" for more plots and "findfiles" to generate file names.
See "filenames" for the current data files.

'''

# Functions ------------------------------------------------------------------

def plotdata(filenames, style=None, x=None, y=None, hold=None, **kwargs):
    """Plot one or more text data files.

    filenames    -- string or an iterable of string file names
    style        -- optional style argument for the pyplot plot function
    x, y         -- column or columns to be used for x and y data.
                    Most often a single integer or an iterable of
                    integer indices.  Can be a single string that is split
                    at commas and converted either to integers or column names.
                    A special symbol "." can be used for data index.
                    When not specified, use the first two columns.
    hold         -- add new lines when True, replace the old lines when
                    False or reuse the axes hold state if None
    kwargs       -- any other keyword arguments passed to the pyplot
                    plot function.

    Return a list of Line2D instances.
    """
    rv = []
    if isinstance(filenames, basestring):
        filenames = [filenames]
    else:
        filenames = list(filenames)
    if not filenames:
        return rv
    xydatasets = [_loadplotdata(f, x, y) for f in filenames]
    linelabels = [os.path.basename(f) for f in filenames]
    # import plotting stuff only when truly needed
    from matplotlib.pyplot import plot
    for pargs, plabel in zip(xydatasets, linelabels):
        if style is not None:
            pargs += (style,)
        # use the hold argument for the first plot,
        # for all others use hold=True.
        phold = True if rv else hold
        rv += plot(*pargs, hold=phold, label=plabel, **kwargs)
    return rv


def main(args=sys.argv[1:]):
    from diffpy.pdfgetx.functs import pylab_draw_show, findfiles
    from diffpy.pdfgetx.interaction import isIPythonRunning
    from diffpy.pdfgetx.interaction import createIPythonInterface
    from diffpy.pdfgetx.interaction import toSList
    ipyface = None
    exitcode = 2
    try:
        opts, pargs = _processoptions(args)
        if opts.openmanual:
            from diffpy.pdfgetx.manual import openHTMLManual
            openHTMLManual('plotdata.html')
            return 0
        filenames = pargs
        if opts.find:
            filenames = findfiles(pargs)
        if opts.listfiles:
            for f in filenames:
                print f
            return 0
        if not filenames:
            plog.warning("No input files, nothing to do.")
            return 0
        if not isIPythonRunning():
            ipyface = createIPythonInterface()
        plotdata(filenames, style=opts.style, x=opts.x, y=opts.y)
        pylab_draw_show(mainloop=False)
        exitcode = 0
        if ipyface:
            ipyface.push(dict(plotdata=plotdata), interactive=False)
            ipyface.push(dict(findfiles=findfiles), interactive=False)
            filenames = toSList(filenames)
            ipyface.push(dict(filenames=filenames), interactive=True)
            ipyface.mainloop(banner=_PLOTDATA_BANNER)
    except (IOError, ValueError), e:
        sys.stderr.write("%s\n" % e)
        exitcode = 1
    except SystemExit, e:
        exitcode = e.code
    # All done here.
    return exitcode

# Local Helpers --------------------------------------------------------------

def _loadplotdata(filename, xi, yi):
    '''Load x and y arrays from filename as per the xi, yi identifiers.

    Return a tuple of (xdata, ydata) that can be used with the plot function.
    '''
    import numpy
    from diffpy.pdfgetx.functs import loadData
    xi = _parsecolumnid(xi)
    yi = _parsecolumnid(yi)
    if yi is None:
        if xi is not None:
            emsg = "y-column must be specified for explicit x."
            raise ValueError(emsg)
        # xi and yi are both None here
        d = loadData(filename)
        if d.ndim <= 1:
            rv = numpy.arange(d.size, dtype=float), d
        else:
            rv = d[:,0], d[:,1]
        return rv
    # here yi is not None
    if xi is None:
        xi = [0]
    nx = len(xi)
    uc = list(xi) + list(yi)
    dotindices = [i for i, c in enumerate(uc) if c == '.']
    dotalias = ([c for c in uc if c != '.'] + [0])[0]
    for i in dotindices:
        uc[i] = dotalias
    d = loadData(filename, usecols=uc)
    rv = d, d
    if d.size:
        nrows = d.shape[0]
        d = d.reshape((nrows, -1))
        d[:,dotindices] = numpy.arange(nrows).reshape(nrows, -1)
        rv = d[:,:nx].squeeze(), d[:,nx:].squeeze()
    return rv


def _processoptions(args):
    """Process the command line options and arguments.

    args -- command line arguments without argzero

    Return a (opts, pargs) tuple of option values and
    the remaining positional arguments.
    """
    from optparse import OptionParser
    from diffpy.pdfgetx import __version__
    parser = OptionParser("usage: %prog [options] file1.dat file2.dat ...")
    parser.allow_interspersed_args = True
    parser.version = '%prog ' + __version__
    # fix help string for --help
    oh = parser.get_option('--help')
    oh.help = 'Show this help message and exit.'
    parser.add_option('-V', '--version', action="version",
        help="Show program version and exit.")
    parser.add_option("--manual",
            action="store_true", dest='openmanual',
            help=("Open manual in a web browser and exit."))
    parser.add_option("-f", "--find", action="store_true",
            help="Use arguments as file name patterns and "
                    "plot the matching files.")
    parser.add_option("-l", "--list",
            action="store_true", dest='listfiles',
            help=("List all input files without plotting.  "
                  "Should be used with the --find option."))
    parser.add_option("-x", type="string", default=None,
            help="Index or name of the x-column to plot.  "
                 'When "." use the data-row index as x.')
    parser.add_option("-y", type="string", default=None,
            help="Index or name of the y-column to plot.  "
                 'May contain a comma separated list of several names or '
                 'indices or Python-like ranges, like "1,2", "G", "0:6:2".  '
                 'Column indices are zero based therefore the first column '
                 'is specified as "0".')
    parser.add_option("-s", "--style", type="string", default=None,
            help="Optional plot style string.  See matplotlib "
                 "documentation for the plot function for a list of "
                 "available styles.")
    opts, pargs = parser.parse_args(args)
    return opts, pargs


def _parsecolumnid(sx):
    '''Helper function that converts a string column identifier to
    either None or a list of integer indices, slice objects and
    string column names, aka something that is digestable as the
    loadData usecols argument.
    '''
    import re
    import numpy
    mxint = re.compile(r'^[+-]?\d+$')
    if isinstance(sx, basestring):
        sx = filter(None, [w.strip() for w in sx.split(',')])
    elif numpy.issubdtype(type(sx), int):
        sx = [sx]
    if sx is None or not len(sx):
        return None
    rv = []
    emsg0 = "invalid column identifier %s"
    for w in sx:
        if numpy.issubdtype(type(w), int):
            rv.append(w)
            continue
        if w[:1].isalpha() or w[:1] == '@' or w == '.':
            rv.append(w)
            continue
        if mxint.match(w):
            rv.append(int(w))
            continue
        if 1 <= w.count(':') <= 2:
            a0 = [w1.strip() for w1 in w.split(':')]
            a0ck = [(x == '' or mxint.match(x)) for x in a0]
            if not all(a0ck):
                raise ValueError(emsg0 % repr(w))
            a1 = [int(x) if x else None for x in a0]
            a1 = a1 + (3 - len(a1)) * [None]
            a2 = slice(*a1)
            if a2.stop is not None:
                rv += numpy.r_[a2].tolist()
                continue
        raise ValueError(emsg0 % repr(w))
    return rv

# Kick starter ---------------------------------------------------------------

if __name__=="__main__":
    sys.exit(main())
