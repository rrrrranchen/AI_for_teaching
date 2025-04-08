<template>
  <div class="course-detail">
    <!-- 课程简介 -->
    <a-card title="课程简介" class="course-info">
      <p>{{ courseDescription }}</p>
    </a-card>

    <!-- 题目列表 -->
    <a-list :data-source="publicQuestions" item-layout="vertical">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-card hoverable>
            <a-card-meta :title="`题目 ${item.id}`">
              <template #description>
                <div class="question-content">
                  <p>类型：{{ (questionTypeMap as any)[item.type] }}</p>
                  <p>难度：{{ (difficultyMap as any)[item.difficulty] }}</p>
                  <div v-html="parseQuestionContent(item.content)"></div>
                </div>

                <a-collapse v-if="item.type === 'choice'">
                  <a-collapse-panel key="1" header="查看选项">
                    <ul>
                      <li
                        v-for="(option, index) in parseChoiceOptions(
                          item.content
                        )"
                        :key="index"
                      >
                        {{ option }}
                      </li>
                    </ul>
                  </a-collapse-panel>
                </a-collapse>
              </template>
            </a-card-meta>

            <div class="correct-answer">
              <a-divider />
              <h4>正确答案：</h4>
              <p>{{ item.correct_answer }}</p>
            </div>
          </a-card>
        </a-list-item>
      </template>
    </a-list>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { message } from "ant-design-vue";
import { questionApi } from "@/api/questions";
import type { Question } from "@/api/questions";

export default defineComponent({
  name: "StudentCourseDetail",
  setup() {
    const route = useRoute();
    const courseId = parseInt(route.params.course_id as string);

    const publicQuestions = ref<Question[]>([]);
    const courseDescription = ref("");

    interface QuestionTypeMap {
      choice: string;
      fill: string;
      short_answer: string;
      [key: string]: string; // 添加索引签名
    }

    interface DifficultyMap {
      1: string;
      2: string;
      3: string;
      4: string;
      5: string;
      [key: number]: string; // 添加索引签名
    }

    const questionTypeMap: QuestionTypeMap = {
      choice: "选择题",
      fill: "填空题",
      short_answer: "简答题",
    };

    const difficultyMap: DifficultyMap = {
      1: "简单",
      2: "较易",
      3: "中等",
      4: "较难",
      5: "困难",
    };

    // 使用时的类型安全
    const getQuestionType = (type: keyof QuestionTypeMap) => {
      return questionTypeMap[type];
    };

    const getDifficulty = (level: keyof DifficultyMap) => {
      return difficultyMap[level];
    };

    const parseQuestionContent = (content: string) => {
      return content.replace(/\n/g, "<br>");
    };

    const parseChoiceOptions = (content: string) => {
      try {
        const match = content.match(/options":\s*(\[.*?\])/);
        return match ? JSON.parse(match[1]) : [];
      } catch {
        return [];
      }
    };

    const loadQuestions = async () => {
      try {
        const response = await questionApi.getPreQuestions(courseId);
        publicQuestions.value = response.filter((q: any) => q.is_public);
        if (publicQuestions.value.length > 0) {
          courseDescription.value =
            publicQuestions.value[0].content.split("\n")[0];
        }
      } catch (error) {
        message.error("题目加载失败");
      }
    };

    onMounted(() => {
      loadQuestions();
    });

    return {
      courseDescription,
      publicQuestions,
      questionTypeMap,
      difficultyMap,
      getQuestionType,
      getDifficulty,
      parseQuestionContent,
      parseChoiceOptions,
    };
  },
});
</script>

<style scoped>
.course-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.course-info {
  margin-bottom: 24px;
}

.question-content {
  margin: 12px 0;
}

.correct-answer {
  margin-top: 16px;
  padding: 12px;
  background-color: #f6ffed;
  border-radius: 4px;
}

.ant-list-item {
  padding: 0 !important;
  margin-bottom: 16px;
}
</style>
