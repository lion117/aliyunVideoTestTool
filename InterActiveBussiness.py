# -*- coding: utf-8 -*-

import GVar
import SyUtil
import VideoVistor
from CsvWriter import  *

g_urlInfo = u'''请输入视频url地址：
举例：example.com/demo.mp4
'''

g_fileInfo = u'''请输入视频文件地址：
举例：c:\demo.mp4
'''

g_dirInfo = u'''请输入视频所在文件夹地址：
举例 c:\demo
'''

g_videoInfo = u'''请输入解析文件名：
例如：Video_Analyze_2018-05-03_15-16-02.csv
'''

g_urlListInfo = u'''提示：请先配置urlcfj.json文件后再使用当前模式
举例：["http://fx.v.kugou.com/G128/M00/06/05/YJQEAFpvIOqAcdIBAFc8tVk1mbE745.mp4"]
'''

def runByUrl():
    print(g_urlInfo)
    lUrl = raw_input().decode(sys.stdin.encoding)
    lUrl = lUrl.strip()
    GVar.gResult = {}
    GVar.gCounts = 0
    GVar.gIndex = 0
    lCsv = CsvWriter("src")
    VideoVistor.asyVisitApiByUrl(lUrl)
    VideoVistor.gTaskMgr.waitDone()
    for itor in GVar.gResult:
        lCsv.writeData(GVar.gResult[itor])
    lCsv.close()


def runByFile():
    print (g_fileInfo)
    lFileUrl = raw_input().decode(sys.stdin.encoding)
    GVar.gResult = {}
    GVar.gCounts = 0
    GVar.gIndex = 0
    lCsv = CsvWriter("src")
    VideoVistor.asyVisitApiByFile(lFileUrl)
    VideoVistor.gTaskMgr.waitDone()
    for itor in GVar.gResult:
        lCsv.writeData(GVar.gResult[itor])
    lCsv.close()

def runByDir():
    print (g_dirInfo)
    lvalue = raw_input().decode(sys.stdin.encoding)

    if os.path.exists(lvalue) is False:
        print u"指定路径不存在:%s" % lvalue
        return
    lList = SyUtil.walkPath(lvalue)
    if len(lList) == 0:
        print u"指定目录下没有发现mp4或flv文件"
        return
    else:
        print u"共发现%d个视频文件." % len(lList)
    GVar.gResult = {}
    GVar.gCounts = len(lList)
    GVar.gIndex = 0
    lCsv = CsvWriter(time.strftime("%H-%M-%S"))
    for itor in lList:
        print u"开始分析视频文件: %s" % itor
        VideoVistor.asyVisitApiByFile(itor)
    VideoVistor.gTaskMgr.waitDone()
    for itor in GVar.gResult:
        lCsv.writeData(GVar.gResult[itor])
    lCsv.close()

def runByVideoTag():
    print (g_videoInfo)
    lvalue = raw_input().decode(sys.stdin.encoding)

    if os.path.exists(lvalue) is False:
        print u"指定路径不存在:%s" % lvalue
        return
    VideoVistor.visitAliyunInfo(lvalue)

# def runByUrlList():
#     print (g_urlListInfo)
#     lFileName =os.path.join(os.getcwd().decode("gbk"), u"urlcfg.json")
#     if os.path.exists(lFileName) is False:
#         with open(lFileName,"w") as handle:
#             handle.write(u"[]")
#             print u"url配置文件为空, 请配置参数后再重试"
#             return
#     with open(lFileName,"rb") as handle:
#         buff = handle.read()
#         videoAnalyzer.analyzeByJson(buff.decode("gbk"))


def TestJson():
    lList = '["http://fx.v.kugou.com/G128/M00/06/05/YJQEAFpvIOqAcdIBAFc8tVk1mbE745.mp4"]'
    import  json
    ljson =json.loads(lList)
    print ljson


if __name__ == "__main__":
    print os.getcwd()
    # runByUrlList()
    # TestJson()