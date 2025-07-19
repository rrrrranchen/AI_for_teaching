<template>
  <div class="class-container">
    <div class="class-card">
      <!-- 面包屑导航 -->
      <div class="breadcrumb-section">
        <a-breadcrumb separator=">">
          <a-breadcrumb-item>
            <router-link to="/home/my-class">我的课程</router-link>
          </a-breadcrumb-item>
          <a-breadcrumb-item>{{
            courseclassDetail?.name || "加载中..."
          }}</a-breadcrumb-item>
        </a-breadcrumb>
      </div>

      <!-- 加载状态 -->
      <a-spin
        v-if="loading"
        class="w-full flex justify-center py-8"
        size="large"
      />

      <!-- 错误状态 -->
      <a-result
        v-else-if="error"
        status="error"
        :title="error"
        sub-title="请刷新页面或稍后再试"
      />

      <!-- 内容区域 -->
      <div v-else class="class-content">
        <!-- 头部信息区 -->
        <div class="class-header">
          <div class="class-image-container">
            <img
              v-if="courseclassDetail?.image_path"
              :src="'http://localhost:5000/' + courseclassDetail.image_path"
              alt="班级图片"
              class="class-image"
            />
            <div v-else class="class-image-placeholder">
              <book-outlined class="placeholder-icon" />
            </div>
          </div>
          <div class="class-basic">
            <div
              style="
                font-weight: bold;
                font-size: 36px;
                margin-left: 10px;
                margin-bottom: 20px;
              "
            >
              {{ courseclassDetail?.name || "加载中..." }}
            </div>
            <div class="class-meta">
              <p class="class-description">
                <calendar-outlined /> 创建时间：{{
                  formatCreatedAt(courseclassDetail?.created_at)
                }}
              </p>
              <p class="class-description">
                <BookOutlined />
                {{ courseclassDetail?.description || "暂无班级描述" }}
              </p>
            </div>
          </div>

          <!-- 任课教师 -->
          <div class="teacher-section">
            <h3>任课教师</h3>
            <a-space wrap>
              <div class="flex flex-row items-center">
                <a-avatar
                  v-if="
                    courseclassDetail?.teachers &&
                    courseclassDetail?.teachers.length > 0
                  "
                  size="large"
                  :src="
                    'http://localhost:5000/' +
                      courseclassDetail.teachers[0].avatar ||
                    '/default-avatar.png'
                  "
                  class="text-lg bg-blue-100 p-2 rounded-full"
                />
                <p
                  v-if="
                    courseclassDetail?.teachers &&
                    courseclassDetail?.teachers.length > 0
                  "
                  style="font-size: large"
                >
                  {{ courseclassDetail?.teachers[0]?.username }}
                </p>
              </div>
            </a-space>
          </div>
        </div>

        <!-- 标签页区域 -->
        <div class="class-tabs">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="courses" tab="课程章节管理">
              <!-- 课程管理内容 -->
              <div class="tab-content">
                <div class="action-bar">
                  <a-input-search
                    v-model:value="searchCourseKey"
                    placeholder="搜索课程"
                    class="custom-search-input"
                  >
                    <template #enterButton>
                      <a-button type="primary" class="search-button">
                        <template #icon><search-outlined /></template>
                        搜索
                      </a-button>
                    </template>
                  </a-input-search>
                </div>

                <!-- 改进后的课程列表 -->
                <div class="course-list-container">
                  <a-empty
                    v-if="filteredCourses.length === 0"
                    description="暂无课程章节"
                    class="empty-placeholder"
                  />

                  <div v-else class="course-timeline-container">
                    <!-- 时间轴 -->
                    <div class="timeline-line"></div>

                    <!-- 课程时间轴列表 -->
                    <div class="course-timeline-list">
                      <div
                        v-for="(course, index) in filteredCourses"
                        :key="course.id"
                        class="course-timeline-item"
                        :style="{ '--index': index }"
                      >
                        <!-- 时间节点 -->
                        <div class="timeline-node">
                          <div class="node-dot"></div>
                          <div class="node-date"></div>
                        </div>

                        <!-- 课程卡片 -->
                        <div
                          class="course-card"
                          @click="handleCourseClick(course.id, course.name)"
                        >
                          <div class="course-card-header">
                            <h3 class="course-title">{{ course.name }}</h3>
                          </div>
                          <p class="course-description">
                            {{ course.description || "暂无课程描述" }}
                          </p>
                          <div class="course-meta">
                            <span class="create-time">
                              <calendar-outlined />
                              {{ formatCreatedAt(course.created_at) }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </a-tab-pane>

            <a-tab-pane key="students" tab="学生管理">
              <!-- 学生管理内容 -->
              <div class="tab-content">
                <div class="action-bar">
                  <a-input-search
                    v-model:value="searchStudentKey"
                    placeholder="搜索学生"
                    class="custom-search-input"
                  >
                    <template #enterButton>
                      <a-button type="primary" class="search-button">
                        <template #icon><search-outlined /></template>
                        搜索
                      </a-button>
                    </template>
                  </a-input-search>
                </div>

                <!-- 改进后的学生列表 -->
                <div class="student-list-container">
                  <a-empty
                    v-if="filteredStudents.length === 0"
                    description="暂无学生"
                    class="empty-placeholder"
                  />

                  <div class="student-table">
                    <div class="student-table-header">
                      <div class="header-cell" style="flex: 2">学生姓名</div>
                    </div>

                    <div
                      v-for="student in filteredStudents"
                      :key="student.id"
                      class="student-table-row"
                    >
                      <div class="student-cell" style="flex: 2">
                        <a-avatar
                          v-if="student?.avatar"
                          :src="'http://localhost:5000/' + student?.avatar"
                        >
                        </a-avatar>
                        <a-avatar v-else>
                          <UserOutlined />
                        </a-avatar>
                        <span class="student-name">{{ student.username }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="report" tab="我的学习报告">
              <!-- 报告内容区域 -->
              <div class="report-container">
                <div class="report-header">
                  <a-button
                    type="primary"
                    @click="handleUpdateMyReport"
                    :loading="updatingReport"
                  >
                    <sync-outlined />
                    {{ myReport ? "更新报告" : "生成报告" }}
                  </a-button>
                </div>

                <div v-if="!myReport" class="empty-report">
                  <a-empty description="暂无学习报告">
                    <a-button type="primary" @click="handleUpdateMyReport">
                      立即生成
                    </a-button>
                  </a-empty>
                </div>

                <div
                  v-else
                  id="myReportViewer"
                  class="markdown-content"
                  v-html="renderedReport"
                  style="background: white; padding: 16px"
                ></div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from "vue";
import { message } from "ant-design-vue";
import { useRouter, useRoute } from "vue-router";
import {
  getCourseclassDetail,
  getStudentsByCourseclass,
} from "@/api/courseclass";
import { getCoursesByCourseclass, createCourseForClass } from "@/api/course";
import type { Courseclass, Student, MongoDate } from "@/api/courseclass";
import type { Course } from "@/api/course";
import {
  UserOutlined,
  CalendarOutlined,
  BookOutlined,
  SyncOutlined,
  SearchOutlined,
} from "@ant-design/icons-vue";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";
import {
  getStudentClassReport,
  updateStudentClassReport,
} from "@/api/studentanswer";
import { useAuthStore } from "@/stores/auth";

export default defineComponent({
  name: "CourseClassDetail",
  components: {
    UserOutlined,
    CalendarOutlined,
    BookOutlined,
    SyncOutlined,
    SearchOutlined,
  },
  setup() {
    const route = useRoute();
    const courseclassId = ref<number>(0);
    const courseclassDetail = ref<Courseclass | null>(null);
    const courses = ref<Course[]>([]);
    const students = ref<Student[]>([]);
    const loading = ref<boolean>(true);
    const error = ref<string | null>(null);
    const newCourseName = ref<string>("");
    const newCourseDescription = ref<string>("");
    const activeTab = ref("courses");
    const multiSelecting = ref(false);
    const searchCourseKey = ref("");
    const searchStudentKey = ref("");
    const createVisible = ref(false);
    const creating = ref(false);
    const newCourse = ref({ name: "", description: "" });
    const router = useRouter();

    const myReport = ref<string | null>(null);
    const updatingReport = ref(false);
    const authStore = useAuthStore();
    // 在setup中添加
    const md: any = new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
      highlight: function (str, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return (
              '<pre class="hljs"><code>' +
              hljs.highlight(str, { language: lang, ignoreIllegals: true })
                .value +
              "</code></pre>"
            );
          } catch (err) {
            console.log(err);
          }
        }
        return (
          '<pre class="hljs"><code>' +
          md.utils.escapeHtml(str) +
          "</code></pre>"
        );
      },
    });

    // 添加渲染后的报告内容
    const renderedReport = ref<string>("");
    // 获取报告数据
    const loadMyReport = async () => {
      try {
        const { data } = await getStudentClassReport(
          authStore.user?.id || 0,
          courseclassId.value
        );
        myReport.value = data.markdown_report;
        console.log("....", myReport.value);
        renderedReport.value = md.render(myReport.value || "");
        console.log("....", renderedReport.value);
      } catch (error) {
        message.error("获取报告失败");
      }
    };

    // 更新报告
    const handleUpdateMyReport = async () => {
      try {
        updatingReport.value = true;
        const { data } = await updateStudentClassReport(
          authStore.user?.id || 0,
          courseclassId.value
        );
        myReport.value = data.markdown_report;
        renderedReport.value = md.render(myReport.value);
        message.success("报告更新成功");
      } catch (error) {
        message.error("报告更新失败");
      } finally {
        updatingReport.value = false;
      }
    };

    const handleCourseClick = (courseId: number, courseName: string) => {
      router.push({
        path: `/home/s-course/${courseId}`,
        query: {
          courseclassName: courseclassDetail.value?.name || "未知班级",
          courseclassId: courseclassId.value,
          courseName: courseName,
        },
      });
    };

    // 修改filteredCourses计算属性，按创建时间倒序排列
    const filteredCourses = computed(() => {
      return courses.value
        .filter((c) =>
          c.name.toLowerCase().includes(searchCourseKey.value.toLowerCase())
        )
        .sort((a, b) => {
          const dateA = new Date(a.created_at).getTime();
          const dateB = new Date(b.created_at).getTime();
          return dateA - dateB; // 最新在上
        });
    });

    const filteredStudents = computed(() => {
      return students.value.filter((s) =>
        s.username.toLowerCase().includes(searchStudentKey.value.toLowerCase())
      );
    });

    // 获取课程班详情
    const fetchCourseclassDetail = async () => {
      try {
        const response = await getCourseclassDetail(courseclassId.value);
        courseclassDetail.value = response;
      } catch (err) {
        error.value = "获取课程班详情失败";
        console.error(err);
      }
    };

    // 获取课程班的课程列表
    const fetchCourses = async () => {
      try {
        const response = await getCoursesByCourseclass(courseclassId.value);
        courses.value = response;
      } catch (err) {
        error.value = "获取课程列表失败";
        console.error(err);
      }
    };

    // 获取课程班的学生列表
    const fetchStudents = async () => {
      try {
        const response = await getStudentsByCourseclass(courseclassId.value);
        students.value = response.students;
      } catch (err) {
        error.value = "获取学生列表失败";
        console.error(err);
      }
    };

    // 页面加载时获取数据
    onMounted(async () => {
      try {
        loading.value = true;
        courseclassId.value = parseInt(route.params.id as string);
        await Promise.all([
          fetchCourseclassDetail(),
          fetchCourses(),
          fetchStudents(),
        ]);
        await loadMyReport();
      } catch (err) {
        error.value = "加载数据失败，请稍后再试";
        console.error(err);
      } finally {
        loading.value = false;
      }
    });

    // 添加新课程
    const addNewCourse = async () => {
      // 验证输入是否为空
      if (!newCourse.value.name) {
        message.error("请输入课程名称");
        return;
      }

      try {
        creating.value = true; // 显示加载状态

        // 调用后端接口创建课程
        const newCourseData = await createCourseForClass(courseclassId.value, {
          name: newCourse.value.name,
          description: newCourse.value.description,
        });

        // 添加新课程到列表
        courses.value.push(newCourseData);

        // 显示成功提示
        message.success("课程创建成功");

        // 关闭模态框
        createVisible.value = false;
      } catch (error) {
        message.error("创建课程失败，请稍后再试");
      } finally {
        // 无论成功或失败，都重置加载状态
        creating.value = false;
      }
    };

    type CreatedAtType = string | MongoDate | Date | null | undefined;
    const formatCreatedAt = (date: CreatedAtType): string => {
      if (!date) return "未知时间";

      let dateStr: string;

      if (typeof date === "string") {
        dateStr = date;
      } else if ("$date" in date) {
        dateStr = date.$date;
      } else if (date instanceof Date) {
        dateStr = date.toISOString();
      } else {
        return "无效日期格式";
      }

      try {
        return new Date(dateStr).toLocaleString();
      } catch {
        return "无效日期格式";
      }
    };

    // 在setup()中添加formatTimelineDate方法
    const formatTimelineDate = (dateString: string): string => {
      console.log("时间", dateString);
      if (!dateString) return "";
      const date = new Date(dateString);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    };
    return {
      handleCourseClick,
      courseclassId,
      courseclassDetail,
      courses,
      students,
      loading,
      error,
      newCourseName,
      newCourseDescription,
      addNewCourse,
      activeTab,
      multiSelecting,
      searchCourseKey,
      searchStudentKey,
      createVisible,
      creating,
      newCourse,
      filteredCourses,
      filteredStudents,
      showCreateModal: () => (createVisible.value = true),
      formatCreatedAt,
      myReport,
      handleUpdateMyReport,
      updatingReport,
      renderedReport,
      formatTimelineDate,
    };
  },
});
</script>
<style scoped>
/* 面包屑导航样式 */
.ant-breadcrumb {
  padding: 16px 24px; /* 上下间距和左间距 */
  font-size: 16px; /* 字体大小 */
  line-height: 1.5;
  margin-bottom: 10px; /* 下间距 */
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

.class-container {
  background: inherit;
  min-height: calc(100vh - 64px);
  display: flex;
  justify-content: center;
}

.class-card {
  background: inherit;
  width: 100%;
  overflow: hidden;
}

.class-content {
  width: 80%;
  margin: 0 auto;
}

.class-header {
  padding: 12px 0;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  border-bottom: 1px solid #f0f2f5;
}

.class-info-section {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.class-basic {
  flex: 1;
  min-width: 300px;
}

.class-title {
  font-weight: 600;
  font-size: 28px;
  color: #1d2129;
  margin-bottom: 16px;
}

.class-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.invite-code {
  margin-top: 8px;
  max-width: 300px;
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s;
}

.invite-code:hover {
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
  transform: translateY(-1px);
}

.class-description-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4e5969;
  font-size: 14px;
  line-height: 1.6;
}

.meta-icon {
  color: #86909c;
}

.teacher-section {
  min-width: 200px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #1d2129;
  margin-bottom: 12px;
}

.teacher-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.teacher-card:hover {
  background: #e6f4ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.teacher-actions {
  align-self: flex-start;
}

.class-image-container {
  width: 250px;
  height: 175px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: linear-gradient(135deg, #f0f7ff, #e6f4ff);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.class-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.class-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f7ff, #e6f4ff);
}

.placeholder-icon {
  font-size: 48px;
  color: #91caff;
}

.custom-tabs {
  margin-top: 16px;
}

.custom-tabs :deep(.ant-tabs-nav) {
  margin: 0;
}

.custom-tabs :deep(.ant-tabs-tab) {
  padding: 12px 24px;
  font-weight: 500;
}

.custom-tabs :deep(.ant-tabs-tab-active) {
  color: #1677ff;
}

.tab-content {
  padding: 16px 0;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.action-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s;
}

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.course-list-container {
  margin-top: 16px;
  max-height: 53vh;
  overflow-y: auto;
  padding-right: 8px;
  padding-top: 8px;
}

/* 课程时间轴容器 */
.course-timeline-container {
  position: relative;
  padding: 0 40px;
}

/* 时间轴线 */
.timeline-line {
  position: absolute;
  left: 60px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #1890ff, #91caff);
  z-index: 0;
}

/* 课程时间轴列表 */
.course-timeline-list {
  position: relative;
  z-index: 1;
}

/* 时间轴项 */
.course-timeline-item {
  display: flex;
  margin-bottom: 24px;
  align-items: flex-start;
  position: relative;
}

/* 时间节点 */
.timeline-node {
  width: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 8px;
}

.node-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #1890ff;
  border: 3px solid white;
  box-shadow: 0 0 0 2px #1890ff;
  z-index: 2;
}

.node-date {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
  font-weight: 500;
}

/* 课程卡片 */
.course-card {
  flex: 1;
  padding: 16px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  cursor: pointer;
  border: 1px solid #f0f2f5;
  margin-left: 16px;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.2);
  border-color: #91caff;
}

