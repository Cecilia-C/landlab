# -*- coding: utf-8 -*-
"""
test_sink_filler:

Created on Tues Oct 20, 2015

@author: dejh
"""

import landlab
from landlab import RasterModelGrid, FieldError
from landlab.components.flow_routing.route_flow_dn import FlowRouter
from landlab.components.sink_fill.fill_sinks import HoleFiller
from numpy import sin, pi
import numpy as np  # for use of np.round
from numpy.testing import assert_array_equal, assert_array_almost_equal
from landlab import BAD_INDEX_VALUE as XX
from nose.tools import (with_setup, assert_true, assert_false, assert_raises,
                        assert_almost_equal)
try:
    from nose.tools import (assert_is, assert_set_equal, assert_dict_equal)
except ImportError:
    from landlab.testing.tools import (assert_is, assert_set_equal,
                                       assert_dict_equal)


def setup_dans_grid1():
    """
    Create a 7x7 test grid with a well defined hole in it.
    """
    global hf, mg
    global z, r_new, r_old, A_new, A_old, s_new, depr_outlet_target
    global lake, outlet, outlet_array

    mg = RasterModelGrid(7, 7, 1.)

    z = np.array([0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,
                  0.0,  2.0,  2.0,  2.0,  2.0,  2.0,  0.0,
                  0.0,  2.0,  1.6,  1.5,  1.6,  2.0,  0.0,
                  0.0,  2.0,  1.7,  1.6,  1.7,  2.0,  0.0,
                  0.0,  2.0,  1.8,  2.0,  2.0,  2.0,  0.0,
                  0.0,  1.0,  0.6,  1.0,  1.0,  1.0,  0.0,
                  0.0,  0.0, -0.5,  0.0,  0.0,  0.0,  0.0]).flatten()

    depr_outlet_target = np.array([XX, XX, XX, XX, XX, XX, XX,
                                   XX, XX, XX, XX, XX, XX, XX,
                                   XX, XX, 30, 30, 30, XX, XX,
                                   XX, XX, 30, 30, 30, XX, XX,
                                   XX, XX, XX, XX, XX, XX, XX,
                                   XX, XX, XX, XX, XX, XX, XX,
                                   XX, XX, XX, XX, XX, XX, XX]).flatten()

    lake = np.array([16, 17, 18, 23, 24, 25])
    outlet = 30
    outlet_array = np.array([outlet])

    mg.add_field('node', 'topographic__elevation', z, units='-')

    hf = HoleFiller(mg)


def setup_dans_grid2():
    """
    Create a 10x10 test grid with a well defined hole in it, from a flat
    surface.
    """
    global hf, mg
    global z, depr_outlet_target
    global lake, outlet, outlet_array

    lake = np.array([44, 45, 46, 54, 55, 56, 64, 65, 66])
    outlet = 35  # shouldn't be needed
    outlet_array = np.array([outlet])

    mg = RasterModelGrid(10, 10, 1.)

    z = np.ones(100, dtype=float)
    z[lake] = 0.

    depr_outlet_target = np.empty(100, dtype=float)
    depr_outlet_target.fill(XX)
    depr_outlet_target = XX  # not well defined in this simplest case...?

    mg.add_field('node', 'topographic__elevation', z, units='-')

    hf = HoleFiller(mg)


def setup_dans_grid3():
    """
    Create a 10x10 test grid with two well defined holes in it, into an
    inclined surface.
    """
    global hf, mg
    global z, depr_outlet_target
    global lake, lake1, lake2, outlet, outlet_array

    lake1 = np.array([34, 35, 36, 44, 45, 46, 54, 55, 56])
    lake2 = np.array([77, 78, 87, 88])
    guard_nodes = np.array([23, 33, 53, 63])
    lake = np.concatenate((lake1, lake2))
    outlet = 35  # shouldn't be needed
    outlet_array = np.array([outlet])

    mg = RasterModelGrid(10, 10, 1.)

    z = np.ones(100, dtype=float)
    # add slope
    z += mg.node_x
    z[guard_nodes] += 0.001
    z[lake] = 0.

    depr_outlet_target = np.empty(100, dtype=float)
    depr_outlet_target.fill(XX)
    depr_outlet_target = XX  # not well defined in this simplest case...?

    mg.add_field('node', 'topographic__elevation', z, units='-')

    hf = HoleFiller(mg)


def setup_dans_grid4():
    """
    Create a 10x10 test grid with two well defined holes in it, into an
    inclined surface. This time, one of the holes is a stupid shape, which
    will require the component to arrange flow back "uphill".
    """
    global hf, mg
    global z, depr_outlet_target
    global lake, lake1, lake2, outlet, outlet_array

    lake1 = np.array([34, 35, 36, 44, 45, 46, 54, 55, 56, 65, 74])
    lake2 = np.array([78, 87, 88])
    guard_nodes = np.array([23, 33, 53, 63, 73, 83])
    lake = np.concatenate((lake1, lake2))
    outlet = 35  # shouldn't be needed
    outlet_array = np.array([outlet])

    mg = RasterModelGrid(10, 10, 1.)

    z = np.ones(100, dtype=float)
    # add slope
    z += mg.node_x
    z[guard_nodes] += 0.001  # forces the flow out of a particular node
    z[lake] = 0.

    depr_outlet_target = np.empty(100, dtype=float)
    depr_outlet_target.fill(XX)
    depr_outlet_target = XX  # not well defined in this simplest case...?

    mg.add_field('node', 'topographic__elevation', z, units='-')

    hf = HoleFiller(mg)


