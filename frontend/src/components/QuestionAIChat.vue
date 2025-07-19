<template>
  <div class="ai-chat-container">
    <div class="ai-chat-container">
      <!-- 消息列表 -->
      <div class="chat-messages" ref="messagesContainer">
        <!-- AI欢迎消息 -->
        <div class="message assistant" v-if="messages.length === 0">
          <div class="message-content">
            <div class="ai-avatar">
              <a-avatar size="large" :src="AIavatar" class="nav-avatar">
              </a-avatar>
            </div>
            <div class="text-content">
              <Markdown :source="welcomeMessage" />
            </div>
          </div>
        </div>

        <!-- 历史消息 -->
        <template v-for="(msg, index) in messages" :key="msg.id">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="message user">
            <div class="message-content">
              <div class="user-avatar">
                <a-avatar
                  v-if="auth.user?.avatar"
                  size="large"
                  :src="'http://localhost:5000/' + auth.user?.avatar"
                  class="nav-avatar"
                >
                </a-avatar>
                <a-avatar v-else :size="48" class="nav-avatar">
                  <UserOutlined />
                </a-avatar>
              </div>
              <div class="text-content">
                {{ msg.content }}
              </div>
            </div>
          </div>

          <!-- AI消息 -->
          <div v-else class="message assistant">
            <div class="message-content">
              <div class="ai-avatar">
                <a-avatar
                  size="large"
                  :src="AIavatar"
                  class="nav-avatar"
                ></a-avatar>
              </div>
              <div class="text-content">
                <!-- 思考过程 -->
                <div
                  v-if="msg.thinkingMode && msg.thinkingContent"
                  class="thinking-container"
                >
                  <a-collapse
                    :bordered="false"
                    :activeKey="thinkingExpanded[msg.id] ? '1' : []"
                  >
                    <a-collapse-panel key="1" :showArrow="false">
                      <template #header>
                        <div
                          class="thinking-header"
                          @click.stop="toggleThinking(msg.id)"
                        >
                          <span class="thinking-title">思考过程</span>
                          <span class="toggle-icon">
                            {{ thinkingExpanded[msg.id] ? "收起" : "展开" }}
                          </span>
                        </div>
                      </template>
                      <div class="thinking-text">
                        {{ msg.thinkingContent }}
                      </div>
                    </a-collapse-panel>
                  </a-collapse>
                </div>
                <Markdown :source="msg.content" />
              </div>
            </div>

            <!-- 知识参考 -->
            <div v-if="msg.sources" class="sources-container">
              <a-collapse class="sources-collapse" :bordered="false">
                <a-collapse-panel key="1" :header="msg.sources.message">
                  <div
                    v-for="(source, sIndex) in msg.sources.sources"
                    :key="sIndex"
                    class="source-section"
                  >
                    <div class="source-meta">
                      <span v-if="source.knowledge_base"
                        >知识库: {{ source.knowledge_base.name }}</span
                      >
                      <span v-if="source.category"
                        >分类: {{ source.category.name }}</span
                      >
                      <span v-if="source.file"
                        >文件: {{ source.file.name }}</span
                      >
                    </div>
                    <div
                      v-for="(chunk, cIndex) in source.chunks"
                      :key="cIndex"
                      class="chunk-item"
                    >
                      <div
                        class="chunk-header"
                        @click="toggleChunk(index, sIndex, cIndex)"
                      >
                        <span>片段 #{{ chunk.position }}</span>
                        <span class="toggle-icon">
                          {{
                            isChunkExpanded(index, sIndex, cIndex)
                              ? "收起"
                              : "展开"
                          }}
                        </span>
                      </div>
                      <div
                        v-if="isChunkExpanded(index, sIndex, cIndex)"
                        class="chunk-content"
                      >
                        <Markdown :source="chunk.text" />
                      </div>
                    </div>
                  </div>
                </a-collapse-panel>
              </a-collapse>
            </div>
          </div>
        </template>

        <!-- 流式输出中的消息 -->
        <div v-if="isStreaming" class="message assistant">
          <div class="message-content">
            <div class="ai-avatar">
              <a-avatar
                size="large"
                :src="AIavatar"
                class="nav-avatar"
              ></a-avatar>
            </div>
            <div class="text-content">
              <!-- 流式思考过程 -->
              <div
                v-if="thinkingMode && streamingThinkingContent"
                class="thinking-bubble"
              >
                <div class="thinking-header">
                  <span class="thinking-title">思考中...</span>
                  <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
                <div class="thinking-text">
                  {{ streamingThinkingContent }}
                </div>
              </div>
              <Markdown :source="streamingContent" />
              <div v-if="!streamingContent" class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>

          <!-- 流式知识参考（仅在结束时显示） -->
          <div v-if="streamingSources" class="sources-container">
            <a-collapse class="sources-collapse" :bordered="false">
              <a-collapse-panel key="1" :header="streamingSources.message">
                <div
                  v-for="(source, sIndex) in streamingSources.sources"
                  :key="sIndex"
                  class="source-section"
                >
                  <div class="source-meta">
                    <span v-if="source.knowledge_base"
                      >知识库: {{ source.knowledge_base.name }}</span
                    >
                    <span v-if="source.category"
                      >分类: {{ source.category.name }}</span
                    >
                    <span v-if="source.file">文件: {{ source.file.name }}</span>
                  </div>
                  <div
                    v-for="(chunk, cIndex) in source.chunks"
                    :key="cIndex"
                    class="chunk-item"
                  >
                    <div
                      class="chunk-header"
                      @click="toggleStreamingChunk(sIndex, cIndex)"
                    >
                      <span>片段 #{{ chunk.position }}</span>
                      <span class="toggle-icon">
                        {{
                          isStreamingChunkExpanded(sIndex, cIndex)
                            ? "收起"
                            : "展开"
                        }}
                      </span>
                    </div>
                    <div
                      v-if="isStreamingChunkExpanded(sIndex, cIndex)"
                      class="chunk-content"
                    >
                      <Markdown :source="chunk.text" />
                    </div>
                  </div>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <a-textarea
          v-model:value="inputMessage"
          placeholder="输入您的问题..."
          :rows="2"
          allow-clear
          @pressEnter="handleSend"
          :disabled="isLoading"
        />
        <div class="input-actions">
          <span class="char-count">{{ inputMessage.length }}/2000</span>
          <div v-if="isRecording" class="recording-status">
            录音中... {{ formatRecordingTime }}
          </div>
          <!-- 语音输入按钮 -->
          <a-button
            class="voice-btn"
            :type="isRecording ? 'danger' : 'default'"
            @click="toggleVoiceInput"
          >
            <template #icon>
              <audio-outlined v-if="!isRecording" />
              <loading-outlined v-else class="recording-animation" />
            </template>
            {{ isRecording ? "停止录音" : "语音输入" }}
          </a-button>
          <!-- 思考模式切换 -->
          <a-button
            class="thinking-btn"
            :type="thinkingMode ? 'primary' : 'default'"
            @click="thinkingMode = !thinkingMode"
          >
            <template #icon><TrademarkCircleOutlined /></template>
            深度思考
          </a-button>
          <a-button
            type="primary"
            @click="handleSend"
            :loading="isLoading"
            :disabled="!inputMessage.trim()"
          >
            发送
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  watch,
  nextTick,
  defineProps,
  defineEmits,
  onUnmounted,
  computed,
} from "vue";
import { message } from "ant-design-vue";
import Markdown from "vue3-markdown-it";
import "highlight.js/styles/github.css";
import { questionClassChat } from "@/api/aichat";
import { useAuthStore } from "@/stores/auth";
import AIavatar from "@/assets/xiaozhi_avatar.png";
import {
  TrademarkCircleOutlined,
  UserOutlined,
  AudioOutlined,
  LoadingOutlined,
} from "@ant-design/icons-vue";

