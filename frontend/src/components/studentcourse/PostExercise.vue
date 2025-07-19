<template>
  <div v-if="isDeadlinePassed" class="deadline-alert">
    <a-alert
      message="已超过截止时间，无法继续提交答案"
      type="warning"
      show-icon
      banner
    />
  </div>
  <div class="exercise-container">
    <!-- 顶部题目导航栏 -->
    <div class="question-nav">
      <div class="question-numbers">
        <div
          v-for="(q, index) in questions"
          :key="q.id"
          :class="[
            'question-number',
            {
              active: currentIndex === index,
              answered: q.has_answered || savedAnswers[index],
            },
          ]"
          @click="currentIndex = index"
        >
          {{ index + 1 }}
        </div>
      </div>

      <div class="navigation-buttons">
        <a-button @click="prevQuestion" :disabled="currentIndex === 0">
          上一题
        </a-button>

        <a-button
          v-if="currentIndex < questions.length - 1"
          type="primary"
          @click="nextQuestion"
        >
          下一题
        </a-button>

        <a-button
          v-else
          type="primary"
          @click="submitAll"
          :disabled="Object.keys(savedAnswers).length === 0"
        >
          提交答案
        </a-button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧题目区域 -->
      <div class="question-area">
        <!-- 题目内容 -->
        <div class="question-content">
          <h3>题目 {{ currentIndex + 1 }}</h3>
          <Markdown :source="currentQuestion.content" />
        </div>

        <!-- 答题区域 -->
        <div class="answer-area">
          <div v-if="!currentQuestion.has_answered">
            <!-- 选择题 -->
            <div
              v-if="currentQuestion.type === 'choice'"
              class="choice-options"
            >
              <a-radio-group
                v-model:value="currentAnswer"
                class="choice-buttons"
              >
                <a-radio-button
                  v-for="letter in ['A', 'B', 'C', 'D']"
                  :key="letter"
                  :value="letter"
                  class="choice-button"
                >
                  {{ letter }}
                </a-radio-button>
              </a-radio-group>
            </div>

            <!-- 填空题/简答题 -->
            <div
              v-if="
                currentQuestion.type === 'fill' ||
                currentQuestion.type === 'short_answer'
              "
            >
              <a-textarea
                v-model:value="currentAnswer"
                :placeholder="
                  currentQuestion.type === 'fill' ? '请输入答案' : '请简要回答'
                "
                :rows="currentQuestion.type === 'fill' ? 2 : 4"
                class="text-answer"
              />
            </div>

            <!-- 编程题 -->
            <div
              v-if="currentQuestion.type === 'programming'"
              class="programming-area"
            >
              <div class="editor-container">
                <CodeEditor
                  ref="codeEditor"
                  v-model="code"
                  v-model:language="programmingLanguage"
                  height="300px"
                />

                <div class="action-bar">
                  <a-button
                    type="primary"
                    @click="runCode"
                    :loading="isRunning"
                  >
                    {{ isRunning ? "运行中..." : "运行代码" }}
                  </a-button>
                  <a-button
                    type="primary"
                    @click="saveOutputAsAnswer"
                    :disabled="!output || output === '运行结果将显示在这里...'"
                    class="save-output-btn"
                  >
                    保存输出为答案
                  </a-button>
                </div>
              </div>

              <div class="io-section">
                <div class="input-section">
                  <h4>输入 (stdin)</h4>
                  <a-textarea v-model:value="stdin" :rows="2" />
                </div>

                <div class="output-section">
                  <h4>运行结果</h4>
                  <div class="output-content" :class="{ error: outputIsError }">
                    <pre>{{ output }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else>
            <div class="answer-record">
              <h3>答题记录</h3>
              <div class="record-detail">
                <p>
                  <strong>正确答案：</strong>
                  {{ currentQuestion.correct_answer }}
                </p>
                <p>
                  <strong>您的答案：</strong>
                  {{ currentQuestion.answer_record?.student_answer }}
                </p>
                <p>
                  <strong>答题时间：</strong>
                  {{
                    formatDate(currentQuestion.answer_record?.answered_at) ||
                    "未提交"
                  }}
                </p>
              </div>

              <div class="question-analysis">
                <h3>题目解析</h3>
                <Markdown :source="currentQuestion.analysis || '暂无解析'" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧AI助手区域 -->
      <div class="ai-assistant-area">
        <!-- 未作答显示AI助手 -->
        <QuestionAIChat
          :visible="true"
          :classId="classId"
          :questionId="currentQuestion.id"
          class="ai-chat"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, defineProps, defineEmits } from "vue";
