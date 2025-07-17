<template>
  <div class="coding-page">
    <div class="page-container">
      <!-- 左侧题目区域 -->
      <div class="problem-section">
        <h2>{{ problem.title }}</h2>
        <div class="problem-content" v-html="problem.description"></div>

        <div class="test-cases">
          <h3>示例测试用例</h3>
          <div
            v-for="(testCase, index) in problem.testCases"
            :key="index"
            class="test-case"
          >
            <div class="input">
              <strong>输入:</strong>
              <pre>{{ testCase.input }}</pre>
            </div>
            <div class="output">
              <strong>输出:</strong>
              <pre>{{ testCase.output }}</pre>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧编程区域 -->
      <div class="coding-section">
        <div class="editor-container">
          <CodeEditor
            ref="codeEditor"
            v-model="code"
            v-model:language="language"
            :height="'500px'"
          />

          <div class="action-bar">
            <button @click="runCode" :disabled="isRunning" class="run-button">
              {{ isRunning ? "执行中..." : "执行代码" }}
            </button>
          </div>
        </div>

        <!-- 输入输出区域 -->
        <div class="io-section">
          <div class="input-section">
            <h3>输入 (stdin)</h3>
            <textarea v-model="stdin" rows="4"></textarea>
          </div>

          <div class="output-section">
            <h3>执行结果</h3>
            <div class="output-content" :class="{ error: outputError }">
              <pre>{{ output }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import CodeEditor from "./questions/CodeEditor.vue";

// 定义Piston API地址
const PISTON_API_URL = "https://emkc.org/api/v2/piston";

// 题目数据
const problem = ref({
  title: "两数之和",
  description: `
    <p>给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出 <strong>和为目标值</strong> target 的那 <strong>两个</strong> 整数，并返回它们的数组下标。</p>
    <p>你可以假设每种输入只会对应一个答案。但是，数组中同一个元素在答案里不能重复出现。</p>
    <p>你可以按任意顺序返回答案。</p>
  `,
  testCases: [
    {
      input: "nums = [2,7,11,15], target = 9",
      output: "[0,1]",
    },
    {
      input: "nums = [3,2,4], target = 6",
      output: "[1,2]",
    },
  ],
});

// 编辑器相关状态
const codeEditor = ref(null);
const code = ref(`# 在这里编写你的代码
def two_sum(nums, target):
    # 你的代码
    pass

# 测试代码
nums = [2, 7, 11, 15]
target = 9
print(two_sum(nums, target))`);

const language = ref("python");
const stdin = ref("");
const output = ref("执行结果将显示在这里...");
const outputError = ref(false);
const isRunning = ref(false);

// 运行代码
const runCode = async () => {
  if (isRunning.value) return;

  isRunning.value = true;
  output.value = "执行中...";
  outputError.value = false;

  try {
    console.log("代码内容：", code.value);

    const response = await fetch(`${PISTON_API_URL}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language: language.value,
        version: "*",
        files: [{ content: code.value }],
        stdin: stdin.value,
        args: [],
        compile_timeout: 10000,
        run_timeout: 5000,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.run.stderr) {
      output.value = result.run.stderr;
      outputError.value = true;
    } else {
      output.value = result.run.output || "执行成功(无输出)";
    }
  } catch (error) {
    output.value = `错误: ${error.message}`;
    outputError.value = true;
  } finally {
    isRunning.value = false;
  }
};
</script>

<style scoped>
.coding-page {
  font-family: Arial, sans-serif;
  height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
}

.page-container {
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  gap: 20px;
  height: calc(100vh - 40px);
}

.problem-section {
  flex: 1;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.coding-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.editor-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 15px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.run-button {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.run-button:hover {
  background-color: #45a049;
}

.run-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.language-selector {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.io-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-section,
.output-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 15px;
}

.input-section textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: monospace;
  resize: vertical;
}

.output-content {
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
  min-height: 100px;
  font-family: monospace;
  white-space: pre-wrap;
}

.output-content.error {
  color: #d32f2f;
  background-color: #ffebee;
}

.stats {
  margin-top: 10px;
  font-size: 12px;
  color: #666;
}

.test-cases {
  margin-top: 20px;
}

.test-case {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.test-case pre {
  margin: 5px 0 0 0;
  padding: 5px;
  background-color: white;
  border-radius: 3px;
}

h2,
h3 {
  color: #333;
  margin-top: 0;
}

.problem-content {
  line-height: 1.6;
}
</style>