const auth = useAuthStore();

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  classId: {
    type: Number,
    required: true,
  },
  questionId: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(["update:visible"]);

// 数据
const internalVisible = ref(props.visible);
const inputMessage = ref("");
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);
const messages = ref([]);
const streamingContent = ref("");
const streamingThinkingContent = ref("");
const streamingSources = ref(null);
const thinkingMode = ref(false);

// 欢迎消息
const welcomeMessage = ref(`
# 题目AI助手

我是您的题目专属助手，可以为您：

1. **解释题目**：分析题目要求和解题思路
2. **解答疑问**：回答题目相关的任何问题
3. **提供提示**：在您卡住时给予解题提示
4. **检查答案**：(完成习题后)帮助验证您的解答是否正确

请随时向我提问关于题目的任何问题！
`);

// 监听visible变化
watch(
  () => props.visible,
  (val) => {
    internalVisible.value = val;
    if (val) {
      // 每次打开重置消息
      messages.value = [];
      messageIdCounter = 0;
      nextTick(() => {
        scrollToBottom();
      });
    }
  }
);

// 用于管理展开/收起状态
const expandedChunks = ref({});
const expandedStreamingChunks = ref({});

// 检查片段是否展开
const isChunkExpanded = (msgIndex, sourceIndex, chunkIndex) => {
  return expandedChunks.value[`${msgIndex}-${sourceIndex}-${chunkIndex}`];
};

