#!/bin/python

import sys, os, re, gzip
from devices import DEVICE_DATA

DEBUG = False
try:
    sys.argv.remove("-d")
    DEBUG = True
except ValueError:
    pass

SummaryOnly = False
try:
    sys.argv.remove("-s")
    SummaryOnly = True
except ValueError:
    pass

RawOnly = False
try:
    sys.argv.remove("-r")
    RawOnly = True
except ValueError:
    pass

# We care about Firefox >= 16 only
MinimumVersion = 16

class Counts(object):
    def __init__(self):
        self.total = 0
        self.versionSkip = 0
        self.multiGPUSkip = 0
        self.bogusDataSkip = 0
    def inc(self): self.total = self.total + 1
    def badVersion(self): self.versionSkip = self.versionSkip + 1
    def badGPUs(self): self.multiGPUSkip = self.multiGPUSkip + 1
    def badData(self): self.bogusDataSkip = self.bogusDataSkip + 1

class FeatureStatus(object):
    def __init__(self, name):
        self.name = name
        self.success = 0
        self.failure = 0

    def record(self, n):
        if n == 1:
            self.success = self.success + 1
        elif n == 0:
            self.failure = self.failure + 1

allCounts = Counts()
d3d9Feature = FeatureStatus("d3d9")
d3d10Feature = FeatureStatus("d3d10")
d2dFeature = FeatureStatus("d2d")
webglFeature = FeatureStatus("webgl")

def processFile(fn):
    if fn.endswith("gz"):
        fp = gzip.GzipFile(fn, "rb")
    else:
        fp = open(fn, "rb")

    header = fp.readline().split("\t")

    PRODUCT_COL = header.index("product")
    VERSION_COL = header.index("version")
    BUILD_COL = header.index("build")
    BRANCH_COL = header.index("branch")
    OS_NAME_COL = header.index("os_name")
    OS_VERSION_COL = header.index("os_version")
    APP_NOTES_COL = header.index("app_notes")

    for rawline in fp:
        line = rawline.split("\t")
    
        if line[PRODUCT_COL] != "Firefox" or line[OS_NAME_COL] != "Windows NT":
            continue
    
        allCounts.inc()
    
        vstr = line[VERSION_COL]
        if "." in vstr:
            vstr = vstr[0:vstr.find(".")]
        try:
            versionNumber = int(vstr)
        except:
            versionNumber = 0

        if versionNumber < MinimumVersion:
            allCounts.badVersion()
            continue
    
        appnotes = line[APP_NOTES_COL]
        if "Has dual GPUs" in appnotes:
            allCounts.badGPUs()
            continue
    
        osVersion = line[OS_VERSION_COL]
        if len(osVersion) < 3:
            if DEBUG: print "BOGUS OSVERSION:", osVersion
            allCounts.badData()
            continue
    
        if osVersion[0:3] == "5.1" or osVersion[0:3] == "5.2":
            osVersion = "WinXP"
        elif osVersion[0:3] == "6.0":
            osVersion = "Vista"
        elif osVersion[0:3] == "6.1":
            osVersion = "Win7"
        elif osVersion[0:3] == "6.2":
            osVersion = "Blue"
        else:
            if DEBUG: print "BOGUS OSVERSION:", osVersion
            allCounts.badData()
            continue
    
        adapterDevice = ""
        adapterDriverVersion = ""
    
        gotD2D = ""
        gotD3D9 = ""
        gotD3D10 = ""
        gotWebGL = ""
    
        m = re.match(r".*AdapterVendorID: (0x[0-9a-f]{4}).*AdapterDeviceID: (0x[0-9a-f]{4}).*AdapterDriverVersion: ?([0-9.]+| ?)", appnotes)
        if m:
            adapterVendor = m.group(1)
            adapterDevice = m.group(2)
            adapterDriverVersion = m.group(3)
        else:
            if DEBUG: print "BOGUS APPNOTES (fx version %s):" % line[VERSION_COL], "'" + appnotes + "'"
            allCounts.badData()
            continue
    
        if not adapterDriverVersion:
            allCounts.badData()
            continue

        if "D3D9 Layers+" in appnotes:   gotD3D9 = 1
        elif "D3D9 Layers-" in appnotes: gotD3D9 = 0
    
        if "D3D10 Layers+" in appnotes:   gotD3D10 = 1
        elif "D3D10 Layers-" in appnotes: gotD3D10 = 0
    
        if "D2D+" in appnotes:   gotD2D = 1
        elif "D2D-" in appnotes: gotD2D = 0
    
        if "WebGL+" in appnotes:   gotWebGL = 1
        elif "WebGL-" in appnotes: gotWebGL = 0

        d3d9Feature.record(gotD3D9)
        d3d10Feature.record(gotD3D10)
        d2dFeature.record(gotD2D)
        webglFeature.record(gotWebGL)

        versionSplit = adapterDriverVersion.split(".")
        if len(versionSplit) != 4:
            versionSplit = ["x","x","x","x"]

        try:
            name = DEVICE_DATA[adapterVendor[2:]][adapterDevice[2:]]
        except:
            name = ""

        if not SummaryOnly:
            print "\t".join(map(str, [osVersion, adapterVendor, adapterDevice, name, adapterDriverVersion, "\t".join(versionSplit), gotD3D9, gotD3D10, gotD2D, gotWebGL]))

    fp.close()

if not SummaryOnly and not RawOnly:
    print "\t".join(["os", "vendor", "device", "name", "driver", "va", "vb", "vc", "vd", "d3d9", "d3d10", "d2d", "webgl"])

for fn in sys.argv[1:]:
    processFile(fn)

def pct(a, b = None):
    if b is None: b = allCounts.total
    return (a / float(b)) * 100.0

def printFeature(feature):
    print "% 10s: Success: % 8d %5.2f%%  Failure: % 8d %5.2f%%" % (feature.name, feature.success, pct(feature.success), feature.failure, pct(feature.failure))


if not RawOnly:
    print "Total:   %d" % (allCounts.total)
    print "Skipped: Bogus: % 10d %5.2f%% Multi-GPU: % 10d %5.2f%% Version<%s: % 10d %5.2f%%" % (
        allCounts.bogusDataSkip, pct(allCounts.bogusDataSkip),
        allCounts.multiGPUSkip, pct(allCounts.multiGPUSkip),
        str(MinimumVersion),
        allCounts.versionSkip, pct(allCounts.versionSkip))

    for feature in [d3d9Feature, d3d10Feature, d2dFeature, webglFeature]:
        printFeature(feature)