import Markdown from "vue3-markdown-it";
import CodeEditor from "@/components/questions/CodeEditor.vue";
import QuestionAIChat from "@/components/QuestionAIChat.vue";
import { questionApi } from "@/api/questions";
import { message } from "ant-design-vue";
import dayjs from "dayjs";

const props = defineProps({
  classId: {
    type: Number,
    required: true,
  },
  courseId: {
    type: Number,
    required: true,
  },
  deadline: {
    // 新增
    type: String,
    default: null,
  },
});

// 2. 添加emit定义
const emit = defineEmits(["submit"]);

// 3. 添加截止时间检查
const isDeadlinePassed = computed(() => {
  if (!props.deadline) return false;
  return dayjs().isAfter(dayjs(props.deadline));
});

// Piston API 地址
const PISTON_API_URL = "https://emkc.org/api/v2/piston";

// 题目数据
const questions = ref([]);
const currentIndex = ref(0);
const currentAnswer = ref("");
const programmingLanguage = ref("python");
const isRunning = ref(false);
const output = ref("运行结果将显示在这里...");
const stdin = ref("");
const outputIsError = ref(false);
const savedAnswers = ref({}); // 存储所有题目的答案

// 获取当前题目
const currentQuestion = computed(() => {
  return questions.value[currentIndex.value] || {};
});

// 加载课后习题
const loadQuestions = async () => {
  try {
    const response = await questionApi.StugetPostQuestions(props.courseId);
    questions.value = response;

    // 尝试从本地存储加载保存的答案
    const saved = localStorage.getItem(`postExerciseAnswers_${props.courseId}`);
    if (saved) {
      savedAnswers.value = JSON.parse(saved);
    }

    // 初始化当前题目的答案
    if (savedAnswers.value[currentIndex.value] !== undefined) {
      currentAnswer.value = savedAnswers.value[currentIndex.value];
    } else if (questions.value[currentIndex.value]?.has_answered) {
      currentAnswer.value =
        questions.value[currentIndex.value].answer_record?.student_answer || "";
    } else {
      currentAnswer.value = "";
    }
  } catch (error) {
    console.error("加载习题失败:", error);
    message.error("加载习题失败，请刷新页面重试");
  }
};

// 保存当前答案到本地存储
const saveAnswer = () => {
  if (currentAnswer.value.trim() !== "") {
    savedAnswers.value[currentIndex.value] = currentAnswer.value;
    localStorage.setItem(
      `postExerciseAnswers_${props.courseId}`,
      JSON.stringify(savedAnswers.value)
    );
  }
};

// 自动保存答案的监听
watch(currentAnswer, (newVal) => {
  if (newVal.trim() !== "") {
    saveAnswer();
  }
});

// 题目切换
const prevQuestion = () => {
  if (currentIndex.value > 0) {
    saveAnswer();
    currentIndex.value--;
    // 加载新题目的答案
    currentAnswer.value =
      savedAnswers.value[currentIndex.value] ||
      currentQuestion.value.answer_record?.student_answer ||
      "";
    output.value = "运行结果将显示在这里...";
    outputIsError.value = false;
  }
};

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) {
    saveAnswer();
    currentIndex.value++;
    // 加载新题目的答案
    currentAnswer.value =
      savedAnswers.value[currentIndex.value] ||
      currentQuestion.value.answer_record?.student_answer ||
      "";
    output.value = "运行结果将显示在这里...";
    outputIsError.value = false;
  }
};

// 4. 修改submitAll方法，实际提交到服务器
const submitAll = async () => {
  if (isDeadlinePassed.value) {
    message.error("已超过截止时间，无法提交");
    return;
  }

  try {
    // 收集所有答案
    const answers = Object.entries(savedAnswers.value).map(
      ([index, answer]) => ({
        questionId: questions.value[index].id,
        answer: answer,
      })
    );

    // 触发submit事件
    emit("submit", answers);

    // 清空本地存储
    localStorage.removeItem(`postExerciseAnswers_${props.courseId}`);
    savedAnswers.value = {};

    // 重新加载题目以更新答题状态
    await loadQuestions();

    message.success("答案提交成功！");
  } catch (error) {
    message.error("提交失败，请重试");
    console.error("提交错误:", error);
  }
};