const isStreamingChunkExpanded = (sourceIndex, chunkIndex) => {
  return expandedStreamingChunks.value[`${sourceIndex}-${chunkIndex}`];
};

// 切换片段展开状态
const toggleChunk = (msgIndex, sourceIndex, chunkIndex) => {
  const key = `${msgIndex}-${sourceIndex}-${chunkIndex}`;
  expandedChunks.value = {
    ...expandedChunks.value,
    [key]: !expandedChunks.value[key],
  };
};

const toggleStreamingChunk = (sourceIndex, chunkIndex) => {
  const key = `${sourceIndex}-${chunkIndex}`;
  expandedStreamingChunks.value = {
    ...expandedStreamingChunks.value,
    [key]: !expandedStreamingChunks.value[key],
  };
};

const handleSend = (e) => {
  if (e.shiftKey) {
    return; // 允许换行
  }
  e.preventDefault();
  sendMessage();
};

let messageIdCounter = 0;
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const msgId = messageIdCounter++;
  const userMsg = {
    id: msgId,
    role: "user",
    content: inputMessage.value,
  };

  messages.value.push(userMsg);

  inputMessage.value = "";
  isLoading.value = true;
  isStreaming.value = true;
  streamingContent.value = "";
  streamingThinkingContent.value = "";
  streamingSources.value = null;
  expandedStreamingChunks.value = {};
  scrollToBottom();

  let cancelFunction;

  try {
    // 获取最近5条消息作为历史
    const recentHistory = messages.value
      .slice(-5)
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({
        role: m.role,
        content: m.content,
      }));

    cancelFunction = questionClassChat(
      props.questionId,
      {
        query: userMsg.content,
        thinking_mode: thinkingMode.value,
        class_id: props.classId,
        history: recentHistory,
      },
      (response) => {
        switch (response.status) {
          case "reasoning":
            // 累积思考内容
            streamingThinkingContent.value += response.content;
            scrollToBottom();
            break;
          case "content":
            // 累积回复内容
            streamingContent.value += response.content;
            scrollToBottom();
            break;
          case "end":
            // 保存资源
            if (response.sources) {
              streamingSources.value = response.sources;
            }
            break;
        }
      },
      (error) => {
        console.error("AI聊天错误:", error);
        addAssistantMessage("抱歉，处理您的请求时出错了。", "", null, null);
      },
      () => {
        isLoading.value = false;
        isStreaming.value = false;
        // 将流式内容保存为正式消息
        if (streamingContent.value || streamingThinkingContent.value) {
          addAssistantMessage(
            streamingContent.value,
            thinkingMode.value,
            thinkingMode.value ? streamingThinkingContent.value : "",
            streamingSources.value
          );

          // 重置流式内容
          streamingContent.value = "";
          streamingThinkingContent.value = "";
          streamingSources.value = null;
          inputMessage.value = "";
        }

        scrollToBottom();
      }
    );
  } catch (error) {
    console.error("请求错误:", error);
    isLoading.value = false;
    isStreaming.value = false;
    addAssistantMessage("请求发送失败，请稍后再试", "", null, null);
  }

  // 组件卸载时取消请求
  onUnmounted(() => {
    cancelFunction?.();
  });
};

