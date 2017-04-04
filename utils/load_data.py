"""Program for loading data files.
"""

import sys
import os
import warnings
from numpy import array, loadtxt

def load_data(filename, minrows=10, **kwargs):
    """Find and load data from a text file.

    The data reading starts at the first matrix block of at least minrows rows
    and constant number of columns. 

    filename -- name of the file we want to load data from.
    minrows  -- minimum number of rows in the first data block.
                All rows must have the same number of floating point values.
    usecols  -- indices or names of the columns to be loaded, by default all
                columns in a data block.  Data blocks that do not contain
                sufficient number of columns are skipped.
                When usecols contains string items, they are translated to
                column indices using the findColumnNames function.  When
                usecols is a single string, it gets split to names at any
                comma or whitespace character.
    unpack   -- return data as a sequence of columns that allows tuple
                unpacking such as  x, y = loadData(FILENAME, unpack=True).
                Note transposing the loaded array as loadData(FILENAME).T
                has the same effect.
    kwargs   -- keyword arguments that are passed to numpy.loadtxt

    Return a numpy array of the data.
    See also numpy.loadtxt for more details.
    """
    # determine the arguments
    delimiter = kwargs.get('delimiter')
    usecols = kwargs.get('usecols')
    # required at least one column of floating point values
    mincv = (1, 1)
    # but if usecols is specified, require sufficient number of columns
    # where the used columns contain floats
    if usecols is not None:
        usecols = _resolveStringColumns(filename, usecols)
        kwargs['usecols'] = usecols
        hiidx = max(-min(usecols), max(usecols) + 1)
        mincv = (hiidx, len(set(usecols)))
    # Check if a line consists of floats only and return their count
    # Return zero if some strings cannot be converted.
    def countcolumnsvalues(line):
        try:
            words = line.split(delimiter)
            # remove trailing blank columns
            while words and not words[-1].strip():
                words.pop(-1)
            nc = len(words)
            if usecols is not None:
                nv = len(map(float, [words[i] for i in usecols]))
            else:
                nv = len(map(float, words))
        except (IndexError, ValueError):
            nc = nv = 0
        return nc, nv
    # make sure fid gets cleaned up
    with open(filename, 'rb') as fid:
        # search for the start of datablock
        start = ncvblock = None
        fpos = nrows = 0
        for line in fid:
            fpos += len(line)
            ncv = countcolumnsvalues(line)
            if ncv < mincv:
                start = None
                continue
            # ncv is acceptable here, require the same number of columns
            # throughout the datablock
            if start is None or ncv != ncvblock:
                ncvblock = ncv
                nrows = 0
                start = fpos - len(line)
            nrows += 1
            # block was found here!
            if nrows >= minrows:
                break
        # Return an empty array when no data found.
        # loadtxt would otherwise raise an exception on loading from EOF.
        if start is None:
            rv = array([], dtype=float)
        else:
            fid.seek(start)
            # always use usecols argument so that loadtxt does not crash
            # in case of trailing delimiters.
            kwargs.setdefault('usecols', range(ncvblock[0]))
            rv = loadtxt(fid, **kwargs)
    return rv