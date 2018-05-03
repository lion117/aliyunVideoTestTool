# 测试工具

## 依赖
- python 2.7
- aliyun-python-sdk-core
- aliyun-python-sdk-vod

# 安装方法
```
#安装SDK
pip install aliyun-python-sdk-core
pip install aliyun-python-sdk-vod

pip install --upgrade aliyun-python-sdk-vod

# 卸载SDK 通过pip卸载：
pip uninstall aliyun-python-sdk-core
pip uninstall aliyun-python-sdk-vod
```


# 运行
- 直接运行 run.py
- 通过make.bat生成exe文件运行 （需要依赖pyinstaller）

# 配置关键信息
必须配置Gvar.py里面的参数后, 才能正确上传和分析
```
gAppId = '请输入您的appid'
gAppKey = '请输入您的appkey'
```

# 软件运行流程
1. 指定上传视频文件目录（仅支持mp4和flv上传, 限制大小为10M）
2. 上传视频文件到阿里云服务器
3. 记录videoid到csv文件
4. 上传视频文件完成后,等待约5分钟
5. 指定刚刚生成的csv文件,获取视频文件信息, 完成后将自动生成一个新的csv结果文件