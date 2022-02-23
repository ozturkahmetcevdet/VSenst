uOTALoop = True
uOTAFileName = ""
uf = None
def GetFileName(data):
    global uOTAFileName
    global uf
    IsFileNameExist = False
    splitData = data.decode('utf-8').split('@')
    for item in splitData:
        if item == "FName":
            IsFileNameExist = True
        elif IsFileNameExist:
            uOTAFileName = item
            try:
                uf = open(uOTAFileName, 'w')
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not open file. ---{}".format(uOTAFileName))
            except:
                print("Unexpected error!")
                raise

def IsFileReadFinish(data):
    return data == b'uOTA end\r\n'

def ReadAndSaveFile(data):
    global uOTALoop
    global uOTAFileName
    global uf
    if data != None:
        if uOTAFileName == "":
            GetFileName(data)
        elif uOTAFileName != "":
            if IsFileReadFinish(data):
                uf.close()
                uOTALoop = False
            else:
                uf.write(data.decode('utf-8'))
    