# -*- coding: utf-8 -*-



import os, sys
import time
import  InterActiveBussiness


g_titleInfo = u'''
----------测试工具---------
------请选择当前测试模式-----
1:指定视频文件夹上传  2:获取视频分类信息
q:退出
>'''



def UserInterActivate():
    while (True):
        print(g_titleInfo),
        iIndex = raw_input()
        if iIndex == '1':
            InterActiveBussiness.runByDir()
        elif iIndex == '2':
            InterActiveBussiness.runByVideoTag()
        # elif iIndex == '3':
        #     InterActiveBussiness.runByDir()
        # elif iIndex == '4':
        #     InterActiveBussiness.runByVideoTag()
        elif iIndex == "q":
            break
        else:
            print(u"输入参数不正确,请输入[1-2之内的数值]")
        print ""

def Run():
    if __debug__:
        UserInterActivate()
    else:
        try:
            UserInterActivate()
        except Exception, ex:
            print ex
            print u"按回车键继续"
            raw_input()



if __name__ == "__main__":
    Run()