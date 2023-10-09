from asyncio.windows_events import NULL
import os
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from extractdvh import extract
import csv
import hashlib
from datetime import date, datetime

def anonDate(dt):
    anonDate = datetime.strptime(dt, '%Y%m%d')
    anonDate = date(anonDate.year, anonDate.month, 1)
    return datetime.strftime(anonDate, '%Y%m%d')


workDir = 'c:/workspace/trumpet/data/hnc'
fcsv = open(f'{workDir}/dvhs.csv', 'w', newline='')
csvwriter = csv.DictWriter(fcsv, delimiter=',', dialect='excel', fieldnames=['numnat', 'studyDate', 'doseDate', 'studyId', 'nbStructures', 'structures', 'dirDvhs'])
csvwriter.writeheader()
fanoncsv = open(f'{workDir}anon/dvhs.csv', 'w', newline='')
anoncsvwriter = csv.DictWriter(fanoncsv, delimiter=',', dialect='excel', fieldnames=['numnat', 'studyDate', 'doseDate', 'studyId', 'nbStructures', 'structures', 'dirDvhs'])
anoncsvwriter.writeheader()
auth = HTTPBasicAuth('orthanc', 'orthanc')
url = "http://si-s-serv1041.st.chulg:8042/studies"
try:
    resp = requests.get(url,auth=auth)
    resp.raise_for_status()
    studies = resp.json()
    for studyName in studies:
        url = f'http://si-s-serv1041.st.chulg:8042/studies/{studyName}'
        resp = requests.get(url, auth=auth)
        resp.raise_for_status()
        study = resp.json()
        urlRtDose = None
        urlRtStruct = None
        patientId = study['PatientMainDicomTags']['PatientID']
        studyDate = study['MainDicomTags']['StudyDate']
        anonStudyDate = anonDate(studyDate)
        studyId = study['MainDicomTags']['StudyID']
        for serieName in study['Series']:
            url = f'http://si-s-serv1041.st.chulg:8042/series/{serieName}'
            resp = requests.get(url,auth=auth)
            resp.raise_for_status()
            serie = resp.json()
            tags = serie['MainDicomTags']
            doseDate = tags['SeriesDate']
            anonDoseDate = anonDate(doseDate)
            instances = serie['Instances']
            if tags['Modality']=='RTSTRUCT':
                assert len(instances)==1
                urlRtStruct = f'http://si-s-serv1041.st.chulg:8042/instances/{instances[0]}/file'
            if tags['Modality']=='RTDOSE':
                url = f'http://si-s-serv1041.st.chulg:8042/instances/{instances[0]}/content/3004,000a'
                resp = requests.get(url,auth=auth)
                if resp and resp.text=='PLAN':
                    assert len(instances)==1
                    urlRtDose = f'http://si-s-serv1041.st.chulg:8042/instances/{instances[0]}/file'
        if urlRtDose!=None and urlRtStruct!=None:
            patientDir = f'{workDir}/{patientId}/{studyId}'
            shaPatientId = 'CHUL' + hashlib.sha256(patientDir.encode('utf-8')).hexdigest()
            shaStudyId = 'CHUL' + hashlib.sha256(studyId.encode('utf-8')).hexdigest()
            targetDir = f'{workDir}anon/{shaPatientId}/{shaStudyId}'
            print(f"Extracting patient {patientId}, study {studyId}")
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
            csvwriter.writerow({'numnat': patientId, 'studyDate': studyDate, 'doseDate': doseDate, 'studyId': studyId, 'nbStructures': len(structures), 'structures': structureNames, 'dirDvhs': f'{shaPatientId}/{shaStudyId}' })
            fcsv.flush()
            anoncsvwriter.writerow({'numnat': patientId, 'studyDate': anonStudyDate, 'doseDate': anonDoseDate, 'studyId': studyId, 'nbStructures': len(structures), 'structures': structureNames, 'dirDvhs': f'{shaPatientId}/{shaStudyId}'})
            fanoncsv.flush()
        else:
            print(f"Missing data for {patientId}, study {studyId}")
except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}') 
except Exception as err:
    print(f'Other error occurred: {err}')  
else:
    print('Success!')
finally:
    fcsv.close()
    fanoncsv.close()

