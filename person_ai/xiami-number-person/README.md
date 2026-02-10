# 数字人

![演示](h5.gif)

## 设置

[application.yml](src/main/resources/application.yml)
> 项目中使用的是[百度AI开放平台](https://ai.baidu.com/)与[阿里云](https://www.aliyun.com)的语音交互与对话服务，需要申请对应的百度[AK/SK](https://ai.baidu.com/ai-doc/REFERENCE/Ck3dwjhhu)、阿里[AccessKey](https://help.aliyun.com/zh/isi/getting-started/start-here?spm=a2c4g.11186623.help-menu-30413.d_1_0.365dffd9eqpBH4&scm=20140722.H_72138._.OR_help-T_cn~zh-V_1)。
```
human:
  baidu:
    api-key: ********************************
    secret-key: ********************************
  aliyun:
    access-key-id: ********************************
    access-key-secret: ********************************
```
> 项目中包含一个通用的对话接口,您可以使用所有厂家符合OpenAI接口规范的产品，如：[百度千帆大模型](https://cloud.baidu.com/product-s/qianfan_home)、[阿里云百炼模型](https://bailian.console.aliyun.com)、[DeepSeek](https://api-docs.deepseek.com/zh-cn/)等。
```
human:
  chat:
    api-key: ********************************
    base-url: https://api.deepseek.com/v1
    models:
      - title: DeepSeek-V3
        value: deepseek-chat
      - title: DeepSeek-R1
        value: deepseek-reasoner
```
> 在网页使用麦克风录音时需使用HTTPS安全协议。
> 项目自带一个测试用的证书，您在使用中可以替换成您的证书或关闭server.ssl.enabled=false使用Nginx代理。
```
server:
  ssl:
    enabled: true
    key-store: classpath:keystore.jks
    key-store-password: 123456
```
### 场景

[human.js](src/main/resources/static/human/human.js)  
```
scene: [
    {title: '场景1', value: 'human/background/bg_1.png'},
    {title: '场景2', value: 'human/background/bg_2.png'},
    {title: '场景3', value: 'human/background/bg_3.png'},
    {title: '场景4', value: 'human/background/bg_4.png'},
    {title: '场景5', value: 'human/background/bg_5.png'},
    {title: '场景6', value: 'human/background/bg_6.png'},
    {title: '场景7', value: 'human/background/bg_7.png'}
]
```

### 形象

[human.js](src/main/resources/static/human/human.js)  
> 形象分为存放数字人待机时的图片动画[standby](src/main/resources/static/human/xiaochuan/standby)目录，数字人说话时的图片动画[speak](src/main/resources/static/human/xiaochuan/speak)目录，数字人的头像图片[me.png](src/main/resources/static/human/xiaochuan/me.png)。
```
//名称、位置、待机帧数与间隔、说话帧数与间隔
human: [
    {
        title: '小川', value: 'human/xiaochuan',
        standby: {frame: 113, interval: 20},
        speak: {frame: 186, interval: 30}
    },
    {
        title: '关关', value: 'human/guanguan',
        standby: {frame: 152, interval: 80},
        speak: {frame: 114, interval: 60}
    }
]
```

### 音库

【百度】[音色列表](https://ai.baidu.com/ai-doc/SPEECH/Rluv3uq3d)（注：[baidu.tts.js](src/main/resources/static/human/baidu.tts.js)）  
【阿里】[音色列表](https://help.aliyun.com/zh/isi/developer-reference/overview-of-speech-synthesis?spm=a2c4g.11186623.help-menu-30413.d_3_1_0_0.26ff3c84Kc9rS3#5186fe1abb7ag)（注：[aliyun.tts.js](src/main/resources/static/human/aliyun.tts.js)）

## 语音识别

【百度】[语音识别极速版](https://ai.baidu.com/ai-doc/SPEECH/4lbxdz34z)  
【阿里】[一句话识别](https://help.aliyun.com/zh/isi/developer-reference/restful-api-2)  

## 语音合成

【百度】[流式文本在线合成](https://ai.baidu.com/ai-doc/SPEECH/lm5xd63rn)  
【阿里】[流式文本语音合成](https://help.aliyun.com/zh/isi/developer-reference/streaming-text-tts-wss)  

## 对话Chat

[百度千帆大模型](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Fm2vrveyu)  
[阿里云百炼模型](https://bailian.console.aliyun.com)  
[DeepSeek](https://api-docs.deepseek.com/zh-cn/guides/multi_round_chat)  

## 语音交互与对话服务申请步骤

### 百度

1、注册[百度AI开放平台](https://ai.baidu.com/)账户并完成实名认证。  
2、创建[语音技术应用列表](https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list)获取“API Key”与“Secret Key”（注：[application.yml](src/main/resources/application.yml)中的“api-key”与“secret-key”）。  
3、申请[流式文本在线合成](https://ai.baidu.com/ai-doc/SPEECH/lm5xd63rn)试用（注：“流式文本在线合成”处于邀测阶段，需要申请试用）。  
4、开通[百度千帆大模型](https://console.bce.baidu.com/qianfan/ais/console/onlineService)。  
5、创建[API Key](https://console.bce.baidu.com/iam/#/iam/apikey/list)（注：[application.yml](src/main/resources/application.yml)中的“api-key”与“base-url=<https://qianfan.baidubce.com/v2>”）。  
6、支持的[模型列表](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Fm2vrveyu)（注：[application.yml](src/main/resources/application.yml)中的“models”）。  

### 阿里

1、注册[阿里云](https://www.aliyun.com/)账户并完成实名认证。  
2、创建[AccessKey](https://ram.console.aliyun.com/profile/access-keys)获取“AccessKey ID”与“AccessKey Secret”（注：[application.yml](src/main/resources/application.yml)中的“access-key-id”与“access-key-secret”）。  
3、开通[智能语音交互](https://ai.aliyun.com/nls)（注：“流式文本语音合成”没有免费试用）。  
4、创建[智能语音交互项目](https://nls-portal.console.aliyun.com/applist)获取“Appkey”（注：[aliyun.asr.js](src/main/resources/static/human/aliyun.asr.js)与[aliyun.tts.js](src/main/resources/static/human/aliyun.tts.js)中的“app_key”）。  
5、开通[阿里云百炼模型](https://bailian.console.aliyun.com/?tab=model#/model-market)。  
6、创建[API-Key](https://bailian.console.aliyun.com/?tab=model#/api-key)（注：[application.yml](src/main/resources/application.yml)中的“api-key”与“base-url=<https://dashscope.aliyuncs.com/compatible-mode/v1>”）。  
7、支持的[模型列表](https://bailian.console.aliyun.com/?tab=doc#/doc/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2840914.html)（注：[application.yml](src/main/resources/application.yml)中的“models”）。