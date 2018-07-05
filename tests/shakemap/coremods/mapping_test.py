#!/usr/bin/env python

import os
import pytest
from configobj import ConfigObj
import tempfile
import time

from shapely.geometry import Polygon
from mpl_toolkits.basemap import Basemap
from mapio.basemapcity import BasemapCities

from shakemap.coremods.mapping import getProjectedPatches
from shakemap.coremods.mapping import MapMaker
from shakemap.utils.config import get_config_paths
from shakemap.coremods.assemble import AssembleModule
from shakemap.coremods.model import ModelModule
from shakelib.utils.containers import ShakeMapOutputContainer
from shakemap.utils.utils import path_macro_sub
from shakemap.utils.config import get_logger
from impactutils.time.ancient_time import HistoricTime
from shakelib.rupture.factory import get_rupture
from shakelib.rupture.origin import Origin


def test_patches():
    # Need a basemap instance
    m = Basemap(projection='merc',
                llcrnrlat=-80,
                urcrnrlat=80,
                llcrnrlon=-180,
                urcrnrlon=180,
                resolution='c')

    # Geneirc polygon
    polygon = Polygon([[0, 0], [1, 0], [1, 1], [0, 1]])

    # Since this is not a MultiPolygon it should hit
    # untested code
    getProjectedPatches(polygon, m)


def test_mapmaker():
    installpath, datapath = get_config_paths()

    # No data no fault version just to make it faster
    evid = 'integration_test_0001'
    assemble = AssembleModule(evid, comment='Test comment.')
    assemble.execute()
    del assemble
    model = ModelModule(evid)
    model.execute()
    del model

    # Find the output container
    datafile = os.path.join(datapath, evid, 'current', 'products',
                            'shake_result.hdf')
    container = ShakeMapOutputContainer.load(datafile)

    config_file = os.path.join(installpath, 'config', 'products.conf')

    # Need other inputs for MakMaker
    config = ConfigObj(config_file)
    # datadir = os.path.join(datapath, evid, 'current', 'products')
    logger = get_logger(evid, log_option='quiet', log_file=None)
    layers = config['products']['mapping']['layers']
    layerdict = {}
    layerdict['coast'] = path_macro_sub(
        layers['coasts'], ip=installpath, dp=datapath)
    layerdict['ocean'] = path_macro_sub(
        layers['oceans'], ip=installpath, dp=datapath)
    layerdict['lake'] = path_macro_sub(
        layers['lakes'], ip=installpath, dp=datapath)
    layerdict['country'] = path_macro_sub(
        layers['countries'], ip=installpath, dp=datapath)
    layerdict['state'] = path_macro_sub(
        layers['states'], ip=installpath, dp=datapath)
    topofile = path_macro_sub(
        layers['topography'], ip=installpath, dp=datapath)
    cities = path_macro_sub(
        layers['cities'], ip=installpath, dp=datapath)

    # Add roads!!!
    layerdict['roads'] = os.path.join(installpath, 'roads')

    mapmod = MapMaker(container, topofile, layerdict, cities, logger,
                      config['products']['mapping']['operator'])
    with tempfile.TemporaryDirectory() as tmpdirname:
        mapmod.drawIntensityMap(tmpdirname)

    # Raise exception
    layerdict.pop('lake', None)
    with pytest.raises(KeyError):
        mapmod = MapMaker(container, topofile, layerdict, cities, logger,
                          config['products']['mapping']['operator'])
    # Put lake back
    layerdict['lake'] = path_macro_sub(
        layers['lakes'], ip=installpath, dp=datapath)

    # Turn it into a point source
    layerdict['lake'] = path_macro_sub(
        layers['lakes'], ip=installpath, dp=datapath)
    origin = Origin({
        'id': 'test',
        'lon': -122.5, 'lat': 37.3,
        'depth': 5.0, 'mag': 7.0, 'netid': 'us',
        'network': '', 'locstring': '',
        'time': HistoricTime.utcfromtimestamp(time.time())
    })
    rupt = get_rupture(origin)
    container.setRupture(rupt)
    mapmod = MapMaker(container, topofile, layerdict, cities, logger,
                      config['products']['mapping']['operator'])

    # Set city grid
    mapmod.setCityGrid(4, 4, 2)

    # Set figure size
    mapmod.setFigureSize(4, 4)

    # Set city list
    df = BasemapCities.loadFromGeoNames(cities).getDataFrame()
    mapmod.setCityList(df)

    # Need to use a different shakemap that includes a lake to
    # hit the _drawLakes method


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_patches()
    test_mapmaker()