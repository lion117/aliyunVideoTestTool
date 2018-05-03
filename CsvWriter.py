# -*- coding: utf-8 -*-

import sys, os, time
import datetime
import  csv


gSrcTitle = ["source", "date",  "videoId"]
gDestTitle = ["source", "date",  "videoId","catagory","score","cateList","detail"]


def GetCsvFileName():
    today = time.strftime("%Y-%m-%d")
    lFileName = str.format("Video_Analyze_%s_Result.csv"%(today))
    return  lFileName



def GetFileName(tMark):
    if tMark is None:
        tMark = "result"
    today = time.strftime("%Y-%m-%d")
    lFileName = str.format("Video_Analyze_%s_%s.csv"%(today,tMark))
    return  lFileName

class CsvWriter():
    # _csvFile = os.path.join(os.getcwd(),GetCsvFileName() )
    _csvFile = GetCsvFileName()
    _filehandle = None
    _writer = None
    def __init__(self, tMark):
        self._csvFile = GetFileName(tMark)
        if os.path.exists(self._csvFile):
            self._filehandle = open(self._csvFile,"ab")
        else:
            self._filehandle = open(self._csvFile,"wb")
            self._writer = csv.writer(self._filehandle)
            self._writer.writerow(gSrcTitle)

    def writeData(self, tDict):
        if self._writer is None:
            self._writer = csv.writer(self._filehandle)
        lList = []
        lList.append(tDict["source"])
        if "date" in tDict:
            lList.append(tDict["date"])
        else:
            lList.append(time.strftime("%Y-%m-%d %H:%M:%S"))
        lList.append(tDict["videoId"])
        self._writer.writerow(lList)
        self._filehandle.flush()


    def writeBatch(self, tList):
        if self._filehandle:
            lwrite = csv.DictWriter(self._filehandle)
            lwrite.writerows(tList)
            self._filehandle.flush()


    def close(self):
        if self._filehandle :
            self._filehandle.close()

class FastCsvWriter():
    @staticmethod
    def write(tList):
        lFileName = GetFileName("dest")
        with open(lFileName,"wb+") as lhanle:
            lwrite = csv.DictWriter(lhanle,gDestTitle)
            lwrite.writeheader()
            lwrite.writerows(tList)

    @staticmethod
    def fastWrite(tList,tFile):
        with open(tFile, "wb+") as lhanle:
            lwrite = csv.DictWriter(lhanle, gDestTitle)
            lwrite.writeheader()
            lwrite.writerows(tList)

class FastCsvReader():
    @staticmethod
    def read(tFile):
        lList = []
        if os.path.exists(tFile) is False:
            print (u"could not find file %s"%tFile)
            return  lList
        with open(tFile) as fhandle:
            reader = csv.DictReader(fhandle, gSrcTitle)
            for itor in reader:
                lList.append(itor)
        return lList


class CsvRead():
    # _csvFile = os.path.join(os.getcwd(),GetCsvFileName() )
    def __init__(self,tMark):
        self._csvFile = GetFileName(tMark)
        pass

    def readData(self):
        lList = []
        with open(self._csvFile) as fhandle:
            reader = csv.DictReader(fhandle,gSrcTitle)
            for itor in reader:
                lList.append(itor)
        return lList




class TestMain():
    @staticmethod
    def testWriter():
        lcsv = CsvWriter("test")
        lDict = {"source": "http://baidu.com", "videoId": "dance"}
        for _ in range(10):
            lcsv.writeData(lDict)
        lcsv.close()

    @staticmethod
    def testReader():
        lcsv = CsvRead("src")
        print lcsv.readData()


if __name__ == "__main__":
    print os.getcwd()
    # TestMain.testWriter()
    TestMain.testReader()