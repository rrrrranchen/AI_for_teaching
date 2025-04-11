<template>
  <div class="question-list">
    <a-spin :spinning="loading">
      <a-empty v-if="filteredQuestions.length === 0" description="暂无题目" />

      <div v-else class="question-container">
        <!-- 当前题目显示 -->
        <div class="current-question">
          <a-card :title="`题目 ${currentIndex + 1}`">
            <!-- 题目内容 -->
            <div class="question-content">
              <div class="meta-info">
                <a-tag color="blue">{{
                  questionTypeMap[currentQuestion.type]
                }}</a-tag>
                <a-rate :value="Number(currentQuestion.difficulty)" disabled />
              </div>

              <!-- 解析后的内容 -->
              <div class="content-box">
                <div
                  class="question-text"
                  v-html="parseContent(parsedContent.question)"
                />

                <!-- 选择题选项 -->
                <a-radio-group
                  v-if="currentQuestion.type === 'choice'"
                  v-model:value="currentAnswer"
                  :disabled="!!currentQuestion.studentAnswer"
                >
                  <a-radio
                    v-for="(option, index) in parsedContent.options"
                    :key="index"
                    :value="String.fromCharCode(65 + index)"
                    class="option-item"
                  >
                    {{ option }}
                  </a-radio>
                </a-radio-group>

                <!-- 其他题型 -->
                <template v-else>
                  <a-textarea
                    v-if="!currentQuestion.studentAnswer"
                    v-model:value="currentAnswer"
                    :placeholder="'请输入答案'"
                    :rows="currentQuestion.type === 'short_answer' ? 4 : 2"
                  />

                  <div v-else class="submitted-answer">
                    <a-alert
                      :message="`你的答案：${currentQuestion.studentAnswer.answer}`"
                      type="info"
                      show-icon
                    />
                    <div class="correct-answer">
                      <span>正确答案：</span>
                      <pre>{{ currentQuestion.correct_answer }}</pre>
                    </div>
                    <a-progress
                      :percent="
                        currentQuestion.studentAnswer.correct_percentage
                      "
                      status="active"
                      class="progress-bar"
                    />
                  </div>
                </template>
              </div>
            </div>

            <!-- 导航按钮 -->
            <template #actions>
              <div class="navigation-buttons">
                <a-button @click="prevQuestion" :disabled="currentIndex === 0">
                  上一题
                </a-button>

                <a-button
                  v-if="!isLastQuestion"
                  type="primary"
                  @click="nextQuestion"
                  :disabled="!isAnswerValid"
                >
                  下一题
                </a-button>

                <a-button
                  v-else
                  type="primary"
                  @click="submitAnswers"
                  :disabled="!isAnswerValid"
                >
                  提交答案
                </a-button>
              </div>
            </template>
          </a-card>
        </div>

        <!-- 进度指示 -->
        <div class="progress-indicator">
          当前进度：{{ currentIndex + 1 }}/{{ filteredQuestions.length }}
        </div>
      </div>
    </a-spin>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref, computed, watch } from "vue";
import { Question } from "@/api/questions";

export default defineComponent({
  name: "StudentQuestionList",
  props: {
    questions: {
      type: Array as PropType<Question[]>,
      required: true,
    },
    loading: Boolean,
  },
  emits: ["submit", "update-answer"],

  setup(props, { emit }) {
    const currentIndex = ref(0);
    const currentAnswer = ref("");
    const answersCache = ref<Record<number, string>>({});

    // 过滤已提交的题目
    const filteredQuestions = computed(() =>
      props.questions.filter((q) => !q.studentAnswer)
    );

    // 解析题目内容
    const parsedContent = computed(() => {
      try {
        const question = filteredQuestions.value[currentIndex.value];
        if (question?.type === "choice") {
          return JSON.parse(question.content);
        }
        return {
          question: question?.content || "",
          options: [],
        };
      } catch (e) {
        return { question: "题目解析错误", options: [] };
      }
    });

    // 当前题目对象
    const currentQuestion = computed(
      () => filteredQuestions.value[currentIndex.value]
    );

    // 答案有效性检查
    const isAnswerValid = computed(() => currentAnswer.value.trim().length > 0);

    // 是否是最后一题
    const isLastQuestion = computed(
      () => currentIndex.value === filteredQuestions.value.length - 1
    );

    // 导航方法
    const prevQuestion = () => {
      if (currentIndex.value > 0) {
        currentIndex.value--;
        currentAnswer.value =
          answersCache.value[currentQuestion.value.id] || "";
      }
    };

    const nextQuestion = () => {
      if (currentIndex.value < filteredQuestions.value.length - 1) {
        saveAnswer();
        currentIndex.value++;
        currentAnswer.value =
          answersCache.value[currentQuestion.value.id] || "";
      }
    };

    // 保存答案到缓存
    const saveAnswer = () => {
      if (currentAnswer.value.trim()) {
        answersCache.value[currentQuestion.value.id] = currentAnswer.value;
        emit("update-answer", {
          questionId: currentQuestion.value.id,
          answer: currentAnswer.value,
        });
      }
    };

    // 提交所有答案
    const submitAnswers = () => {
      saveAnswer();
      const answers = Object.entries(answersCache.value).map(
        ([id, answer]) => ({
          questionId: Number(id),
          answer,
        })
      );
      emit("submit", answers);
    };

    // 当题目变化时重置答案
    watch(currentQuestion, (newVal) => {
      currentAnswer.value = answersCache.value[newVal?.id] || "";
    });

    return {
      currentIndex,
      currentAnswer,
      parsedContent,
      currentQuestion,
      isLastQuestion,
      isAnswerValid,
      filteredQuestions,
      prevQuestion,
      nextQuestion,
      submitAnswers,
      questionTypeMap: {
        choice: "选择题",
        fill: "填空题",
        short_answer: "简答题",
      },
      parseContent: (text: string) => text.replace(/\n/g, "<br>"),
    };
  },
});
</script>

<style scoped>
.question-container {
  position: relative;
  max-width: 800px;
  margin: 0 auto;
}

.current-question {
  margin-bottom: 24px;
}

.navigation-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 0;
}

.option-item {
  display: block;
  margin: 8px 0;
  height: 32px;
  line-height: 32px;
}

.progress-indicator {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 16px;
}

.question-text {
  margin-bottom: 16px;
  font-size: 16px;
  line-height: 1.6;
}

.submitted-answer {
  margin-top: 16px;
}

.correct-answer {
  background: #f6ffed;
  padding: 12px;
  border-radius: 4px;
  margin-top: 16px;
}

.correct-answer pre {
  margin: 0;
  white-space: pre-wrap;
}

.progress-bar {
  margin-top: 16px;
}

.content-box {
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
}
</style>
