import os
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from extractdvh import extract, processSynonyms
import csv
import hashlib
import logging
from datetime import date, datetime

def anonString(str):
    prefixed = 'TRUMPETHNC$!' + str
    return 'CHUL' + hashlib.sha1(prefixed.encode('ISO_8859_1')).hexdigest()

def anonDate(dt):
    anonDate = datetime.strptime(dt, '%Y%m%d')
    anonDate = date(anonDate.year, anonDate.month, 1)
    return datetime.strftime(anonDate, '%Y%m%d')

#workDir = 'c:/workspace/trumpet/data/hnc'
workDir = '/var/data/hnc'
processSynonyms('structures_dict.csv')
fcsv = open(f'{workDir}/dvhs.csv', 'w', newline='')
csvwriter = csv.DictWriter(fcsv, delimiter=',', dialect='excel', fieldnames=['numnat', 'studyDate', 'doseDate', 'studyId', 'studyName', 'nbStructures', 'structures', 'dirDvhs'])
csvwriter.writeheader()
fanoncsv = open(f'{workDir}anon/dvhs.csv', 'w', newline='')
anoncsvwriter = csv.DictWriter(fanoncsv, delimiter=',', dialect='excel', fieldnames=['numnat', 'studyDate', 'doseDate', 'studyId', 'studyName', 'nbStructures', 'structures', 'dirDvhs'])
anoncsvwriter.writeheader()
auth = HTTPBasicAuth('orthanc', 'orthanc')
url = "http://si-s-serv1041.st.chulg:8042/studies"
try:
    resp = requests.get(url,auth=auth)
    resp.raise_for_status()
    studies = resp.json()
    nbStudies = len(studies)
    iStudy = 1
    for studyName in studies:
        url = f'http://si-s-serv1041.st.chulg:8042/studies/{studyName}'
#    studyName='0b33e2ff-ae5ebd1b-5a2f9e66-61225e3f-67beb356'
#    for x in range(1):
        url = f'http://si-s-serv1041.st.chulg:8042/studies/{studyName}'
        resp = requests.get(url, auth=auth)
        resp.raise_for_status()
        study = resp.json()
        urlRtStruct = None
        patientId = study['PatientMainDicomTags']['PatientID']
        studyDate = study['MainDicomTags']['StudyDate']
        studyID = study['MainDicomTags']['StudyID']
        print(f'Processing patient {patientId}, study {studyName}. Study {iStudy} on {nbStudies} studies')
        iStudy = iStudy + 1
        anonStudyDate = anonDate(studyDate)
        for serieName in study['Series']:
            url = f'http://si-s-serv1041.st.chulg:8042/series/{serieName}'
            resp = requests.get(url,auth=auth)
            resp.raise_for_status()
            serie = resp.json()
            tags = serie['MainDicomTags']
            instances = serie['Instances']
            if tags['Modality']=='RTSTRUCT':
                assert len(instances)==1
                if urlRtStruct!=None:
                    logging.warn(f"Multiple RTSTRUCTs found for patient {patientId}, study {studyName}.")
                else:
                   urlRtStruct = f'http://si-s-serv1041.st.chulg:8042/instances/{instances[0]}/file'
        if urlRtStruct==None:
            print(f"Missing RT Struct data for {patientId}, study {studyName}")
        urlRtDose = None
        nbRtDose = 1
        for serieName in study['Series']:
            url = f'http://si-s-serv1041.st.chulg:8042/series/{serieName}'
            resp = requests.get(url,auth=auth)
            resp.raise_for_status()
            serie = resp.json()
            tags = serie['MainDicomTags']
            instances = serie['Instances']
            if tags['Modality']=='RTDOSE':
                url = f'http://si-s-serv1041.st.chulg:8042/instances/{instances[0]}/content/3004,000a'
                resp = requests.get(url,auth=auth)
                if resp and resp.text=='PLAN':
                    assert len(instances)==1
                    urlRtDose = f'http://si-s-serv1041.st.chulg:8042/instances/{instances[0]}/file'
                    doseDate = tags['SeriesDate']
                    anonDoseDate = anonDate(doseDate)
                    patientDir = f'{workDir}/{patientId}/{studyName}/{nbRtDose}'
                    #TODO: add study prefix for anonymization !!! check that still match !!!
                    shaPatientId = anonString(patientId)
                    shaStudyName = anonString(studyName)
                    shaStudyID = anonString(studyID)
                    targetDir = f'{workDir}anon/{shaPatientId}/{shaStudyName}/{nbRtDose}'
                    print(f"Extracting patient {patientId}, study {studyName}, nbRtDose {nbRtDose}.")
                    os.makedirs(patientDir)
                    os.makedirs(targetDir)
                    resp = requests.get(urlRtStruct, auth=auth)
                    resp.raise_for_status()
                    with open(f'{patientDir}/rtstruct.dcm', 'wb') as f:
                        f.write(resp.content)
                    resp = requests.get(urlRtDose, auth=auth)
                    resp.raise_for_status()
                    with open(f'{patientDir}/rtdose.dcm', 'wb') as f:
                        f.write(resp.content)
                    structures = extract(patientDir, targetDir)
                    structureList = [i["name"] for i in structures]
                    structureNames = "|".join(structureList)
                    csvwriter.writerow({'numnat': patientId, 'studyDate': studyDate, 'doseDate': doseDate, 'studyId': studyID, 'studyName': studyName, 'nbStructures': len(structures), 'structures': structureNames, 'dirDvhs': f'{shaPatientId}/{shaStudyName}/{nbRtDose}' })
                    fcsv.flush()
                    anoncsvwriter.writerow({'numnat': shaPatientId, 'studyDate': anonStudyDate, 'doseDate': anonDoseDate, 'studyId': shaStudyID, 'studyName': shaStudyName,  'nbStructures': len(structures), 'structures': structureNames, 'dirDvhs': f'{shaPatientId}/{shaStudyName}/{nbRtDose}'})
                    fanoncsv.flush()
                    urlRtDose=None
                    nbRtDose = nbRtDose + 1 
        if nbRtDose==1:
            print(f"Missing RT Dose data for {patientId}, study {studyName}")
except HTTPError as http_err:
    logging.error('HTTP Error at %s', 'division', exc_info=http_err)
except Exception as err:
    logging.error('Other error occurred at %s', 'division', exc_info=err)
else:
    print('Success!')
finally:
    fcsv.close()
    fanoncsv.close()
