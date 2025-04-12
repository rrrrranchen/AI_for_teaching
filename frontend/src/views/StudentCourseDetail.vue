<template>
  <!-- 面包屑导航 -->
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
        <div class="recommend-container">
          <a-row :gutter="24">
            <!-- 课前推荐 -->
            <a-col :span="12">
              <div class="recommend-section">
                <div class="section-header">
                  <h3>课前推荐资源</h3>
                  <a-button
                    v-if="!preRecommendations.length"
                    type="primary"
                    @click="generatePreRecommend"
                    :loading="generatingPre"
                  >
                    生成课前推荐
                  </a-button>
                </div>

                <a-spin :spinning="loadingPre">
                  <a-empty
                    v-if="!preRecommendations.length && !loadingPre"
                    description="暂无课前推荐"
                  />
                  <div
                    v-else
                    class="markdown-content"
                    v-html="renderedPreRecommend"
                  />
                </a-spin>
              </div>
            </a-col>

            <!-- 课后推荐 -->
            <a-col :span="12">
              <div class="recommend-section">
                <div class="section-header">
                  <h3>课后推荐资源</h3>
                  <a-button
                    v-if="!postRecommendations.length"
                    type="primary"
                    @click="generatePostRecommend"
                    :loading="generatingPost"
                  >
                    生成课后推荐
                  </a-button>
                </div>

                <a-spin :spinning="loadingPost">
                  <a-empty
                    v-if="!postRecommendations.length && !loadingPost"
                    description="暂无课后推荐"
                  />
                  <div
                    v-else
                    class="markdown-content"
                    v-html="renderedPostRecommend"
                  />
                </a-spin>
              </div>
            </a-col>
          </a-row>
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { message } from "ant-design-vue";
import { questionApi, type Question } from "@/api/questions";
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
import { SyncOutlined } from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import {
  generatePreClassRecommendations,
  getPreClassRecommendations,
  generatePostClassRecommendations,
  getPostClassRecommendations,
} from "@/api/student_recommend";

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
  components: { QuestionList, SyncOutlined },
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
        await loadReport(); // 加载时获取报告
        await loadPreRecommendations();
        await loadPostRecommendations();
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

    // 新增推荐资源相关状态
    const preRecommendations = ref<any[]>([]);
    const postRecommendations = ref<any[]>([]);
    const loadingPre = ref(false);
    const loadingPost = ref(false);
    const generatingPre = ref(false);
    const generatingPost = ref(false);

    // 计算渲染后的Markdown内容
    const renderedPreRecommend = computed(() =>
      preRecommendations.value.map((r) => md.render(r.content)).join("<hr>")
    );

    const renderedPostRecommend = computed(() =>
      postRecommendations.value.map((r) => md.render(r.content)).join("<hr>")
    );

    // 获取推荐资源
    const loadPreRecommendations = async () => {
      try {
        loadingPre.value = true;
        preRecommendations.value = await getPreClassRecommendations(
          courseId.value
        );
      } catch (err) {
        message.error("获取课前推荐失败");
      } finally {
        loadingPre.value = false;
      }
    };

    const loadPostRecommendations = async () => {
      try {
        loadingPost.value = true;
        postRecommendations.value = await getPostClassRecommendations(
          courseId.value
        );
      } catch (err) {
        message.error("获取课后推荐失败");
      } finally {
        loadingPost.value = false;
      }
    };

    // 生成推荐资源
    const generatePreRecommend = async () => {
      try {
        generatingPre.value = true;
        await generatePreClassRecommendations(courseId.value);
        await loadPreRecommendations();
        message.success("课前推荐生成成功");
      } catch (err) {
        message.error("生成失败");
      } finally {
        generatingPre.value = false;
      }
    };

    const generatePostRecommend = async () => {
      try {
        generatingPost.value = true;
        await generatePostClassRecommendations(courseId.value);
        await loadPostRecommendations();
        message.success("课后推荐生成成功");
      } catch (err) {
        message.error("生成失败");
      } finally {
        generatingPost.value = false;
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
      preRecommendations,
      postRecommendations,
      renderedPreRecommend,
      renderedPostRecommend,
      loadingPre,
      loadingPost,
      generatingPre,
      generatingPost,
      generatePreRecommend,
      generatePostRecommend,
    };
  },
});
</script>

<style scoped>
/* 原有样式保持不变 */
.student-course-container {
}

.ant-breadcrumb {
  padding: 16px 24px;
  font-size: 16px;
  line-height: 1.5;
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
  max-height: 70vh; /* 根据视口高度自动调整 */
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
