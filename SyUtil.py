# -*- coding: utf-8 -*-

import sys, os, time

def walkPath(tDir):
    lItemList = []
    for (dirpath, dirnames, filenames) in os.walk(tDir):
            for itor in filenames:
                if itor.find(u".mp4") != -1 or itor.find(u".flv") != -1:
                    if tDir == dirpath:
                        lItemList.append(os.path.join(tDir, itor))
    return lItemList




if __name__ == "__main__":
    print os.getcwd()