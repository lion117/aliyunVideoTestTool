# -*- coding: utf-8 -*-

import  json

from aliyunsdkcore import client
from aliyunsdkvod.request.v20170321 import GetVideoInfoRequest

import  AsyTask
import GVar
from  CsvWriter import  *
from voduploadsdk.AliyunVodUploader import AliyunVodUploader
from voduploadsdk.AliyunVodUtils import *
from voduploadsdk.UploadVideoRequest import UploadVideoRequest

gTaskMgr = AsyTask.ThreadPoolManger(10)
# gCsvWrite = CsvWriter("src")


def visitApiByUrl(tUrl):
    if tUrl is None:
        return None
    try:
        uploader = AliyunVodUploader(GVar.gAppId, GVar.gAppKey)
        uploadVideoRequest = UploadVideoRequest(tUrl,tUrl )
        uploadVideoRequest.setTags('kugou,test url')
        videoId = uploader.uploadWebVideo(uploadVideoRequest)
        print("file: %s, videoId: %s" % (uploadVideoRequest.filePath, videoId))
        return  videoId
    except AliyunVodException as e:
        print(e)
        return  None



def visitApiByFile(tFile):
    if tFile is None:
        return  None
    if isinstance(tFile , str ):
        raise  Exception("visitApiByFile require unicode type")
        return
    if os.path.exists(tFile) is False:
        print(u"not exist %s"%tFile)
        return
    if os.path.getsize(tFile) > GVar.gVideoSize:
        print u"文件大小超过限制:%d M   %s"%(os.path.getsize(tFile)/(1024*1024), tFile)
        return None
    try:
        uploader = AliyunVodUploader(GVar.gAppId, GVar.gAppKey)
        uploadVideoRequest = UploadVideoRequest(tFile, os.path.basename(tFile))
        uploadVideoRequest.setTags('kugou,test file')
        videoId = uploader.uploadLocalVideo(uploadVideoRequest)
        print("file: %s, videoId: %s" % (uploadVideoRequest.filePath, videoId))
        return  videoId
    except AliyunVodException as e:
        print(e)
        return None


def callBackFunc(*args):
    if len(args) != 2:
        print (u"call back error args len %d" % len(args))
        return
    lKey = args[0]
    lvalue = args[1]
    lMap = {}
    lMap[u"videoId"] = lvalue
    lMap[u"source"] = lKey
    lMap[u"date"] = time.strftime(u"%Y-%m-%d %H:%M:%S",time.localtime())
    GVar.gResult[lKey] = lMap
    if GVar.gCounts > 0:
        GVar.gIndex +=1
        print(u"完成文件提交:%s - %s 进度 %d / %d"%(lKey, lvalue,GVar.gIndex , GVar.gCounts))
    else:
        print (u"完成文件提交:%s - %s"%(lKey, lvalue))


def asyVisitApiByUrl(tUrl):
    if tUrl is None:
        return None
    gTaskMgr.addJob(visitApiByUrl,*(tUrl,callBackFunc))


def asyVisitApiByFile(tFile):
    if tFile is None:
        return
    if isinstance(tFile, str):
        raise Exception(u"visitApiByFile require unicode type")
        return
    if os.path.exists(tFile) is False:
        print(u"not exist %s" % tFile)
        return
    if os.path.getsize(tFile) > GVar.gVideoSize:
        print u"文件大小超过限制:%d M   %s" % (os.path.getsize(tFile) / (1024 * 1024), tFile)
        return
    gTaskMgr.addJob(visitApiByFile,*(tFile,callBackFunc))


def asyVisitApiByDir(tDir):
    pass





def initVodClient():
    regionId = 'cn-shanghai'   # 点播服务所在的Region，国内请填cn-shanghai，不要填写别的区域
    connectTimeout = 10        # 连接超时，单位：秒。连接失败默认会自动重试，且最多重试3次
    return client.AcsClient(GVar.gAppId, GVar.gAppKey, regionId, auto_retry=True, max_retry_time=3, timeout=connectTimeout)

gClient =  initVodClient()

def visitAliyunVideoInfo(videoId):
    request = GetVideoInfoRequest.GetVideoInfoRequest()
    request.set_accept_format('JSON')
    request.set_VideoId(videoId)
    request.set_ResultTypes("AI")
    response = json.loads(gClient.do_action(request))
    return response