// 添加思考过程的展开状态
const thinkingExpanded = ref({});

// 切换思考过程展开状态的方法
const toggleThinking = (msgId) => {
  thinkingExpanded.value = {
    ...thinkingExpanded.value,
    [msgId]: !thinkingExpanded.value[msgId],
  };
};

// 添加助手消息
const addAssistantMessage = (
  content,
  thinkingMode,
  thinkingContent,
  sources
) => {
  const msgId = messageIdCounter++;
  messages.value.push({
    id: msgId, // 添加唯一ID
    role: "assistant",
    content: content,
    thinkingMode: thinkingMode,
    thinkingContent: thinkingContent,
    sources: sources,
  });
  // 默认收起思考过程
  thinkingExpanded.value[msgId] = false;
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

// 新增状态变量
const isRecording = ref(false);
const recordingTime = ref(0);
const recognition = ref(null);
const recordingTimer = ref(null);

// 格式化录音时间
const formatRecordingTime = computed(() => {
  const mins = Math.floor(recordingTime.value / 60);
  const secs = recordingTime.value % 60;
  return `${mins.toString().padStart(2, "0")}:${secs
    .toString()
    .padStart(2, "0")}`;
});

// 初始化语音识别
const initSpeechRecognition = () => {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    message.error("您的浏览器不支持语音识别功能，请使用Chrome浏览器");
    return false;
  }

  recognition.value = new SpeechRecognition();
  recognition.value.continuous = true;
  recognition.value.interimResults = true;
  recognition.value.lang = "zh-CN";

  recognition.value.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        transcript += event.results[i][0].transcript;
      }
    }
    inputMessage.value += transcript;
  };

  recognition.value.onerror = (event) => {
    console.error("语音识别错误:", event.error);
    stopRecording();
    message.error(`语音识别错误: ${event.error}`);
  };

  return true;
};

// 切换录音状态
const toggleVoiceInput = () => {
  if (isRecording.value) {
    stopRecording();
  } else {
    startRecording();
  }
};

// 开始录音
const startRecording = () => {
  if (!initSpeechRecognition()) return;

  try {
    recognition.value.start();
    isRecording.value = true;
    recordingTime.value = 0;

    // 计时器
    recordingTimer.value = setInterval(() => {
      recordingTime.value++;
    }, 1000);
  } catch (error) {
    message.error("无法访问麦克风，请检查权限设置");
    console.error("麦克风访问错误:", error);
  }
};

// 停止录音
const stopRecording = () => {
  if (recognition.value) {
    recognition.value.stop();
  }
  isRecording.value = false;
  clearInterval(recordingTimer.value);
};
// 组件卸载时清理
onUnmounted(() => {
  if (isRecording.value) {
    stopRecording();
  }
});
</script>

<style scoped lang="scss">
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f8fafc;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-top: 18px;

  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.5);
    border-radius: 3px;

    &:hover {
      background: rgba(102, 126, 234, 0.7);
    }
  }
}

.message {
  margin-bottom: 24px;
  animation: fadeInUp 0.4s ease-out;

  &.assistant {
    .message-content {
      margin-left: 8px;
    }
  }

  &.user {
    .message-content {
      margin-right: 8px;
      flex-direction: row-reverse;
    }
  }
}

.message-content {
  display: flex;
  align-items: flex-start;
  max-width: 90%;
  margin: 0 auto;
}

.ai-avatar,
.user-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid rgb(198, 217, 254);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 10px;
  font-size: 16px;
}

.ai-avatar {
  color: white;
  box-shadow: 0 3px 12px rgba(35, 35, 36, 0.3);
}

.user-avatar {
  background: #f0f0f0;
  color: #666;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15);
}