const codeEditor = ref(null);
const code = ref("");
// 运行代码（编程题）
const runCode = async () => {
  if (isRunning.value) return;

  isRunning.value = true;
  output.value = "代码执行中...";
  outputIsError.value = false;

  try {
    console.log("代码内容：", code.value);
    // 设置超时处理
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${PISTON_API_URL}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language: programmingLanguage.value,
        version: "*",
        files: [{ content: code.value }],
        stdin: stdin.value,
        args: [],
        compile_timeout: 10000,
        run_timeout: 5000,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const result = await response.json();

    if (result.run.stderr) {
      output.value = result.run.stderr;
      outputIsError.value = true;
    } else {
      output.value = result.run.output || "执行成功(无输出)";
    }
  } catch (error) {
    if (error.name === "AbortError") {
      output.value = "错误: 请求超时，请检查代码或网络连接";
    } else {
      output.value = `错误: ${error.message}`;
    }
    outputIsError.value = true;
  } finally {
    isRunning.value = false;
  }
};

// 将运行输出保存为答案
const saveOutputAsAnswer = () => {
  if (output.value && output.value !== "运行结果将显示在这里...") {
    currentAnswer.value = output.value;
    message.success("已保存运行结果为答案");
  }
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${date.getDate().toString().padStart(2, "0")} ${date
    .getHours()
    .toString()
    .padStart(2, "0")}:${date.getMinutes().toString().padStart(2, "0")}`;
};

// 监听当前题目变化
watch(currentIndex, (newIndex) => {
  // 加载新题目的答案
  currentAnswer.value =
    savedAnswers.value[newIndex] ||
    questions.value[newIndex]?.answer_record?.student_answer ||
    "";
  output.value = "运行结果将显示在这里...";
  outputIsError.value = false;
});

// 初始化加载
onMounted(() => {
  loadQuestions();
});
</script>

<style scoped>
/* 新增保存输出按钮样式 */
.save-output-btn {
  margin-left: 10px;
  background-color: #1890ff;
}

/* 其他样式保持不变 */
.exercise-container {
  margin: auto;
  height: 81vh;
  width: 90%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.question-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background-color: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-numbers {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.question-number {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: #f0f2f5;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
  border: 1px solid #e8e8e8;
}

.question-number:hover {
  background-color: #e6f7ff;
  border-color: #91d5ff;
}

.question-number.active {
  background-color: #1890ff;
  color: white;
  border-color: #1890ff;
}

.question-number.answered {
  background-color: #52c41a;
  color: white;
  border-color: #52c41a;
}

.navigation-buttons {
  display: flex;
  gap: 10px;
}

.main-content {
  display: flex;
  flex: 1;
  gap: 20px;
  overflow: hidden;
}

.question-area {
  flex: 6;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  overflow-y: auto;
}

.ai-assistant-area {
  flex: 4;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.question-content {
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
}

.question-content h3 {
  color: #1890ff;
  margin-bottom: 15px;
}

.answer-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.choice-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 10px;
}

.choice-option {
  padding: 12px 15px;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
  background-color: #fafafa;
  transition: all 0.2s;
}

.choice-option:hover {
  background-color: #e6f7ff;
  border-color: #91d5ff;
}

.option-label {
  font-weight: bold;
  margin-right: 8px;
  color: #1890ff;
}

.text-answer {
  margin-top: 15px;
}

.programming-area {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 15px;
}

.editor-container {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  overflow: hidden;
}

.action-bar {
  padding: 10px;
  background-color: #fafafa;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
}

.io-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.input-section,
.output-section {
  background-color: #fafafa;
  border-radius: 6px;
  padding: 15px;
  border: 1px solid #f0f0f0;
}

.output-content {
  background-color: white;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 10px;
  min-height: 100px;
  font-family: monospace;
  white-space: pre-wrap;
  overflow: auto;
  max-height: 200px;
}

.answer-record {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.record-detail {
  background-color: #f9f9f9;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.question-analysis {
  background-color: #f0f9ff;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #e6f7ff;
}

.ai-chat {
  height: 100%;
  border-radius: 0;
  box-shadow: none;
}
</style>
