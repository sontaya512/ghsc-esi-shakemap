#!/usr/bin/env python

# stdlib modules
import json
import os.path
import pathlib
import pickle
import sqlite3
import sys
import tempfile

# third party modules
import numpy as np
import pandas as pd

# local imports
from shakelib.station import TABLES, StationList

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, "..", ".."))
sys.path.insert(0, shakedir)

#
# Set SAVE to True to write new versions of the output to disk,
# set it to False to actually run the tests.
#
SAVE = False


def test_station():
    homedir = os.path.dirname(os.path.abspath(__file__))

    #
    # First test the Calexico data on its own
    #
    event = "Calexico"

    datadir = os.path.abspath(os.path.join(homedir, "station_data"))
    datadir = os.path.abspath(os.path.join(datadir, event, "input"))

    inputfile = os.path.join(datadir, "stationlist_dat.xml")
    dyfifile = os.path.join(datadir, "ciim3_dat.xml")
    xmlfiles = [inputfile, dyfifile]

    stations = StationList.loadFromFiles(xmlfiles)

    df1, _ = stations.getStationDictionary(instrumented=True)
    df2, _ = stations.getStationDictionary(instrumented=False)

    ppath = os.path.abspath(os.path.join(datadir, "..", "database", "test1.pickle"))
    if SAVE:
        ldf = [df1, df2]
        with open(ppath, "wb") as f:
            pickle.dump(ldf, f, protocol=4)
    else:
        with open(ppath, "rb") as f:
            ldf = pickle.load(f)

        saved_df1 = ldf[0]
        saved_df2 = ldf[1]

        compare_dataframes(saved_df1, df1)
        compare_dataframes(saved_df2, df2)

    #
    # Should at least hit this code
    #
    imtlist = stations.getIMTtypes()
    assert "PGA" in imtlist
    assert "PGV" in imtlist

    #
    # Add the Northridge data to the Calexico data to test
    # addData()
    #
    event = "northridge"
    datadir = os.path.abspath(os.path.join(homedir, "station_data"))
    datadir = os.path.abspath(os.path.join(datadir, event, "input"))

    inputfile = os.path.join(datadir, "hist_dat.xml")
    dyfifile = os.path.join(datadir, "dyfi_dat.xml")
    len_stat1 = len(stations.getStationDictionary(instrumented=True)[0]["id"])
    xmlfiles = [inputfile, dyfifile]
    stations = stations.addData(xmlfiles, 3)
    len_stat2 = len(stations.getStationDictionary(instrumented=True)[0]["id"])

    # Check that more stations were added
    assert len_stat2 > len_stat1

    df1, _ = stations.getStationDictionary(instrumented=True)
    df2, _ = stations.getStationDictionary(instrumented=False)

    ppath = os.path.abspath(os.path.join(datadir, "..", "database", "test2.pickle"))
    if SAVE:
        ldf = [df1, df2]
        with open(ppath, "wb") as f:
            pickle.dump(ldf, f, protocol=4)
    else:
        with open(ppath, "rb") as f:
            ldf = pickle.load(f)

        saved_df1 = ldf[0]
        saved_df2 = ldf[1]

        compare_dataframes(saved_df1, df1)
        compare_dataframes(saved_df2, df2)


def test_station2():
    #
    # Test the wenchuan data
    #
    homedir = os.path.dirname(os.path.abspath(__file__))

    event = "wenchuan"

    datadir = os.path.abspath(os.path.join(homedir, "station_data"))
    datadir = os.path.abspath(os.path.join(datadir, event, "input"))

    inputfile = os.path.join(datadir, "stationlist.xml")
    xmlfiles = [inputfile]

    stations = StationList.loadFromFiles(xmlfiles)

    df1, _ = stations.getStationDictionary(instrumented=True)
    # Check Keys pressent
    assert "PGA" in _
    assert "PGV" in _
    assert "SA(0.3)" in _
    assert "SA(1.0)" in _
    assert "SA(3.0)" in _
    assert "PGV_sd" in df1
    assert "PGV" in df1
    assert "SA(0.3)" in df1
    assert "SA(1.0)" in df1
    assert "SA(3.0)" in df1
    assert "id" in df1
    df2, _ = stations.getStationDictionary(instrumented=False)
    # Check Keys pressent
    assert "MMI" in _
    ppath = os.path.abspath(os.path.join(datadir, "..", "database", "test3.pickle"))
    if SAVE:
        ldf = [df1, df2]
        with open(ppath, "wb") as f:
            pickle.dump(ldf, f, protocol=4)
    else:
        with open(ppath, "rb") as f:
            ldf = pickle.load(f)

        saved_df1 = ldf[0]
        saved_df2 = ldf[1]

        compare_dataframes(saved_df1, df1)
        compare_dataframes(saved_df2, df2)

        #
        # Dump the database to SQL and then restore it to a new
        # StationList object. Compare dataframes.
        #
        sql = stations.dumpToSQL()

        stations2 = StationList.loadFromSQL(sql)

        df1, _ = stations2.getStationDictionary(instrumented=True)
        df2, _ = stations2.getStationDictionary(instrumented=False)

        compare_dataframes(saved_df1, df1)
        compare_dataframes(saved_df2, df2)


