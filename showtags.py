from pydicom import dcmread

basedir = "C:/workspace/TRUMPET/data/RayStation/3679196L"
ds = dcmread(basedir + "/RS.dcm")
for element in ds:
    print(element)
print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
ds = dcmread(basedir + "/RD.dcm")
for element in ds:
    print(element)