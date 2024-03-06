from dicompylercore import dicomparser, dvh, dvhcalc
import jsons

dicomDir = 'C:\\workspace\\TRUMPET\\data\\hnc\\3771192F\\15ab6c5a-f4e1f841-cc083f4e-68909fe4-8db94635\\1'
rsfile = "%s\\rtstruct.dcm" % dicomDir
dp = dicomparser.DicomParser(rsfile)
structures = dp.GetStructures()
absdvh = dvhcalc.get_dvh(refile, "%s\\rtdose.dcm" % dicomDir, 17)
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
