from dicompylercore import dicomparser, dvh, dvhcalc
import jsons

basedir = "c:/workspace/trumpet/data/RayStation/"
rsfile = basedir + "RS.dcm"
rdfile = basedir + "RD.dcm"
dp = dicomparser.DicomParser(rsfile)
structures = dp.GetStructures()
infos = []
for structure in structures.values():
    if (structure['type']!='MARKER') and (structure['type']!='CONTROL'):
        infos.append({ "id": structure['id'], "name": structure['name'], "type": structure['type'], "empty": structure['empty']})
str = jsons.dumps(infos)
f = open(basedir + "structures.json", "w")
f.write(str)
f.close()

for info in infos:
    dvhabs = dvhcalc.get_dvh(rsfile, rdfile, info['id'])
    dvhrelvol = dvhabs.relative_volume
    dvhinfo = { "bins": dvhrelvol.bins, "counts": dvhrelvol.counts, "dose_units": dvhrelvol.dose_units, "volume_units": dvhrelvol.volume_units, 
               "volumeCm3": dvhabs.volume, "maxDose": dvhabs.max, "minDose": dvhabs.min, "meanDose": dvhabs.mean,
               "D100": dvhabs.D100, "D98": dvhabs.D98, "D95": dvhabs.D95, "D2cc": dvhabs.D2cc
              }
    str = jsons.dumps(dvhinfo)
    f = open(basedir + "dvhinfo_%d.json" % info['id'], "w")
    f.write(str)
    f.close()
quit()

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