.course-card.selected {
  background-color: #f0f9ff;
  border-left: 3px solid #1890ff;
}

.course-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.course-title {
  font-weight: 600;
  font-size: 16px;
  color: #1d2129;
  margin: 0;
}

.course-description {
  color: #86909c;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-meta {
  display: flex;
  justify-content: flex-end;
}

.create-time {
  font-size: 12px;
  color: #8c8c8c;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .course-timeline-container {
    padding: 0 20px;
  }

  .timeline-line {
    left: 30px;
  }

  .timeline-node {
    width: 50px;
  }
}

.student-list-container {
  margin-top: 16px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
  border-radius: 8px;
  border: 1px solid #f0f2f5;
}

.student-table {
  background: #ffffff;
  border-radius: 8px;
  overflow: hidden;
}

.student-table-header {
  display: flex;
  background-color: #f8f9fa;
  padding: 12px 16px;
  font-weight: 500;
  color: #1d2129;
  border-bottom: 1px solid #f0f2f5;
}

.student-table-row {
  display: flex;
  padding: 12px 16px;
  align-items: center;
  transition: background-color 0.3s;
}

.student-table-row:hover {
  background-color: #f8f9fa;
}

.student-table-row:not(:last-child) {
  border-bottom: 1px solid #f0f2f5;
}