.text-content {
  width: 80%;
  flex: 1;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
  font-size: 14px;
  background: white;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

  :deep(*) {
    margin-top: 0;
    margin-bottom: 0.8em;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(pre) {
    background: rgba(0, 0, 0, 0.05);
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
  }

  :deep(code) {
    font-family: "Courier New", Courier, monospace;
    font-size: 14px;
  }

  :deep(a) {
    color: #667eea;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  :deep(blockquote) {
    border-left: 4px solid #667eea;
    padding-left: 12px;
    margin-left: 0;
    color: #666;
  }
}

/* 思考过程文本样式 - 普通文本 */
.thinking-text {
  white-space: pre-wrap;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.typing-indicator {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 12px;

  span {
    width: 8px;
    height: 8px;
    background: #667eea;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }
    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

.chat-input {
  padding: 10px;
  border-top: 1px solid #e2e8f0;
  background: white;

  :deep(.ant-input) {
    font-size: 16px;
    line-height: 1.5;
    border-radius: 12px;
    padding: 12px;
    resize: none;
  }
}

.input-actions {
  display: flex;
  justify-content: flex-end; // 改为右对齐
  align-items: center;
  margin-top: 12px;
  gap: 8px;

  .char-count {
    font-size: 14px;
    color: #718096;
    margin-right: auto; // 字符计数靠左
  }

  // 深度思考按钮样式
  .thinking-btn {
    height: 40px;
    padding: 0 15px;
    font-size: 16px;
    border-radius: 20px;

    // 未激活状态 (灰色)
    &:not(.ant-btn-primary) {
      background: #f0f0f0;
      color: rgba(0, 0, 0, 0.45);
      border-color: #d9d9d9;

      &:hover {
        color: #667eea;
        border-color: #667eea;
      }
    }

    // 激活状态 (紫色渐变)
    &.ant-btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      color: white;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
      }
    }
  }

  // 发送按钮样式保持不变
  .ant-btn-primary {
    height: 40px;
    padding: 0 24px;
    font-size: 16px;
    color: white;
    border-radius: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    &:disabled {
      background: #f0f0f0;
      color: #bfbfbf;
      cursor: not-allowed;
    }
  }
}

/* 知识参考部分样式 */
.sources-collapse {
  max-width: 90%;
  margin: 12px auto 0;
  border: none;

  :deep(.ant-collapse-header) {
    padding: 8px 16px !important;
    background: #f0f5ff;
    border-radius: 6px;
    color: #667eea;
    font-weight: 500;
  }

  :deep(.ant-collapse-content) {
    border: none;
    background: transparent;
  }
}

.source-section {
  padding: 12px;
  background: white;
  border-radius: 6px;
  margin-top: 8px;
  border: 1px solid #e2e8f0;
}

.source-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.9em;
  color: #666;
  flex-wrap: wrap;

  span {
    padding: 2px 6px;
    background: #f0f0f0;
    border-radius: 4px;
  }
}

.chunk-item {
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;

  &:last-child {
    margin-bottom: 0;
  }
}

.chunk-header {
  padding: 8px 12px;
  background: #f8fafc;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9em;

  &:hover {
    background: #f0f5ff;
  }
}

.toggle-icon {
  color: #667eea;
  font-size: 0.8em;
}

.chunk-content {
  padding: 12px;
  background: white;
  border-top: 1px solid #e2e8f0;

  :deep(*) {
    margin-top: 0;
    margin-bottom: 0.8em;

    &:last-child {
      margin-bottom: 0;
    }
  }
}

/* 思考过程折叠面板 */
.thinking-container {
  margin-bottom: 12px;

  :deep(.ant-collapse) {
    border: none;
    background: transparent;
  }

  :deep(.ant-collapse-item) {
    border: none;
  }
}

/* 思考过程头部样式 */
.thinking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #667eea;

  &:hover {
    background: #f0f5ff;
  }
}

.thinking-title {
  font-weight: 500;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 新增语音按钮样式 */
.voice-btn {
  height: 40px;
  padding: 0 15px;
  font-size: 16px;
  border-radius: 20px;
  margin-right: 8px;

  &.ant-btn-danger {
    background: #ff4d4f;
    border-color: #ff4d4f;
    color: white;

    &:hover {
      background: #ff7875;
      border-color: #ff7875;
    }
  }
}

/* 录音动画 */
.recording-animation {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
  100% {
    opacity: 1;
  }
}

/* 录音状态提示 */
.recording-status {
  position: absolute;
  bottom: 70px;
  left: 50%;
  transform: translateX(-50%);
  background: #ff4d4f;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.3);
}
</style>
