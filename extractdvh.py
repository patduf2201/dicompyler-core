import string
import numpy as np
from dicompylercore import dicomparser, dvh, dvhcalc
import jsons
import csv

synonyms= {}
def processSynonyms(sfile: string):
    with open(sfile, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            if len(row)>2 and row[2]!='':
                synonyms[row[0]]=row[2]

def getStructureSynonym(name: string):
    if (name in synonyms.keys()):
        return synonyms[name]
    return name

def extract(basedir, targetdir):
    rsfile = basedir + "/rtstruct.dcm"
    rdfile = basedir + "/rtdose.dcm"
    dp = dicomparser.DicomParser(rsfile)
    structures = dp.GetStructures()
    infos = []
    for structure in structures.values():
        if (structure['type']!='MARKER') and (structure['type']!='CONTROL'):
            infos.append({ "id": structure['id'], "name": structure['name'], "type": structure['type']})
    str = jsons.dumps(infos)
    f = open(targetdir + "/structures.json", "w")
    f.write(str)
    f.close()

    for info in infos:
        dvhabs = dvhcalc.get_dvh(rsfile, rdfile, info['id'])
        dvhrelvol = dvhabs.relative_volume
        # Resize to bins of 2 cGy
        relcounts = np.copy(dvhrelvol.counts) if (dvhrelvol.counts.size%2==0) else np.hstack((dvhrelvol.counts, dvhrelvol.counts[-1]))
        relcounts = np.mean(relcounts.reshape(relcounts.size//2, 2), axis=1)
        relbins = np.copy(dvhrelvol.bins) if (dvhrelvol.bins.size%2==0) else np.hstack((dvhrelvol.bins, dvhrelvol.bins[-1]))
        relbins =  np.take(relbins.reshape(relbins.size//2, 2), 0, axis=1)

        dvhinfo = { "bins": dvhrelvol.bins, "counts": dvhrelvol.counts, "dose_units": dvhrelvol.dose_units, "volume_units": dvhrelvol.volume_units, 
                   "volumeCm3": dvhabs.volume, "maxDose": dvhabs.max, "minDose": dvhabs.min, "meanDose": dvhabs.mean,
                   "D100": dvhabs.D100, "D98": dvhabs.D98, "D95": dvhabs.D95, "D2cc": dvhabs.D2cc
                  }
        str = jsons.dumps(dvhinfo)
        name = getStructureSynonym(info['name'])
        f = open(targetdir + "/dvhinfo_%s.json" % name, "w")
        f.write(str)
        f.close()
    return infos
'''
absdvh = dvhcalc.get_dvh("../data/export_short/RS.dcm", "../data/export_short/RD.dcm", 17)
absdvh.describe()
dvhrel = absdvh.relative_dose(6400)
dvhrel.describe()
str = jsons.dumps(absdvh.__dict__)
f = open("../data/absdvh.json", "w")
f.write(str)
f.close()
f = open("../data/absdvh.json", "r")
str = f.read()
f.close()
readdvh = jsons.loads(str, dvh.DVH)
readdvh.describe()
quit()
'''