@with_setup(setup_dans_grid1)
def check_fields(grid):
    """
    Check to make sure the right fields have been created.
    """
    assert_array_equal(z, mg.at_node['topographic__elevation'])
    assert_array_equal(np.zeros(mg.number_of_nodes),
                       mg.at_node['sediment_fill__depth'])
    assert_raises(FieldError, mg.at_node['drainage_area'])


@with_setup(setup_dans_grid1)
def test_get_lake_ext_margin():
    lake = np.array([16, 17, 23, 24, 25, 30, 31, 32])
    ext_margin_returned = hf.get_lake_ext_margin(lake)
    ext_margin = np.array([8, 9, 10, 11, 15, 18, 19, 22, 26, 29, 33, 36, 37,
                           38, 39, 40])
    assert_array_equal(ext_margin_returned, ext_margin)


@with_setup(setup_dans_grid1)
def test_get_lake_int_margin():
    lake = np.array([16, 17, 18, 23, 24, 25, 26, 30, 31, 32])
    ext_margin = np.array([8, 9, 10, 11, 12, 15, 19, 20, 22, 27, 29, 33, 34,
                           36, 37, 38, 39, 40])
    int_margin_returned = hf.get_lake_int_margin(lake, ext_margin)
    int_margin = np.array([16, 17, 18, 23, 25, 26, 30, 31, 32])
    assert_array_equal(int_margin_returned, int_margin)


@with_setup(setup_dans_grid1)
def test_drainage_directions_change():
    lake = np.array([23, 24])
    old_elevs = np.ones(49, dtype=float)
    old_elevs[lake] = 0.
    new_elevs = old_elevs.copy()
    new_elevs[40] = 2.
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert_false(cond)
    new_elevs[24] = 0.5
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert_false(cond)
    new_elevs[24] = 1.
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert_false(cond)
    new_elevs[24] = 1.2
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert_true(cond)


@with_setup(setup_dans_grid1)
def test_add_slopes():
    new_z = z.copy()
    outlet_elev = z[outlet]
    hf._elev[lake] = outlet_elev
    rt2 = np.sqrt(2.)
    slope_to_add = 0.1
    depr_outlet_map = np.empty_like(z)
    depr_outlet_map.fill(XX)
    depr_outlet_map[lake] = outlet
    hf._lf.depression_outlet = depr_outlet_map
    hf.lake_nodes_treated = np.array([], dtype=int)
    dists = mg.get_distances_of_nodes_to_point((mg.node_x[outlet],
                                                mg.node_y[outlet]))
    new_z[lake] = outlet_elev
    new_z[lake] += dists[lake]*slope_to_add
    # test the ones we can do easily analytically separately
    straight_north = np.array([23, 16])
    off_angle = 24
    elevs_out, lake_out = hf.add_slopes(slope_to_add, outlet)
    assert_array_equal(slope_to_add*(np.arange(2.)+1.)+outlet_elev,
                       elevs_out[straight_north])
    assert_almost_equal(slope_to_add*rt2+outlet_elev, elevs_out[off_angle])
    assert_array_equal(new_z, elevs_out)
    assert_array_equal(lake, lake_out)


@with_setup(setup_dans_grid2)
def test_filler_flat():
    """
    Very simple, though possibly degerate, case, filling a 3x3 hole up to
    the flat surface surrounding it.
    """
    hf.fill_pits()
    assert_array_equal(hf._elev[lake], np.ones(9.))
    assert_array_equal(mg.at_node['topographic__elevation'][lake],
                       np.ones(9.))


@with_setup(setup_dans_grid3)
def test_filler_inclined():
    """
    Tests a flat fill into an inclined surface, with two holes.
    """
    hf.fill_pits()
    assert_array_equal(mg.at_node['topographic__elevation'][lake1],
                       np.ones(9.)*4.)
    assert_array_equal(mg.at_node['topographic__elevation'][lake2],
                       np.ones(4.)*7.)


@with_setup(setup_dans_grid3)
def test_filler_inclined2():
    """
    Tests an inclined fill into an inclined surface, with two holes.
    """
    hf.fill_pits(apply_slope=0.1)
    hole1 = np.array([4.141421, 4.223607, 4.316228, 4.1, 4.2, 4.3, 4.141421,
                      4.223607, 4.316228])
    hole2 = np.array([7.141421, 7.223607, 7.1, 7.2])
    assert_array_almost_equal(mg.at_node['topographic__elevation'][lake1],
                              hole1)
    assert_array_almost_equal(mg.at_node['topographic__elevation'][lake2],
                              hole2)


@with_setup(setup_dans_grid4)
def test_stupid_shaped_hole():
    """
    Tests inclined fill into a surface with a deliberately awkward shape.
    Also tests the ability to pass a bool to fill_pits(), to use the default
    value of 1.e-5.
    """
    hf.fill_pits(apply_slope=True)
    hole1 = np.array([4.000014, 4.000022, 4.000032, 4.00001, 4.00002, 4.00003,
                      4.000014, 4.000022, 4.000032, 4.000028, 4.000032])
    hole2 = np.array([7.000022, 7.00001, 7.00002])
    np.array([34, 35, 36, 44, 45, 46, 54, 55, 56, 65, 74])
    # print this to check out the funky drainage arrangement...
    # print(mg.at_node['topographic__elevation'].reshape((10, 10))[3:8, 4:7])
    assert_array_almost_equal(mg.at_node['topographic__elevation'][lake1],
                              hole1)
    assert_array_almost_equal(mg.at_node['topographic__elevation'][lake2],
                              hole2)
