# RailwayAI - DeepSeek-V4 网页AI智能助手
## 项目简介
本项目是轻量化网页端AI对话工具，Python+Streamlit搭建可视化交互页面，核心接入DeepSeek-V4系列大模型API，无需前端开发基础，一行命令启动本地网页。


## 核心功能
1. 百万上下文记忆：完整留存超长对话，长文档、多轮连续问答不丢失上下文
2. 音频语音交互：可语音朗读回复，
3. 对话持久缓存：自动保存会话记录，重启程序历史聊天不丢失
4. 轻量化网页部署：仅依赖Python环境，自带完整依赖清单，一键安装库
6. 模型参数自定义：侧边栏可以选择历史对话，ai助手的名字和身份

## 技术栈
- 编程语言：Python 3.13
- 网页框架：Streamlit
- 大模型接口：DeepSeek-V4 

## 本地快速运行教程
### 1. 安装全部依赖
终端进入项目根目录执行：
pip install -r requirements.txt

## 功能截图预览
### 1. 主对话页面
![程序首页主界面](screenshot of operation/main_page.png)


### 2. 安装全部依赖
填入你的 DeepSeek 个人 API Key，无需额外配置文件。

###3.启动ai助手
终端进入项目根目录执行：
streamlit run 1/03.ai_partner_main.py

## 页面展示
程序首页主界面(screenshot of operation/1.png)
设置AI名字和语气(screenshot of operation/2.png)
