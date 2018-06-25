# -*- coding: UTF-8 -*-
import json
import oss2
import base64
import requests
from oss2 import compat

from aliyunsdkcore import client
from aliyunsdkvod.request.v20170321 import CreateUploadVideoRequest
from aliyunsdkvod.request.v20170321 import RefreshUploadVideoRequest
from aliyunsdkvod.request.v20170321 import CreateUploadImageRequest
from voduploadsdk.AliyunVodUtils import *
from voduploadsdk.UploadVideoRequest import UploadVideoRequest

VOD_MAX_TITLE_LENGTH = 128
VOD_MAX_DESCRIPTION_LENGTH = 1024

class AliyunVodUploader:
    
    def __init__(self, accessKeyId, accessKeySecret, ecsRegionId=None):
        """
        constructor for VodUpload
        :param accessKeyId: string, access key id
        :param accessKeySecret: string, access key secret
        :param ecsRegion: string, 部署迁移脚本的ECS所在的Region，详细参考：https://help.aliyun.com/document_detail/40654.html，如：cn-beijing
        :return
        """
        self.__accessKeyId = accessKeyId
        self.__accessKeySecret = accessKeySecret
        self.__ecsRegion = ecsRegionId
        self.__vodApiRegion = 'cn-shanghai'   # 点播服务所在的Region，国内为cn-shanghai
        self.__connTimeout = 10
        self.__bucketClient = None
        self.__maxRetryTimes = 3
        self.__vodClient = client.AcsClient(accessKeyId, accessKeySecret, self.__vodApiRegion, auto_retry=True, max_retry_time=3)
        
        # 分片上传参数
        self.__multipartThreshold = 10 * 1024 * 1024    # 分片上传的阈值，超过此值开启分片上传
        self.__multipartPartSize = 10 * 1024 * 1024     # 分片大小，单位byte
        self.__multipartThreadsNum = 1                  # 分片上传时并行上传的线程数，暂时为串行上传，不支持并行，后续会支持。
        
    def setMultipartUpload(self, multipartThreshold=10*1024*1024, multipartPartSize=10*1024*1024, multipartThreadsNum=1):
        if multipartThreshold > 0:
            self.__multipartThreshold = multipartThreshold
        if multipartPartSize > 0:
            self.__multipartPartSize = multipartPartSize
        if multipartThreadsNum > 0:
            self.__multipartThreadsNum = multipartThreadsNum
    
    @catch_error
    def uploadLocalVideo(self, uploadVideoRequest): 
        """
        分片上传本地文件到点播，最大支持48.8TB的单个文件，支持断点续传
        :param uploadVideoRequest: UploadVideoRequest类的实例，注意filePath为本地文件的绝对路径
        :return
        """
        #a = 1 if 5>3 else 0
        uploadInfo = self.__createUploadVideo(uploadVideoRequest)
        headers = self.__getUploadHeaders(uploadVideoRequest)
        self.__uploadOssObjectWithRetry(uploadVideoRequest.filePath, uploadInfo['UploadAddress']['FileName'], uploadInfo['UploadAuth'], 
                                             uploadInfo['UploadAddress'], uploadInfo['VideoId'], headers, 'multipart')
        return uploadInfo['VideoId']
    
    @catch_error    
    def uploadWebVideo(self, uploadVideoRequest):
        """
        上传网络文件到点播, 最大支持5GB的单个文件，不支持断点续传
        :param uploadVideoRequest: UploadVideoRequest类的实例，注意filePath为网络文件的URL地址
        :return
        """
        uploadInfo = self.__createUploadVideo(uploadVideoRequest)
        headers = self.__getUploadHeaders(uploadVideoRequest)
        self.__uploadOssObjectWithRetry(uploadVideoRequest.filePath, uploadInfo['UploadAddress']['FileName'], uploadInfo['UploadAuth'], 
                                             uploadInfo['UploadAddress'], uploadInfo['VideoId'], headers, 'web')
        return uploadInfo['VideoId']
    
    @catch_error   
    def uploadLocalM3u8(self, uploadVideoRequest):
        """
        上传m3u8本地文件及其分片文件到点播，分片文件和m3u8文件必须在同一目录
        :param uploadVideoRequest: UploadVideoRequest类的实例，注意filePath为本地m3u8文件的绝对路径
        :param sliceFileUrls: list, 分片文件的url，例如：['http://host/sample_001.ts', 'http://host/sample_002.ts']
        :return
        """
        # 获取分片文件路径
        sliceFiles = []
        tmpFilePath, fileName = AliyunVodUtils.getFileBriefPath(uploadVideoRequest.filePath)
        for line in open(uploadVideoRequest.filePath):  
            if line.startswith('#'):
                continue
            sliceFileName = line.strip()
            sliceFilePath = uploadVideoRequest.filePath.replace(fileName, sliceFileName)
            sliceFiles.append((sliceFilePath, sliceFileName))
        
        # 获取播放凭证
        uploadInfo = self.__createUploadVideo(uploadVideoRequest)
        videoId = uploadInfo['VideoId']
        uploadAddress = uploadInfo['UploadAddress']
        
        # 上传m3u8文件
        headers = self.__getUploadHeaders(uploadVideoRequest)
        self.__uploadOssObjectWithRetry(uploadVideoRequest.filePath, uploadAddress['FileName'], uploadInfo['UploadAuth'], 
                                             uploadAddress, videoId, headers, 'put')
        # 依次上传分片文件
        for sliceFile in sliceFiles:
            self.__uploadOssObjectWithRetry(sliceFile[0], uploadAddress['ObjectPrefix'] + sliceFile[1], uploadInfo['UploadAuth'], 
                                             uploadAddress, videoId, headers, 'put')
            
        return videoId
            
    @catch_error   
    def uploadWebM3u8(self, uploadVideoRequest, sliceFileUrls):
        """
        上传m3u8网络文件及其分片文件到点播，需要自己解析分片文件地址传入
        :param uploadVideoRequest: UploadVideoRequest类的实例，注意filePath为m3u8网络文件的URL地址
        :param sliceFileUrls: list, 分片文件的url，例如：['http://host/sample_001.ts', 'http://host/sample_002.ts']
        :return
        """
        # 获取播放凭证
        uploadInfo = self.__createUploadVideo(uploadVideoRequest)
        videoId = uploadInfo['VideoId']
        uploadAddress = uploadInfo['UploadAddress']
        
        # 上传m3u8文件
        headers = self.__getUploadHeaders(uploadVideoRequest)
        self.__uploadOssObjectWithRetry(uploadVideoRequest.filePath, uploadAddress['FileName'], uploadInfo['UploadAuth'], 
                                             uploadAddress, videoId, headers, 'web')
        # 依次上传分片文件
        for sliceFileUrl in sliceFileUrls:
            sliceFilePath, sliceFileName = AliyunVodUtils.getFileBriefPath(sliceFileUrl)
            self.__uploadOssObjectWithRetry(sliceFileUrl, uploadAddress['ObjectPrefix'] + sliceFileName, uploadInfo['UploadAuth'], 
                                             uploadAddress, videoId, headers, 'web')
            
        return videoId
                
    @catch_error
    def parseWebM3u8(self, m3u8FileUrl):
        """
        解析m3u8文件得到所有分片文件地址，原理是将m3u8地址前缀拼接ts分片名称作为后者的下载url，适用于url不带签名或分片与m3u8文件签名相同的情况
        :param m3u8FileUrl: string, m3u8网络文件url，例如：http://host/sample.m3u8
        :return sliceFileUrls
        """
        sliceFileUrls = []
        filePath, fileName = AliyunVodUtils.getFileBriefPath(m3u8FileUrl)
        res = requests.get(m3u8FileUrl)
        res.raise_for_status()
        for line in res.iter_lines():
            if line.startswith('#'):
                continue
            sliceFileUrl = m3u8FileUrl.replace(fileName, line.strip())
            sliceFileUrls.append(sliceFileUrl)
            
        return sliceFileUrls
    
    @catch_error
    def uploadImage(self, uploadImageRequest, isLocalFile=True): 
        """
        上传图片文件到点播，不支持断点续传；该接口可支持上传本地图片或网络图片
        :param uploadImageRequest: UploadImageRequest，注意filePath为本地文件的绝对路径或网络文件的URL地址
        :param isLocalFile: bool, 是否为本地文件。True：本地文件，False：网络文件
        :return
        """
        #a = 1 if 5>3 else 0
        uploadInfo = self.__createUploadImage(uploadImageRequest)
        uploadType = 'put' if isLocalFile else 'web'
        self.__uploadOssObject(uploadImageRequest.filePath, uploadInfo['UploadAddress']['FileName'], uploadInfo['UploadAuth'], 
                                             uploadInfo['UploadAddress'], uploadInfo['ImageId'], None, uploadType)
        return uploadInfo['ImageId'], uploadInfo['ImageURL']
    
    # 定义进度条回调函数；consumedBytes: 已经上传的数据量，totalBytes：总数据量
    def uploadProgressCallback(self, consumedBytes, totalBytes):
        return
    
        if totalBytes:
            rate = int(100 * (float(consumedBytes) / float(totalBytes)))
        else:
            rate = 0
              
        print ("uploaded %s, percent %s%s" % (consumedBytes, format(rate), '%'))
        sys.stdout.flush()
            
    # 获取视频上传地址和凭证
    def __createUploadVideo(self, uploadVideoRequest):
        request = CreateUploadVideoRequest.CreateUploadVideoRequest()
        
        title = AliyunVodUtils.subString(uploadVideoRequest.title, VOD_MAX_TITLE_LENGTH)
        request.set_Title(title)          # 视频标题(必填参数)
        request.set_FileName(uploadVideoRequest.fileName)   # 视频源文件名称，必须包含扩展名(必填参数)
    
        if uploadVideoRequest.description:
            description = AliyunVodUtils.subString(uploadVideoRequest.description, VOD_MAX_DESCRIPTION_LENGTH)
            request.set_Description(description)    # 视频源文件描述(可选)
        if uploadVideoRequest.coverURL:   # 自定义视频封面(可选)，不设置会默认取第一张截图作为封面
            request.set_CoverURL(uploadVideoRequest.coverURL)  
        if uploadVideoRequest.tags:
            request.set_Tags(uploadVideoRequest.tags)    # 视频标签，多个用逗号分隔(可选)
        if uploadVideoRequest.cateId:
            request.set_CateId(uploadVideoRequest.cateId) # 视频分类(可选，可以在点播控制台·全局设置·分类管理里查看分类ID：https://vod.console.aliyun.com/#/vod/settings/category)
        if uploadVideoRequest.templateGroupId:
                request.set_TemplateGroupId(uploadVideoRequest.templateGroupId)
      
        request.set_accept_format('JSON')
        result = json.loads(self.__vodClient.do_action_with_exception(request))
        result['UploadAddress'] = json.loads(base64.b64decode(result['UploadAddress']))
        result['UploadAuth'] = json.loads(base64.b64decode(result['UploadAuth']))
        
        logger.info("CreateUploadVideo, FilePath: %s, VideoId: %s" % (uploadVideoRequest.filePath, result['VideoId']))
        return result

    # 刷新上传凭证
    def __refresh_upload_video(self, videoId):
        request = RefreshUploadVideoRequest.RefreshUploadVideoRequest();
        request.set_VideoId(videoId);
        request.set_accept_format('JSON')
        result = json.loads(self.__vodClient.do_action_with_exception(request))
        result['UploadAddress'] = json.loads(base64.b64decode(result['UploadAddress']))
        result['UploadAuth'] = json.loads(base64.b64decode(result['UploadAuth']))
        
        logger.info("RefreshUploadVideo, VideoId %s" % (result['VideoId']))
        return result
    
    # 获取图片上传地址和凭证
    def __createUploadImage(self, uploadImageRequest):
        request = CreateUploadImageRequest.CreateUploadImageRequest()
        
        request.set_ImageType(uploadImageRequest.imageType)   # 图片用途(必填)
        request.set_ImageExt(uploadImageRequest.imageExt)      # 图片扩展名(可选，默认png)
        if uploadImageRequest.title:
            title = AliyunVodUtils.subString(uploadImageRequest.title, VOD_MAX_TITLE_LENGTH)
            request.set_Title(title)          # 图片标题(可选参数)
        if uploadImageRequest.tags:
            request.set_Tags(uploadImageRequest.tags)    # 图片标签，多个用逗号分隔(可选)
            
        request.set_accept_format('JSON')
        result = json.loads(self.__vodClient.do_action_with_exception(request))
        result['UploadAddress'] = json.loads(base64.b64decode(result['UploadAddress']))
        result['UploadAuth'] = json.loads(base64.b64decode(result['UploadAuth']))
        
        logger.info("CreateUploadImage, FilePath: %s, ImageId: %s, ImageUrl: %s" % (
            uploadImageRequest.filePath, result['ImageId'], result['ImageURL']))
        return result
    
    def __getUploadHeaders(self, uploadVideoRequest):
        if uploadVideoRequest.isShowWatermark is None:
            return None
        else:
            userData = "{\"Vod\":{\"UserData\":{\"IsShowWaterMark\": \"%s\"}}}" % (uploadVideoRequest.isShowWatermark)
            return {'x-oss-notification': base64.b64encode(userData, 'utf-8')}

    # uploadType，可选：multipart, put, web
    def __uploadOssObjectWithRetry(self, srcFilePath, destObject, uploadAuth, uploadAddress, videoId, headers, uploadType='multipart'):
        retryTimes = 0
        while retryTimes < self.__maxRetryTimes:
            try:
                return self.__uploadOssObject(srcFilePath, destObject, uploadAuth, uploadAddress, videoId, headers, uploadType)
            except OssError as e:
                # 上传凭证过期需要重新获取凭证
                if e.code == 'SecurityTokenExpired':
                    uploadInfo = self.__refresh_upload_video(videoId)
                    uploadAuth = uploadInfo['UploadAuth']
                    uploadAddress = uploadInfo['UploadAddress']
                    retryTimes += 1
            except Exception as e:
                raise e
            except:
                raise AliyunVodException('UnkownError', repr(e), traceback.format_exc())
            
        
    def __uploadOssObject(self, srcFilePath, destObject, uploadAuth, uploadAddress, videoId, headers, uploadType):
        self.__createOssClient(uploadAuth['AccessKeyId'], uploadAuth['AccessKeySecret'], uploadAuth['SecurityToken'], 
                                         uploadAddress['Endpoint'], uploadAddress['Bucket'])
        if uploadType == 'multipart':
            res = self.__resumableUpload(srcFilePath, destObject, videoId, headers)
        elif uploadType == 'put':
            res = self.__bucketClient.put_object_from_file(destObject , srcFilePath, headers=headers, progress_callback=self.uploadProgressCallback)
        elif uploadType == 'web':
            data = requests.get(srcFilePath)
            data.raise_for_status()
            res = self.__bucketClient.put_object(destObject, data, headers=headers, progress_callback=self.uploadProgressCallback)

        bucketHost = uploadAddress['Endpoint'].replace('://', '://' + uploadAddress['Bucket'] + ".")
        logger.info("UploadFile by %s, MediaId: %s, FilePath: %s, Destination: %s/%s" % (
            uploadType, videoId, srcFilePath, bucketHost, destObject))
        return res
        
    # 使用上传凭证和地址信息初始化OSS客户端（注意需要先Base64解码并Json Decode再传入）
    # 如果上传的ECS位于点播相同的存储区域（如上海），则可以指定internal为True，通过内网上传更快且免费
    def __createOssClient(self, accessKeyId, accessKeySecret, securityToken, endpoint, bucket):
        auth = oss2.StsAuth(accessKeyId, accessKeySecret, securityToken)
        endpoint = AliyunVodUtils.convertOssInternal(endpoint, self.__ecsRegion)
        self.__bucketClient = oss2.Bucket(auth, endpoint, bucket, connect_timeout=self.__connTimeout)
    
    def __resumableUpload(self, srcFilePath, destObject, videoId, headers):
        fileSize = os.path.getsize(srcFilePath)

        if fileSize >= self.__multipartThreshold:
            uploader = _VodResumableUploader(self.__bucketClient, destObject, srcFilePath, videoId, fileSize,
                                      self.__multipartPartSize, self.__multipartThreadsNum, headers, self.uploadProgressCallback)
            result = uploader.upload()
        else:
            with open(srcFilePath, 'rb') as f:
                result = self.__bucketClient.put_object(destObject, f, headers=headers, progress_callback=self.uploadProgressCallback)
    
        return result
    
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo
class _VodResumableUploader:
    def __init__(self, bucket, key, fileName, videoId, totalSize,
                 partSize, threadsNum, headers, progressCallback):
        self.__bucket = bucket
        self.__key = key
        self.__fileName = fileName
        self.__videoId = videoId
        self.__totalSize = totalSize
        self.__headers = headers
        self.__partSize = partSize
        self.__threadsNum = threadsNum
        self.__uploadId = None
        self.__mtime = os.path.getmtime(fileName)
        self.__progressCallback = progressCallback

        self.__record = {}
        self.__finishedSize = 0
        self.__finishedParts = []

    def upload(self):
        psize = oss2.determine_part_size(self.__totalSize, preferred_size=self.__partSize)
        
        # 初始化分片
        self.__uploadId = self.__bucket.init_multipart_upload(self.__key).upload_id

        # 逐个上传分片
        with open(AliyunVodUtils.toUnicode(self.__fileName), 'rb') as fileObj:
            partNumber = 1
            offset = 0
            while offset < self.__totalSize:
                uploadSize = min(psize, self.__totalSize - offset)
                logger.info("UploadPart, FilePath: %s, VideoId: %s, UploadId: %s, PartNumber: %s, PartSize: %s" % (self.__fileName, self.__videoId, self.__uploadId, partNumber, uploadSize))
                result = self.__bucket.upload_part(self.__key, self.__uploadId, partNumber, SizedFileAdapter(fileObj, uploadSize))
                self.__finishedParts.append(PartInfo(partNumber, result.etag))
                offset += uploadSize
                partNumber += 1
                
        # 完成分片上传
        self.__bucket.complete_multipart_upload(self.__key, self.__uploadId, self.__finishedParts, headers=self.__headers)
        
        return result