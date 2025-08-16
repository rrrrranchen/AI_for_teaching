<template>
  <!-- 面包屑导航 -->
  <a-breadcrumb>
    <template #separator>
      <right-outlined class="breadcrumb-sep-icon" />
    </template>
    <a-breadcrumb-item>
      <router-link to="/home/my-class" class="breadcrumb-link">
        <home-outlined class="breadcrumb-home-icon" />
        <span class="breadcrumb-text">我的课程</span>
      </router-link>
    </a-breadcrumb-item>
    <a-breadcrumb-item>
      <router-link
        class="breadcrumb-link"
        :to="{
          path: `/home/courseclass/${courseclassId}`,
        }"
        ><span class="breadcrumb-text">{{ courseclassName }}</span>
      </router-link>
    </a-breadcrumb-item>
    <a-breadcrumb-item>
      <span class="breadcrumb-current">{{ courseName }}</span>
    </a-breadcrumb-item>
  </a-breadcrumb>
  <div class="student-course-container">
    <!-- 标签页导航 -->
    <a-tabs
      v-model:activeKey="activeTab"
      @change="handleTabChange"
      class="custom-tabs"
    >
      <!-- 课前预习 -->
      <a-tab-pane key="pre" tab="课前预习">
        <question-list
          :key="'pre-' + courseId"
          :questions="preQuestions"
          :loading="loading"
          :deadline="previewDeadline"
          @submit="handlePreSubmit"
        />
      </a-tab-pane>

      <!-- 课后练习 -->
      <a-tab-pane key="post" tab="课后练习">
        <PostClassExercise
          :classId="courseclassId"
          :courseId="courseId"
          :deadline="postClassDeadline"
        />
      </a-tab-pane>

      <!-- 新增学习报告标签页 -->
      <a-tab-pane key="report" tab="学习报告">
        <div class="report-container">
          <div class="report-header">
            <a-button
              type="primary"
              @click="handleUpdateReport"
              :loading="updatingReport"
            >
              <sync-outlined />
              {{ reportData ? "更新报告" : "生成报告" }}
            </a-button>
          </div>

          <a-empty
            v-if="!reportData && !loadingReport"
            description="暂无学习报告"
          >
            <a-button type="primary" @click="handleUpdateReport">
              立即生成
            </a-button>
          </a-empty>

          <a-spin :spinning="loadingReport">
            <div
              v-if="reportData"
              class="markdown-content"
              v-html="renderedReport"
            />
          </a-spin>
        </div>
      </a-tab-pane>
      <!-- 新增推荐资源标签页 -->
      <a-tab-pane key="recommend" tab="推荐资源">
        <StudentVideoRecommend :courseId="courseId" />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { message } from "ant-design-vue";
import { questionApi, type Question } from "@/api/questions";
import { getCourseDetail } from "@/api/course";
import {
  addStudentAnswers,
  type AddAnswersParams,
  getStudentCourseReport,
  updateStudentCourseReport,
} from "@/api/studentanswer";
import QuestionList from "@/components/StudentQuestionList.vue";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";
import {
  SyncOutlined,
  HomeOutlined,
  RightOutlined,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import dayjs from "dayjs";
import PostClassExercise from "@/components/studentcourse/PostExercise.vue";
import StudentVideoRecommend from "@/components/studentcourse/StudentVideoRecommend.vue";

// 初始化Markdown解析器
const md: any = new MarkdownIt({
  html: true,
  linkify: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (err) {
        console.log(err);
      }
    }
    return "";
  },
});

export interface AnswerItem {
  questionId: number;
  answer: string;
}

