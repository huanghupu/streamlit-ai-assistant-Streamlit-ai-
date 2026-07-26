import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json
from gtts import gTTS
import base64
import urllib.request

# 设置页面的配置项
st.set_page_config(
    page_title="铁路信息咨询AI助手",
    page_icon="🚂",
    layout="wide", # 布局
    initial_sidebar_state="expanded", # 控制的是侧边栏的状态
    menu_items={}
)


def get_img_as_base64(file_path):
    """将图片文件转为 base64 编码"""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# 设置聊天界面背景图
bg_img_path = "image/2.png"
if os.path.exists(bg_img_path):
    bin_str = get_img_as_base64(bg_img_path)
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    /* 让聊天消息气泡半透明，便于背景图显示 */
    div[data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.01) !important;
        backdrop-filter: blur(4px);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 8px;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# 生成会话标识函数
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def report_debug_event(hypothesis_id, msg, data=None, location="08_ai_partner_6.py"):
    # #region debug-point common:report-helper
    try:
        debug_server_url = "http://127.0.0.1:7777/event"
        debug_session_id = "voice-playback-bug"
        if os.path.exists(".dbg/voice-playback-bug.env"):
            with open(".dbg/voice-playback-bug.env", "r", encoding="utf-8") as env_file:
                for line in env_file:
                    line = line.strip()
                    if line.startswith("DEBUG_SERVER_URL="):
                        debug_server_url = line.split("=", 1)[1]
                    elif line.startswith("DEBUG_SESSION_ID="):
                        debug_session_id = line.split("=", 1)[1]
        payload = {
            "sessionId": debug_session_id,
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id,
            "location": location,
            "msg": f"[DEBUG] {msg}",
            "data": data or {},
            "ts": int(datetime.now().timestamp() * 1000),
        }
        request = urllib.request.Request(
            debug_server_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(request, timeout=1).read()
    except Exception:
        pass
    # #endregion

# 保存会话信息函数
def save_session():
    if st.session_state.current_session:
        # 构建新的会话对象
        session_data = {
            "assistant_name": st.session_state.assistant_name,
            "tone": st.session_state.tone,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        # 如果 sessions 目录不存在, 则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        # 保存会话数据
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

# 加载所有的会话列表信息
def load_sessions():
    session_list = []
    # 加载sessions目录下的文件
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True) # 排序, 降序排列
    return session_list

# 加载指定的会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            # 读取会话数据
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.assistant_name = session_data["assistant_name"]
                st.session_state.tone = session_data["tone"]
                st.session_state.current_session = session_name
    except Exception:
        st.error("加载会话失败!")

# 删除会话信息函数
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json") # 删除文件
            # 如果删除的是当前会话, 则需要更新消息列表
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error("删除会话失败!")


# 大标题
st.title("铁路信息咨询AI助手")

# 系统提示词
system_prompt = """
        你叫 %s，是专业的铁路信息咨询助手。请以专业、热情的态度为用户提供铁路相关信息咨询服务。
        服务范围：
            1. 列车时刻表查询
            2. 车票价格咨询
            3. 铁路线路规划
            4. 车站信息介绍
            5. 购票流程指导
            6. 行李托运规定
            7. 改签退票政策
            8. 铁路安全常识
            9. 高铁动车相关知识
            10. 其他铁路相关问题解答
        规则：
            1. 只回答铁路相关问题，如果问题不相关，请礼貌地引导用户咨询铁路相关内容
            2. 回答准确、专业、简洁
            3. 匹配用户的语言
            4. 语气友好耐心
            5. 可以适当使用emoji表情
        回答语气：
            - %s
        你必须严格遵守上述规则来回复用户。
    """

# 初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []
# 助手名称
if "assistant_name" not in st.session_state:
    st.session_state.assistant_name = "小铁"
# 语气
if "tone" not in st.session_state:
    st.session_state.tone = "专业严谨的官方客服"
# 语音开关
if "enable_voice" not in st.session_state:
    st.session_state.enable_voice = False
# 会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

# 展示聊天信息
st.text(f"会话名称: {st.session_state.current_session}")
for message in st.session_state.messages: # {"role": "user", "content": prompt}
    st.chat_message(message["role"]).write(message["content"])

# 创建与AI大模型交互的客户端对象 (DEEPSEEK_API_KEY 环境变量的名字, 值就是DeepSeek的API_KEY的)
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

# 左侧的侧边栏 - with: streamlit中上下文管理器
with st.sidebar:
    # 会话信息
    st.subheader("AI控制面板")

    # 新建会话
    if st.button("新建会话", width="stretch", icon="✏️"):
        # 1. 保存当前会话信息
        save_session()

        # 2. 创建新的会话
        if st.session_state.messages: # 如果聊天信息非空, True; 否则,  False
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()  # 重新运行当前页面

    # 会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1,col2 = st.columns([4,1])
        with col1:
           # 加载会话信息
           # 三元运算符: 如果条件为真, 则返回第一个表达式的值; 否则, 返回第二个表达式的值 --> 语法: 值1 if 条件 else 值2
           if st.button(session, width="stretch", icon="📄", key=f"load_{session}", type="primary" if session == st.session_state.current_session else "secondary"):
               load_session(session)
               st.rerun()
        with col2:
            # 删除会话信息
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    # 分割线
    st.divider()

    # 助手信息
    st.subheader("助手设置")
    # 助手名称输入框
    assistant_name = st.text_input("助手名称", placeholder="请输入助手名称", value=st.session_state.assistant_name)
    if assistant_name:
        st.session_state.assistant_name = assistant_name

    # 语气选择
    tone_options = [
        "专业严谨的官方客服",
        "亲切热情的旅行顾问",
        "活泼可爱的铁路小助手",
        "冷静果断的调度员风格",
        "温柔耐心的服务人员"
    ]
    tone = st.selectbox("回答语气", tone_options, index=tone_options.index(st.session_state.tone) if st.session_state.tone in tone_options else 0)
    if tone:
        st.session_state.tone = tone

    # 语音设置
    st.subheader("语音设置")
    st.toggle("开启语音播报", key="enable_voice")
    # #region debug-point A:toggle-state
    report_debug_event(
        "A",
        "语音开关状态已渲染",
        {"enable_voice": st.session_state.get("enable_voice", False)},
        "08_ai_partner_6.py:223",
    )
    # #endregion

# 消息输入框
prompt = st.chat_input("请输入您要咨询的铁路相关问题")
if prompt: # 字符串会自动转换为布尔值, 如果字符串非空, 则为True; ""否则为False
    st.chat_message("user").write(prompt)
    print("----------> 调用AI大模型, 提示词: ", prompt)
    # 保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用AI大模型
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.assistant_name, st.session_state.tone)},
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

    # 语音播报
    # #region debug-point A:voice-branch-entry
    report_debug_event(
        "A",
        "进入语音分支判断",
        {
            "enable_voice": st.session_state.get("enable_voice", False),
            "has_response": bool(full_response),
            "response_length": len(full_response),
        },
        "08_ai_partner_6.py:257",
    )
    # #endregion
    if st.session_state.get("enable_voice", False) and full_response:
        try:
            # #region debug-point B:gtts-start
            report_debug_event("B", "开始生成 gTTS 音频", {"preview": full_response[:50]}, "08_ai_partner_6.py:267")
            # #endregion
            tts = gTTS(text=full_response, lang='zh-cn')
            tts.save("temp_audio.mp3")
            # #region debug-point B:gtts-saved
            report_debug_event(
                "B",
                "gTTS 音频生成完成",
                {
                    "file_exists": os.path.exists("temp_audio.mp3"),
                    "file_size": os.path.getsize("temp_audio.mp3") if os.path.exists("temp_audio.mp3") else 0,
                },
                "08_ai_partner_6.py:276",
            )
            # #endregion
            # 使用 base64 编码并在界面中自动播放
            with open("temp_audio.mp3", "rb") as f:
                audio_bytes = f.read()
            # #region debug-point C:audio-html
            report_debug_event(
                "C",
                "音频数据已准备输出到 Streamlit 播放器",
                {"audio_bytes_length": len(audio_bytes)},
                "08_ai_partner_6.py:296",
            )
            # #endregion
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        except Exception as e:
            # #region debug-point B:gtts-error
            report_debug_event("B", "gTTS 或音频渲染异常", {"error": str(e)}, "08_ai_partner_6.py:301")
            # #endregion
            st.error(f"语音生成失败: {e}")

    # 保存会话信息
    save_session()