def visitAliyunInfo(tFile):
    lList = FastCsvReader.read(tFile)
    if lList is None:
        print (u"无法从配置信息读取数据")
        return

    lDestList = []
    lLeftList = []
    lCounts = 0
    for itor in lList:
        if u"videoId" in itor:
            if itor[u"videoId"] == "videoId" or itor[u"videoId"]=="" :
                continue
            lObj =  visitAliyunVideoInfo(itor[u"videoId"])
            lLable , lScore ,lStrList = parseJson(lObj)
            itor.pop("hasResult",None)
            if lLable is not None:
                itor["catagory"] = lLable.encode("gbk")
                itor["score"] = lScore.encode("gbk")
                itor["cateList"] = lStrList.encode("gbk")
                itor["detail"] = unicode(lObj).encode("gbk")
                lDestList.append(itor)
                lCounts+=1
            else:
                itor["catagory"] = "error"
                itor["score"] = "error"
                itor["cateList"] = lScore
                itor["detail"] = unicode(lObj).encode("gbk")
                lDestList.append(itor)
    print (u"共获取%d个视频源, 有效获取%d个视频信息"%(len(lList), len(lDestList)))
    lBaseName= os.path.basename(tFile) + u"_result.csv"
    lFileName = os.path.join(os.path.dirname(tFile), lBaseName)
    FastCsvWriter.fastWrite(lDestList,lFileName)


def parseJson(tJson):
    if u"AI" not in tJson:
        print (u"not find the key ai")
        return (None, u"not find the key ai", None)
    lAiObj = tJson[u"AI"]

    lJsonAi = json.loads(lAiObj)
    if u"AIVideoCategory" not in lAiObj:
        print (u"not find the key AIVideoCategory")
        return (None, u"not find the key AIVideoCategory", None)

    lCategory = lJsonAi[u"AIVideoCategory"]
    if u"Categories" not in lCategory:
        print (u"not find the key Categories")
        return (None, u"not find the key Categories", None)
    lScore = u""
    lLable = u""
    if len(lCategory[u"Categories"]) > 0:
        for itor in lCategory[u"Categories"]:
            lScore = itor[u"score"]
            lLable = itor[u"label"]
            print lScore, lLable
    lRet = unicode(lCategory[u"Categories"])
    print lRet
    return (lLable, lScore, lRet)




class MainTest():
    @staticmethod
    def testSample():
        fileUrl = 'http://fx.v.kugou.com/G128/M00/06/05/YJQEAFpvIOqAcdIBAFc8tVk1mbE745.mp4'
        try:
            uploader = AliyunVodUploader("LTAIp0xwSxq9ECcj", "fCLa7U7vEjQB2J6xZJrTvzXk2NuwRR")
            uploadVideoRequest = UploadVideoRequest(fileUrl, 'test upload web video')
            # uploadVideoRequest.setTags('test1,test2')
            videoId = uploader.uploadWebVideo(uploadVideoRequest)
            print("file: %s, videoId: %s" % (uploadVideoRequest.filePath, videoId))
        except AliyunVodException as e:
            print(e)

    @staticmethod
    def testUrlMode():
        mediaUrl = u'http://fx.v.kugou.com/G128/M00/06/05/YJQEAFpvIOqAcdIBAFc8tVk1mbE745.mp4'
        reps = visitApiByUrl(mediaUrl)
        return reps

    @staticmethod
    def testFileMode():
        print (u"begin")
        mediaFile = os.path.join(os.getcwd().decode("gbk"), u'media/dance0_output_0.mp4')
        # mediaFile = os.path.join(os.getcwd(), 'media/dance0_output_0.mp4')
        reps = visitApiByFile(mediaFile)
        print (u"end")
        return reps

    @staticmethod
    def testAsyUrl():
        fileUrl = u'http://fx.v.kugou.com/G128/M00/06/05/YJQEAFpvIOqAcdIBAFc8tVk1mbE745.mp4'
        reps = asyVisitApiByUrl(fileUrl)
        return reps


    @staticmethod
    def testAsyFile():
        #lfile =  u"E:\KUGOU_CODE\OpenAi\src\demo\media\dance0_output_0.mp4"
        mediaFile = os.path.join(os.getcwd().decode("gbk"), u'media/dance0_output_0.mp4')
        reps = asyVisitApiByFile(mediaFile)
        return reps

    @staticmethod
    def testGetVideoInfo():
        lVideoId = u"9610ec06f6f348228f04d658f5f02abd"
        lret = visitAliyunVideoInfo(lVideoId)
        # print json.dumps(lret["AI"],indent=4)
        print lret[u"AI"]

    @staticmethod
    def testAliyunVideoInfo():
        visitAliyunInfo("")

    @staticmethod
    def testJson():
        lJson = {
            "1":12456,
            "2":124858,
            u"3":"3233",
            u"4":u"3232"
        }
        lJson.pop(u"1",None)
        lJson.pop("3")
        i = 0


if __name__ == "__main__":
    print os.getcwd()
    # MainTest.testUrlMode()
    # MainTest.testFileMode()
    # MainTest.testSample()
    # MainTest.testAsyUrl()
    # MainTest.testAsyFile()
    # MainTest.testGetVideoInfo()
    # MainTest.testAliyunVideoInfo()
    # gTaskMgr.waitDone()
    MainTest.testJson()
