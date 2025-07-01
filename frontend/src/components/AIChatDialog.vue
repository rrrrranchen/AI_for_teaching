<template>
  <a-modal
    :visible="internalVisible"
    title="DeepSeek AI助手"
    :width="1200"
    :footer="null"
    :bodyStyle="{ padding: '0' }"
    :style="{ top: '20px' }"
    @cancel="handleClose"
    @ok="handleClose"
    class="ai-chat-modal"
  >
    <div class="ai-chat-container">
      <!-- 消息列表 -->
      <div class="chat-messages" ref="messagesContainer">
        <!-- AI欢迎消息 -->
        <div class="message assistant">
          <div class="message-content">
            <div class="ai-avatar">
              <RobotOutlined />
            </div>
            <div class="text-content">
              <Markdown :source="welcomeMessage" />
            </div>
          </div>
        </div>

        <!-- 历史消息 -->
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="message-content">
            <div class="user-avatar" v-if="msg.role === 'user'">
              <UserOutlined />
            </div>
            <div class="ai-avatar" v-else>
              <RobotOutlined />
            </div>
            <div class="text-content">
              <Markdown v-if="msg.role === 'assistant'" :source="msg.content" />
              <template v-else>{{ msg.content }}</template>
              <div v-if="msg.isTyping" class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="message assistant">
          <div class="message-content">
            <div class="ai-avatar">
              <RobotOutlined />
            </div>
            <div class="text-content">
              <a-spin size="large" />
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <a-textarea
          v-model:value="inputMessage"
          placeholder="输入您的问题..."
          :rows="4"
          allow-clear
          @pressEnter="handleSend"
        />
        <div class="input-actions">
          <span class="char-count">{{ inputMessage.length }}/2000</span>
          <a-button
            type="primary"
            @click="sendMessage"
            :loading="loading"
            :disabled="!inputMessage.trim()"
          >
            发送
          </a-button>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch, nextTick, defineProps, defineEmits } from "vue";
import { RobotOutlined, UserOutlined } from "@ant-design/icons-vue";
import Markdown from "vue3-markdown-it";
import "highlight.js/styles/github.css";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:visible"]);

// 数据
const internalVisible = ref(props.visible);
const inputMessage = ref("");
const loading = ref(false);
const messagesContainer = ref(null);
const messages = ref([]);
const welcomeMessage = ref(`
# 欢迎使用 DeepSeek AI 助手

我是您的智能助手，可以帮助您解决各种问题，包括：

- **代码编写**：Python、Java、C++等
- **学习辅导**：数学、物理、编程等
- **内容创作**：文章、报告、邮件等
- **问题解答**：技术问题、生活常识等

请随时向我提问！
`);

// 监听visible变化
watch(
  () => props.visible,
  (val) => {
    internalVisible.value = val;
    if (val) {
      nextTick(() => {
        scrollToBottom();
      });
    }
  }
);

// 方法
const handleClose = () => {
  internalVisible.value = false;
  emit("update:visible", false);
};

const handleSend = (e) => {
  if (e.shiftKey) {
    return; // 允许换行
  }
  e.preventDefault();
  sendMessage();
};

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return;

  const userMsg = {
    role: "user",
    content: inputMessage.value,
    isTyping: false,
  };

  messages.value.push(userMsg);
  const aiMsg = {
    role: "assistant",
    content: "",
    isTyping: true,
  };
  messages.value.push(aiMsg);

  inputMessage.value = "";
  loading.value = true;
  scrollToBottom();

  try {
    // 模拟API调用
    const response = await simulateAPI(userMsg.content);
    aiMsg.content = response;
    aiMsg.isTyping = false;
  } catch (error) {
    aiMsg.content = "抱歉，获取回复时出现错误，请稍后再试。";
    aiMsg.isTyping = false;
    console.error("API调用错误:", error);
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const simulateAPI = (prompt) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const responses = [
        `## 关于 "${prompt}" 的解答\n\n根据您的问题，我建议您可以尝试以下方法...\n\n\`\`\`python\n# 示例代码\ndef solution():\n    return "这是Python示例代码"\n\`\`\``,
        `### 这是一个很好的问题\n\n关于"${prompt}"，让我为您详细解释：\n\n1. **第一步**：理解问题\n2. **第二步**：分析原因\n3. **第三步**：解决方案\n\n> 提示：这是Markdown渲染的引用块`,
        `**教育领域**的${prompt}通常可以通过以下方式解决：\n\n- 方法一\n- 方法二\n- 方法三\n\n更多信息请参考[官方文档](https://example.com)`,
        `我理解您的困惑，让我们一步步分析${prompt}：\n\n\`\`\`javascript\n// JavaScript示例\nconsole.log("代码示例");\n\`\`\`\n\n**关键点**：\n- 要点1\n- 要点2`,
        `基于我的知识库，关于${prompt}的最佳实践是：\n\n\`\`\`\n代码块或命令示例\n\`\`\`\n\n**注意事项**：\n1. 注意一\n2. 注意二`,
      ];
      resolve(responses[Math.floor(Math.random() * responses.length)]);
    }, 1500);
  });
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};
</script>

<style scoped lang="scss">
.ai-chat-modal {
  :deep(.ant-modal-body) {
    padding: 0;
  }

  :deep(.ant-modal-header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;

    .ant-modal-title {
      color: white;
      font-size: 18px;
      font-weight: 600;
    }
  }

  :deep(.ant-modal-close) {
    color: white;
  }
}

.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 80vh;
  background: #f8fafc;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
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

    .message-bubble {
      background: #ffffff;
      border: 2px solid rgba(0, 0, 0, 0.08);
      border-radius: 20px 20px 20px 6px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    }
  }

  &.user {
    .message-content {
      margin-right: 8px;
      flex-direction: row-reverse;
    }

    .message-bubble {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 20px 20px 6px 20px;
      box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
  }
}

.message-content {
  display: flex;
  align-items: flex-start;
  max-width: 80%;
  margin: 0 auto;
}

.ai-avatar,
.user-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 12px;
  font-size: 18px;
}

.ai-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 3px 12px rgba(102, 126, 234, 0.3);
}

.user-avatar {
  background: #f0f0f0;
  color: #666;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15);
}

.text-content {
  flex: 1;
  padding: 16px 20px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
  font-size: 14px;
  background: #e7ecff;

  :deep(*) {
    margin-top: 0;
    margin-bottom: 0.8em;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(pre) {
    background: rgba(0, 0, 0, 0.05);
    padding: 12px;
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
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;

  .char-count {
    font-size: 14px;
    color: #718096;
  }

  .ant-btn {
    height: 40px;
    padding: 0 24px;
    font-size: 16px;
    color: #e2e8f0;
    border-radius: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
  }
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
</style>
