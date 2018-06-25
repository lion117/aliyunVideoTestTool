# -*- coding: UTF-8 -*-
from voduploadsdk.AliyunVodUtils import *

class UploadImageRequest:
    """
    VOD上传图片的请求类，请求参数和返回字段可参考：https://help.aliyun.com/document_detail/55619.html
    """
    def __init__(self, filePath):
        """
        constructor for UploadVideoRequest
        :param filePath: string, 文件的绝对路径，或者网络文件的URL，必须含有扩展名
        :return
        """
        extName = AliyunVodUtils.getFileExtension(filePath)
        if not extName:
            raise AliyunVodException('ParameterError', 'InvalidParameter', 'filePath has no Extension')
        self.filePath = AliyunVodUtils.toUnicode(filePath)
        self.imageExt = extName
        self.imageType = 'default'
        self.title = None    
        self.tags = None
        
    # 设置图片类型，可选值：default(默认)、cover(封面)、watermark(水印)
    def setImageType(self, imageType):
        self.imageType = imageType 
    
    # 设置图片标题，长度不超过128个字节，UTF8编码
    def setTitle(self, title):
        self.title = title
        
    # 设置图片标签，单个标签不超过32字节，最多不超过16个标签，多个用逗号分隔，UTF8编码
    def setTags(self, tags):
        self.tags = tags
    