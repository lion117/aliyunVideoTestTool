# -*- coding: UTF-8 -*-
from voduploadsdk.AliyunVodUtils import *

class UploadVideoRequest:
    """
    VOD上传视频的请求类，请求参数和返回字段可参考：https://help.aliyun.com/document_detail/55407.html
    """
    def __init__(self, filePath, title=None):
        """
        constructor for UploadVideoRequest
        :param filePath: string, 文件的绝对路径，或者网络文件的URL，必须含有扩展名
        :param title: string, 视频标题，最长128字节，不传则使用文件名为标题
        :return
        """
        extName = AliyunVodUtils.getFileExtension(filePath)
        if not extName:
            raise AliyunVodException('ParameterError', 'InvalidParameter', 'filePath has no Extension')
        self.filePath = AliyunVodUtils.toUnicode(filePath)
        
        briefPath, briefName = AliyunVodUtils.getFileBriefPath(filePath)
        self.fileName = briefPath   # 获取上传地址和凭证的接口需要过滤文件URL的?及后面的参数
        if title:
            self.title = title
        else:
            self.title = briefName
        
        self.cateId = None
        self.tags = None
        self.description = None
        self.coverURL = None
        self.templateGroupId = None
        self.isShowWatermark = None
        
    # 设置视频分类ID
    def setCateId(self, cateId):
        self.cateId = cateId  
    
    # 视频标签,多个用逗号分隔
    def setTags(self, tags):
        self.tags = tags
        
    # 视频描述，最长1024字节
    def setDescription(self, description):
        self.description = description       
    
    # 视频自定义封面URL                    
    def setCoverURL(self, coverURL):
        self.coverURL = coverURL
        
    # 设置模板组ID
    def setTemplateGroupId(self, templateGroupId):
        self.templateGroupId = templateGroupId
        
    # 关闭水印，仅用于配置全局水印且转码模板开启水印后，单次上传时关闭水印   
    def shutdownWatermark(self):
        self.isShowWatermark = False
    