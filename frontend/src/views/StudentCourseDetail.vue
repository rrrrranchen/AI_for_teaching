<template>
  <!-- 面包屑导航 -->
  <div class="breadcrumb-section">
    <a-breadcrumb separator=">">
      <a-breadcrumb-item>
        <router-link to="/home/my-class">我的课程</router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item>
        <router-link
          :to="{
            path: `/home/s-courseclass/${courseclassId}`,
          }"
          >{{ courseclassName }}</router-link
        >
      </a-breadcrumb-item>
      <a-breadcrumb-item>{{ courseName }}</a-breadcrumb-item>
    </a-breadcrumb>
  </div>
  <div class="student-course-container">
    <!-- 标签页导航 -->
    <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
      <!-- 课前预习 -->
      <a-tab-pane key="pre" tab="课前预习">
        <question-list
          :key="'pre-' + courseId"
          :questions="preQuestions"
          :loading="loading"
          @submit="handlePreSubmit"
        />
      </a-tab-pane>

      <!-- 课后练习 -->
      <a-tab-pane key="post" tab="课后练习">
        <question-list
          :key="'post-' + courseId"
          :questions="postQuestions"
          :loading="loading"
          @submit="handlePostSubmit"
        />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { message } from "ant-design-vue";
import { questionApi, type Question } from "@/api/questions";
import { addStudentAnswers, type AddAnswersParams } from "@/api/studentanswer";
import QuestionList from "@/components/StudentQuestionList.vue";

export interface AnswerItem {
  questionId: number;
  answer: string;
}

export default defineComponent({
  name: "StudentCourseDetail",
  components: { QuestionList },
  setup() {
    const route = useRoute();
    const courseId = ref<number>(0);
    const courseName = ref((route.query.courseName as string) || "未知课程");
    const courseclassId = ref<number>(0);
    const courseclassName = ref(
      (route.query.courseclassName as string) || "未知班级"
    );

    // 题目数据
    const preQuestions = ref<Question[]>([]);
    const postQuestions = ref<Question[]>([]);
    const loading = ref(false);
    const activeTab = ref("pre");

    // 加载题目数据
    const loadQuestions = async () => {
      try {
        loading.value = true;
        const [preRes, postRes] = await Promise.all([
          questionApi.getPreQuestions(courseId.value),
          questionApi.getPostQuestions(courseId.value),
        ]);
        preQuestions.value = preRes.filter((q) => q.is_public);
        postQuestions.value = postRes.filter((q) => q.is_public);
      } catch (error) {
        message.error("题目加载失败");
      } finally {
        loading.value = false;
      }
    };

    // 处理标签切换
    const handleTabChange = () => {
      // 切换时重置滚动位置等（可根据需要扩展）
    };

    // 处理课前提交
    const handlePreSubmit = async (answers: AnswerItem[]) => {
      await handleSubmit(answers, "pre");
    };

    // 处理课后提交
    const handlePostSubmit = async (answers: AnswerItem[]) => {
      await handleSubmit(answers, "post");
    };

    // 统一提交处理
    const handleSubmit = async (
      answers: AnswerItem[],
      type: "pre" | "post"
    ) => {
      try {
        const params: AddAnswersParams = {
          courseclass_id: courseclassId.value,
          answers: answers.map((a) => ({
            question_id: a.questionId,
            answer: a.answer,
          })),
        };

        await addStudentAnswers(params);
        message.success(
          `已提交${type === "pre" ? "课前" : "课后"} ${answers.length} 个答案`
        );
        loadQuestions();
      } catch (error) {
        message.error("提交失败");
      }
    };

    onMounted(async () => {
      try {
        const id = Number(route.params.courseId);
        if (isNaN(id)) throw new Error("无效的课程ID");
        courseId.value = id;
        courseclassId.value = Number(route.query.courseclassId);
        await loadQuestions();
      } catch (err) {
        message.error("初始化失败");
        console.error("初始化错误:", err);
      }
    });

    return {
      courseName,
      courseId,
      courseclassId,
      courseclassName,
      preQuestions,
      postQuestions,
      loading,
      activeTab,
      handleTabChange,
      handlePreSubmit,
      handlePostSubmit,
    };
  },
});
</script>

<style scoped>
/* 原有样式保持不变 */
.student-course-container {
  margin: 0 auto;
  padding: 20px;
}

.ant-breadcrumb {
  padding: 16px 24px;
  font-size: 16px;
  line-height: 1.5;
  margin-bottom: 10px;
}

.ant-breadcrumb a {
  transition: color 0.3s;
  color: #1890ff;
}

.ant-breadcrumb a:hover {
  color: #40a9ff !important;
}

.ant-breadcrumb > span:last-child {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.ant-tabs {
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
