Gfx Miner Readme
================

Download a bunch of .csv.gz files from crash-stats.

For some basic stats:

    python gen.py -s *.csv.gz

To get a data.csv file that you can use for data mining:

    python gen.py -r *.csv.gz > data.csv

Then import that into sqlite (ignore error about no table existing for table.sql):

    sqlite data.sqlite
    .read table.sql
    .separator \t
    .import data.csv data

Some details: the va, vb, vc, vd colums contain the portions of the driver version,
A.B.C.D so that they can be treated as numbers.  The driver column contains the
full driver version string.

Then run queries:

Display a list of Intel GPUs and their driver versions where both d3d9 and d3d10 were blocked.  Note that the grouping options specify which columns to collapse.

    SELECT COUNT(name), name, driver FROM data
       WHERE os IN ('Vista', 'Win7') AND vendor = '0x8086' AND d3d9 = '0' AND d3d10 = '0'
       GROUP BY name, driver
       ORDER BY name, va, vb, vc, cd;

Different queries are possible, if the group is modified:

    SELECT COUNT(name), name, va, vb, vc, min(vd) FROM data
       WHERE os IN ('Vista', 'Win7') AND vendor = '0x8086' AND d3d9 = '0' AND d3d10 = '0'
       GROUP BY name, driver, va, vb, vc
       ORDER BY name, va, vb, vc, cd;

This will collapse the first 3 version numbers and display only the minimum number for the fourth, thus showing the lowest minor version that was seen.

    SELECT count(name), name, webgl FROM data WHERE webgl IS NOT "" GROUP BY name, webgl ORDER BY name, webgl;

For people that attempted WebGL, show their hardware and the counts of how many succeeded and failed.


