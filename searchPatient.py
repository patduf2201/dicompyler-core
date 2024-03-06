from dicompylercore import dicomparser
from os import walk
from shutil import copyfile

dicomDir = 'I:\\RTH_SAI_Trumpet\\Batch01'
targetDir = 'I:\\RTH_SAI_Trumpet\\recovered'
patientIdSet = { '3784315T', '0416198D', '0156738T', '3108688C', '3795153G', '3788691R', '3784315T', '3553497Z', '6686562W', '3095743M', '3180863C', '0286192L', '0198588Z', '0282992Y', '0388430D', '0335618H', '3188204C', '0402174X' }

files = []
for (dirpath, dirnames, filenames) in walk(dicomDir):
    files.extend(filenames)
    break

for f in files:
    dicomFile = "{}\\{}".format(dicomDir, f)
    dp = dicomparser.DicomParser(dicomFile)
    patient = dp.GetDemographics()
    if patient['id'] in patientIdSet:
        print(f)
        print(patient)
        copyfile(dicomFile, "{}\\{}".format(targetDir, f))
print('Finished')
