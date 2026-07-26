import streamlit as st
import os
from openai import OpenAI

# 设置页面的配置项
st.set_page_config(
    page_title="铁路信息咨询AI助手",
    page_icon="🚂",
    layout="wide", # 布局
    initial_sidebar_state="expanded", # 控制的是侧边栏的状态
    menu_items={}
)

# 大标题
st.title("铁路信息咨询AI助手")

# Logo
st.logo("resources/logo.png")

# 系统提示词
system_prompt = """
        你叫 %s，是专业的铁路信息咨询AI助手。
        规则：
            1. 只回答铁路相关问题
            2. 回答准确、清晰、简洁
            3. 匹配用户的语言
            4. 可以根据设定语气组织表达
            5. 对于购票、改签、退票、车站、列车、路线等问题优先提供实用信息
        回答语气：
            - %s
        如果问题与铁路无关，请礼貌引导用户咨询铁路相关内容。
    """

# 初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []
# 昵称
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小铁"
# 性格
if "nature" not in st.session_state:
    st.session_state.nature = "专业严谨的铁路客服"

# 展示聊天信息
for message in st.session_state.messages: # {"role": "user", "content": prompt}
    st.chat_message(message["role"]).write(message["content"])

# 创建与AI大模型交互的客户端对象 (DEEPSEEK_API_KEY 环境变量的名字, 值就是DeepSeek的API_KEY的)
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

# 左侧的侧边栏 - with: streamlit中上下文管理器
with st.sidebar:
    st.subheader("助手设置")
    # 昵称输入框
    nick_name = st.text_input("助手名称", placeholder="请输入助手名称", value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name

    # 性格输入框
    nature = st.text_area("回答语气", placeholder="请输入回答语气", value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature

# 消息输入框
prompt = st.chat_input("请输入您要咨询的铁路相关问题")
if prompt: # 字符串会自动转换为布尔值, 如果字符串非空, 则为True; ""否则为False
    st.chat_message("user").write(prompt)
    print("----------> 调用AI大模型, 提示词: ", prompt)
    # 保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用AI大模型
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True
    )

    # 输出大模型返回的结果 (流式输出的解析方式)
    response_message = st.empty() # 创建一个空的组件, 用于展示大模型返回的结果

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    # 保存大模型返回的结果
    st.session_state.messages.append({"role": "assistant", "content": full_response})