export default defineComponent({
  name: "StudentCourseDetail",
  components: {
    QuestionList,
    SyncOutlined,
    PostClassExercise,
    HomeOutlined,
    RightOutlined,
    StudentVideoRecommend,
  },
  setup() {
    const route = useRoute();
    const courseId = ref<number>(0);
    const courseName = ref((route.query.courseName as string) || "未知课程");
    const courseclassId = ref<number>(0);
    const courseclassName = ref(
      (route.query.courseclassName as string) || "未知班级"
    );

    // 截止时间状态
    const previewDeadline = ref<string | null>(null);
    const postClassDeadline = ref<string | null>(null);

    // 题目数据
    const preQuestions = ref<Question[]>([]);
    const postQuestions = ref<Question[]>([]);
    const loading = ref(false);
    const activeTab = ref("pre");
    // 加载题目数据
    const loadQuestions = async () => {
      try {
        loading.value = true;
        const [preRes, postRes, courseDetail] = await Promise.all([
          questionApi.getPreQuestions(courseId.value),
          questionApi.getPostQuestions(courseId.value),
          getCourseDetail(courseId.value), // 新增获取课程详情
        ]);
        console.log("截止时间：", courseDetail);
        // 存储截止时间
        if (courseDetail.preview_deadline != undefined)
          previewDeadline.value = courseDetail.preview_deadline.$date;
        if (courseDetail.post_class_deadline != undefined)
          postClassDeadline.value = courseDetail.post_class_deadline.$date;

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
        // 获取当前类型的截止时间
        const deadline =
          type === "pre" ? previewDeadline.value : postClassDeadline.value;

        // 最终时间验证
        if (dayjs().isAfter(dayjs(deadline))) {
          message.error("已超过截止时间，无法提交");
          return;
        }

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
        await loadReport(); // 加载时获取报告
      } catch (err) {
        message.error("初始化失败");
        console.error("初始化错误:", err);
      }
    });

    // 原有状态变量保持不变...
    const authStore = useAuthStore();
    const reportData = ref<string | null>(null);
    const renderedReport = ref("");
    const loadingReport = ref(false);
    const updatingReport = ref(false);

    // 加载学习报告
    const loadReport = async () => {
      try {
        loadingReport.value = true;
        const { data } = await getStudentCourseReport(
          authStore.user?.id || 0,
          courseId.value
        );
        reportData.value = data.markdown_report;
        renderedReport.value = md.render(reportData.value || "");
      } catch (error) {
        message.error("加载报告失败");
      } finally {
        loadingReport.value = false;
      }
    };

    // 更新学习报告
    const handleUpdateReport = async () => {
      try {
        updatingReport.value = true;
        const { data } = await updateStudentCourseReport(
          authStore.user?.id || 0,
          courseId.value
        );
        reportData.value = data.markdown_report;
        renderedReport.value = md.render(reportData.value);
        message.success("报告更新成功");
      } catch (error) {
        message.error("报告更新失败");
      } finally {
        updatingReport.value = false;
      }
    };

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
      reportData,
      renderedReport,
      loadingReport,
      updatingReport,
      handleUpdateReport,
      previewDeadline,
      postClassDeadline,
    };
  },
});
</script>

<style scoped>
/* 原有样式保持不变 */
.custom-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}

.custom-tabs :deep(.ant-tabs-tab) {
  padding: 12px 24px;
  font-weight: 500;
}

.custom-tabs :deep(.ant-tabs-tab-active) {
  color: #1677ff;
}
/* 面包屑导航样式 */
.breadcrumb-link {
  height: 30px;
  display: inline-flex;
  align-items: center;
  color: #1677ff;
  padding: 10px 16px;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f7ff 100%);
  border: 1px solid #c8e5fb;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.12);
}

.breadcrumb-link:hover {
  color: #0958d9;
}

.breadcrumb-home-icon {
  font-size: 14px;
  margin-right: 6px;
}

.breadcrumb-sep-icon {
  color: #8c8c8c;
  font-size: 12px;
}

.breadcrumb-text {
  font-weight: 500;
}

.breadcrumb-current {
  height: 30px;
  display: inline-flex;
  align-items: center;
  padding: 10px 16px;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f7ff 100%);
  border: 1px solid #c8e5fb;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.12);
  font-weight: 600;
  color: #1d2129;
}

/* 面包屑导航样式 */
.ant-breadcrumb {
  padding-top: 16px;
  padding-left: 24px; /* 上下间距和左间距 */
  font-size: 16px; /* 字体大小 */
  line-height: 1.5;
}

.ant-breadcrumb a {
  transition: color 0.3s;
  color: #1890ff; /* 链接颜色 */
}

.ant-breadcrumb a:hover {
  color: #40a9ff !important; /* 鼠标悬停时的颜色 */
}

.ant-breadcrumb > span:last-child {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85); /* 当前页面颜色 */
}

.ant-tabs {
  padding: 16px;
}

/* 添加报告样式 */
.report-container {
  padding: 16px;
  background: #fbfaef;
  border: 5px solid #fcf9d3;
  border-radius: 8px;
  min-height: 500px;
}

.report-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.empty-report {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

/* 解决方案2：弹性布局滚动（推荐） */

.markdown-content {
  flex: 1;
  overflow-y: auto;
  max-height: 50vh; /* 根据视口高度自动调整 */
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

/* 通用代码块滚动处理 */
.markdown-content :deep() pre {
  max-width: 100%;
  overflow-x: auto;
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
}
.recommend-container {
  padding: 24px;
  background: rgb(255, 255, 255);
  border-radius: 8px;
}

.recommend-section {
  height: 600px;
  display: flex;
  flex-direction: column;
  background-color: #fcfadf;
  border: 5px solid #fcf9d3;
  border-radius: 8px;
  padding: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