.student-cell {
  display: flex;
  align-items: center;
  padding: 0 8px;
}

.student-name {
  margin-left: 12px;
  color: #1d2129;
  font-weight: 500;
}

.remove-btn {
  border-radius: 4px;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fff2f0;
}

.report-container {
  padding: 24px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  min-height: 400px;
}

.report-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: flex-end;
}

.generate-btn {
  border-radius: 6px;
  font-weight: 500;
}

.empty-report {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  background: #f8f9fa;
  border-radius: 8px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .class-container {
    padding: 16px;
  }

  .class-header {
    flex-direction: column;
  }

  .class-image-container {
    width: 100%;
    height: 180px;
  }

  .action-bar {
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }

  .course-grid {
    grid-template-columns: 1fr;
  }
}

/* 解决方案2：弹性布局滚动（推荐） */

.markdown-content {
  flex: 1;
  overflow-y: auto;
  max-height: 54vh; /* 根据视口高度自动调整 */
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

/* 搜索框样式 */
.custom-search-input {
  width: 350px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.custom-search-input:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.custom-search-input :deep(.ant-input) {
  height: 40px;
  padding: 0 16px;
  border: none;
  background-color: #f8f9fa;
}

.custom-search-input :deep(.ant-input:focus) {
  box-shadow: none;
  background-color: #fff;
}

.custom-search-input :deep(.ant-input-group-addon) {
  background: transparent;
}

.search-button {
  height: 40px;
  border-radius: 0 20px 20px 0 !important;
  padding: 0 20px;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  border: none;
  transition: all 0.3s ease;
}

.search-button:hover {
  background: linear-gradient(135deg, #40a9ff, #1890ff);
  transform: translateY(-1px);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .custom-search-input {
    width: 100%;
  }

  .action-bar {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
