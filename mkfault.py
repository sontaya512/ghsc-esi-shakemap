#!/usr/bin/env python

#stdlib imports
from copy import deepcopy
import argparse
import os.path
from datetime import datetime

#third party imports
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from pyshake.shakelib.vector import Vector
from openquake.hazardlib.geo import point
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo.utils import get_orthographic_projection
import sys

def mapCoords(x,y,z,widths,d,useDepth=False):
    west = x.min()
    east = x.max()
    south = y.min()
    north = y.max()
    proj = get_orthographic_projection(west,east,north,south)
    surfaces = []
    for i in range(0,len(x)-1):
        #Project the top edge coordinates
        p0x,p0y = proj(x[i],y[i])
        p1x,p1y = proj(x[i+1],y[i+1])
        
        #Get the rotation angle defined by these two points 
        dx = p1x-p0x
        dy = p1y-p0y
        theta = np.arctan2(dx,dy)
        R = np.array([[np.cos(theta),-np.sin(theta)],
                     [np.sin(theta),np.cos(theta)]])

        #Rotate the top edge points into a new coordinate system (vertical line)
        p0 = np.array([p0x,p0y])
        p1 = np.array([p1x,p1y])
        p0p = np.dot(R,p0)
        p1p = np.dot(R,p1)

        #Get right side coordinates in project,rotated system
        if useDepth:
            p3xp = p0p[0] + widths[i]
            p3yp = p0p[1]
            p2xp = p1p[0] + widths[i]
            p2yp = p1p[1]
        else:
            dy = np.sin(d[i]) * widths[i]
            dx = np.cos(d[i]) * widths[i]
            p3xp = p0p[0] + dx
            p3yp = p0p[1]
            p2xp = p1p[0] + dx
            p2yp = p1p[1]

        #Get right side coordinates in un-rotated projected system
        p3p = np.array([p3xp,p3yp])
        p2p = np.array([p2xp,p2yp])
        Rback = np.array([[np.cos(-theta),-np.sin(-theta)],
                          [np.sin(-theta),np.cos(-theta)]])
        p3 = np.dot(Rback,p3p)
        p2 = np.dot(Rback,p2p)
        p3x = np.array([p3[0]])
        p3y = np.array([p3[1]])
        p2x = np.array([p2[0]])
        p2y = np.array([p2[1]])

        #project lower edge points back to lat/lon coordinates
        lon3,lat3 = proj(p3x,p3y,reverse=True)
        lon2,lat2 = proj(p2x,p2y,reverse=True)

        #turn these coordinates into a quad
        P0 = point.Point(x[i],y[i],z[i])
        P1 = point.Point(x[i+1],y[i+1],z[i+1])
        P2 = point.Point(lon2,lat2,z[i]+dy)
        P3 = point.Point(lon3,lat3,z[i]+dy)
        surfaces.append([P0,P1,P2,P3])

    return surfaces
        
def main(pargs):
    nargin = len(pargs.coords)
    if nargin < 6:
        print 'You must specify at least two top edge points each with (x y z) coordinates.'
        sys.exit(1)
    if (nargin % 3) != 0:
        print 'Each point must have 3 coordinates (x y z) per top edge point.'
        sys.exit(1)
    npoints = nargin/3
    nquads = ((npoints*2 - 4)/2) + 1
    if pargs.widths is None or len(pargs.widths) != nquads:
        print 'You must specify %i widths' % nquads
        sys.exit(1)
    if pargs.dips is not None and pargs.depths is not None:
        print 'You must specify %i depths or %i dips, not both.' % (nquads,nquads)
        sys.exit(1)
    if pargs.widths is None or len(pargs.widths) != nquads:
        print 'You must specify %i widths' % nquads
        sys.exit(1)
    if pargs.dips is not None and len(pargs.dips) != nquads:
        print 'You must specify %i dips' % nquads
        sys.exit(1)
    if pargs.depths is not None and len(pargs.depths) != nquads:
        print 'You must specify %i depths' % nquads
        sys.exit(1)
    topedge = []
    x = np.array(pargs.coords[1::3])
    y = np.array(pargs.coords[0::3])
    z = np.array(pargs.coords[2::3])

    if pargs.dips:
        surfaces = mapCoords(x,y,z,pargs.widths,pargs.dips,useDepth=False)
    if pargs.depths:
        surfaces = mapCoords(x,y,z,pargs.widths,pargs.depths,useDepth=True)

    if pargs.plotfile:
        fig = plt.figure()
        ax0 = fig.add_subplot(2,1,1)
        ax1 = fig.add_subplot(2,1,2, projection='3d')
        for quad in surfaces:
            P0,P1,P2,P3 = quad
            xp = np.array([P0.longitude,P1.longitude,P2.longitude,P3.longitude,P0.longitude])
            yp = np.array([P0.latitude,P1.latitude,P2.latitude,P3.latitude,P0.latitude])
            zp = np.array([-P0.depth,-P1.depth,-P2.depth,-P3.depth,-P0.depth])
            ax0.plot(xp,yp)
            ax0.set_xlabel('Longitude')
            ax0.set_xlabel('Latitude')
            ax1.plot(xp,yp,zp)
            ax1.set_xlabel('Longitude')
            ax1.set_xlabel('Latitude')
            ax1.set_zlabel('Depth')
            ax0.axis('equal')
            ax1.axis('equal')
        plt.savefig(pargs.plotfile)

    if pargs.outfile:
        f = open(pargs.outfile,'wt')
        f.write('#Fault file generated by mkfault.py at %s\n' % (datetime.utcnow()))
        for quad in surfaces:
            P0,P1,P2,P3 = quad
            f.write('%.4f %.4f %.4f\n' % (P0.latitude,P0.longitude,P0.depth))
            f.write('%.4f %.4f %.4f\n' % (P1.latitude,P1.longitude,P1.depth))
            f.write('%.4f %.4f %.4f\n' % (P2.latitude,P2.longitude,P2.depth))
            f.write('%.4f %.4f %.4f\n' % (P3.latitude,P3.longitude,P3.depth))
            f.write('%.4f %.4f %.4f\n' % (P0.latitude,P0.longitude,P0.depth))
            f.write('>\n')
        f.close()
    
    
if __name__ == '__main__':
    desc = '''Create a multi-segment fault file.  Each segment can only contain one quadrilateral.
    Usage:
    Create a two segment fault where the top edge depths are 0 and the bottom edge depths are 25 and 35 km, with widths of 10 and 12 km. 
    %(prog)s 34.261757 -118.300781 0 34.442982 -118.359146 0 34.642071 -118.346786 0 -w 10.0 12.0 -d 25.0 35.0
    '''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('coords', type=float, nargs='+',
                        help='Top edge coordinates')
    parser.add_argument('-w','--widths', dest='widths', type=float,nargs='+', help='specify widths (must match number of quads)')
    parser.add_argument('-i','--dips', dest='dips', type=float,nargs='+', help='specify dips (must match number of quads)')
    parser.add_argument('-d','--depths', dest='depths', type=float,nargs='+', help='specify depths (must match number of quads)')
    parser.add_argument('-p','--plotfile', dest='plotfile',type=str,help='Generate a plot of the fault')
    parser.add_argument('-o','--outfile', dest='outfile', type=str, help='specify output fault text file')
    args = parser.parse_args()
    main(args)

    

    