def test_station3():
    #
    # Exercise the geojson code.
    #
    homedir = os.path.dirname(os.path.abspath(__file__))

    event = "wenchuan"

    datadir = os.path.abspath(os.path.join(homedir, "station_data"))
    datadir = os.path.abspath(os.path.join(datadir, event, "input"))

    inputfile = os.path.join(datadir, "stationlist.xml")
    xmlfiles = [inputfile]

    stations = StationList.loadFromFiles(xmlfiles)

    myjson = stations.getGeoJson()

    ofd = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    jsonfile = ofd.name
    ofd.write(json.dumps(myjson).encode())
    ofd.close()

    stations2 = StationList.loadFromFiles([jsonfile])

    os.unlink(jsonfile)

    df1, _ = stations.getStationDictionary(instrumented=True)
    df2, _ = stations2.getStationDictionary(instrumented=True)
    compare_dataframes(df1, df2)

    df1, _ = stations.getStationDictionary(instrumented=False)
    df2, _ = stations2.getStationDictionary(instrumented=False)
    compare_dataframes(df1, df2)


def test_station4():
    homedir = os.path.dirname(os.path.abspath(__file__))

    event = "northridge"
    datadir = os.path.abspath(os.path.join(homedir, "station_data"))
    datadir = os.path.abspath(os.path.join(datadir, event, "input"))

    dyfifile = os.path.join(datadir, "dyfi_dat.xml")
    xmlfiles = [dyfifile]

    stations = StationList.loadFromFiles(xmlfiles)

    df1, _ = stations.getStationDictionary(instrumented=True)  # noqa
    df2, _ = stations.getStationDictionary(instrumented=False)  # noqa
    assert df1 is None


def test_station5():
    homedir = os.path.dirname(os.path.abspath(__file__))

    event = "Calexico"

    datadir = os.path.abspath(os.path.join(homedir, "station_data"))
    datadir = os.path.abspath(os.path.join(datadir, event, "input"))

    inputfile = os.path.join(datadir, "stationlist_dat.xml")
    dyfifile = os.path.join(datadir, "ciim3_dat.xml")

    xmlfiles = [inputfile, dyfifile]
    stations1 = StationList.loadFromFiles(xmlfiles)
    #
    # Load the data more than once to exercise the code that handles
    # repeated entries.
    #
    xmlfiles = [inputfile, inputfile, dyfifile, dyfifile]
    stations2 = StationList.loadFromFiles(xmlfiles)

    df1, _ = stations1.getStationDictionary(instrumented=True)
    df2, _ = stations2.getStationDictionary(instrumented=True)

    compare_dataframes(df1, df2)


def compare_dataframes(df1, df2):
    assert sorted(list(df1.keys())) == sorted(list(df2.keys()))

    idx1 = np.argsort(df1["id"])
    idx2 = np.argsort(df2["id"])

    for key in df1.keys():
        if df1[key].dtype in [np.float32, np.float64]:
            np.testing.assert_allclose(df1[key][idx1], df2[key][idx2], equal_nan=True)
        else:
            assert (df1[key][idx1] == df2[key][idx2]).all()


def test_packet():
    datadir = pathlib.Path(__file__).parent / "station_data" / "elmonte"
    db = sqlite3.connect(":memory:")
    stations_list = StationList(db)
    sta_set = set()
    imt_set = set()
    amp_set = set()
    min_nresp = 1
    shakemap_file = datadir / "ci38695658_groundmotions_dat.json"
    stations, amps, _ = stations_list._parse_shakemap_json(
        shakemap_file, min_nresp, sta_set, imt_set, amp_set
    )
    station_columns = [
        "station_id",
        "network",
        "code",
        "name",
        "lat",
        "lon",
        "elev",
        "vs30",
        "stddev",
        "instrumented",
        "source",
        "refid",
    ]
    amp_columns = [
        "station_id",
        "imt_type",
        "channel",
        "orientation",
        "amplitude",
        "stddev",
        "flag",
        "nresp",
    ]
    shakemap_stations_frame = pd.DataFrame(stations, columns=station_columns)
    shakemap_amps_frame = pd.DataFrame(amps, columns=amp_columns)

    sta_set = set()
    imt_set = set()
    amp_set = set()

    packet_file = datadir / "ci38695658_groundmotion_packet.json"
    stations, amps, _ = stations_list._parse_groundpacket_json(
        packet_file, sta_set, imt_set, amp_set
    )
    packet_stations_frame = pd.DataFrame(stations, columns=station_columns)
    packet_amps_frame = pd.DataFrame(amps, columns=amp_columns)
    for idx, shake_group in shakemap_amps_frame.groupby(["station_id", "imt_type"]):
        idx1 = packet_amps_frame["station_id"] == idx[0]
        idx2 = packet_amps_frame["imt_type"] == idx[1]
        packet_group = packet_amps_frame[(idx1) & (idx2)]
        shake_vals = np.sort(shake_group["amplitude"].values)
        packet_vals = np.sort(packet_group["amplitude"].values)
        np.testing.assert_allclose(shake_vals, packet_vals, rtol=1e-2)


if __name__ == "__main__":
    test_station()
    test_station2()
    test_station3()
    test_station4()
    test_station5()
    test_packet()
