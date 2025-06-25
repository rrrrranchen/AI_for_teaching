<template>
  <div class="class-container">
    <div class="class-card">
      <!-- 面包屑导航 -->
      <div class="breadcrumb-section">
        <a-breadcrumb separator=">">
          <a-breadcrumb-item>
            <router-link to="/home/my-class">我的班级</router-link>
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
          <div class="class-basic">
            <div style="font-weight: bold; font-size: 36px; margin-left: 10px">
              {{ courseclassDetail?.name || "加载中..." }}
            </div>
            <div class="class-meta">
              <a-tag
                color="blue"
                class="cursor-pointer invite-code"
                @click="copyInviteCode"
              >
                <template #icon><copy-outlined /></template>
                邀请码：{{ courseclassDetail?.invite_code }}
              </a-tag>
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

          <div
            class="teacher-actions"
            v-if="
              courseclassDetail?.teachers?.some(
                (t) => t.id === authStore.user?.id
              )
            "
          >
            <a-space>
              <a-button type="primary" @click="showEditModal">
                <edit-outlined />
                编辑班级
              </a-button>
              <a-button danger @click="handleDeleteClass">
                <delete-outlined />
                删除班级
              </a-button>
            </a-space>
          </div>
          <!-- 编辑课程班模态框 -->
          <a-modal
            v-model:visible="editVisible"
            title="编辑课程班"
            @ok="handleEditSubmit"
            :confirm-loading="editing"
          >
            <a-form layout="vertical" :model="editForm">
              <a-form-item label="班级名称" required>
                <a-input v-model:value="editForm.name" />
              </a-form-item>
              <a-form-item label="班级描述">
                <a-textarea v-model:value="editForm.description" :rows="4" />
              </a-form-item>
            </a-form>
          </a-modal>
        </div>

        <!-- 标签页区域 -->
        <div class="class-tabs">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="courses" tab="课程管理">
              <!-- 课程管理内容 -->
              <div class="tab-content">
                <div class="action-bar">
                  <a-space>
                    <a-button type="primary" @click="showCreateModal">
                      <plus-outlined />
                      新建课程
                    </a-button>
                    <a-button @click="toggleMultiSelect">
                      <select-outlined />
                      {{ multiSelecting ? "退出多选" : "批量操作" }}
                    </a-button>
                    <a-button
                      danger
                      :disabled="selectedCourseIds.length === 0"
                      @click="deleteSelectedCourses"
                    >
                      删除选中（{{ selectedCourseIds.length }}）
                    </a-button>
                  </a-space>
                  <a-input-search
                    v-model:value="searchCourseKey"
                    placeholder="搜索课程"
                    style="width: 200px"
                  />
                </div>

                <!-- 改进后的课程列表 -->
                <div class="course-list-container">
                  <a-empty
                    v-if="filteredCourses.length === 0"
                    description="暂无课程"
                    class="empty-placeholder"
                  />

                  <div v-else class="course-grid">
                    <div
                      v-for="course in filteredCourses"
                      :key="course.id"
                      class="course-card"
                      :class="{
                        selected: selectedCourseIds.includes(course.id),
                      }"
                      @click="handleCourseClick(course.id, course.name)"
                    >
                      <div class="course-card-header">
                        <a-checkbox
                          v-if="multiSelecting"
                          :checked="selectedCourseIds.includes(course.id)"
                          @click.stop="() => toggleCourseSelection(course.id)"
                          class="course-checkbox"
                        />
                        <h3 class="course-title">{{ course.name }}</h3>
                      </div>

                      <p class="course-description">
                        {{ course.description || "暂无课程描述" }}
                      </p>
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
                    style="width: 200px"
                  />
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
                      <div class="header-cell" style="flex: 1">操作</div>
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
                      <div class="student-cell" style="flex: 1">
                        <a-popconfirm title="确定要移除此学生吗？">
                          <a-button type="text" danger size="small">
                            <template #icon><delete-outlined /></template>
                            移除
                          </a-button>
                        </a-popconfirm>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </a-tab-pane>
            <!-- 在template的a-tabs中添加新的标签页 -->
            <!-- 修改后的报告标签页 -->
            <a-tab-pane key="report" tab="分析报告">
              <div class="report-container">
                <div class="report-header">
                  <a-button
                    type="primary"
                    @click="handleUpdateReport"
                    :loading="updatingReport"
                  >
                    <sync-outlined />
                    {{ classReport ? "更新报告" : "生成报告" }}
                  </a-button>
                </div>

                <div v-if="!classReport" class="empty-report">
                  <a-empty description="暂无分析报告">
                    <a-button type="primary" @click="handleUpdateReport">
                      立即生成
                    </a-button>
                  </a-empty>
                </div>

                <!-- 使用markdown渲染容器 -->
                <div
                  v-else
                  class="markdown-content"
                  v-html="renderedReport"
                ></div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </div>
    </div>

    <!-- 创建课程模态框 -->
    <a-modal
      v-model:visible="createVisible"
      title="新建课程"
      @ok="addNewCourse"
      :confirm-loading="creating"
    >
      <a-form layout="vertical" :model="newCourse">
        <a-form-item label="课程名称" required>
          <a-input
            v-model:value="newCourse.name"
            placeholder="请输入课程名称"
          />
        </a-form-item>
        <a-form-item label="课程描述">
          <a-textarea
            v-model:value="newCourse.description"
            placeholder="请输入课程描述"
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from "vue";
import { message, Modal } from "ant-design-vue";
import { useRouter, useRoute } from "vue-router";
import {
  getCourseclassDetail,
  getStudentsByCourseclass,
  updateCourseclass,
  deleteCourseclass,
} from "@/api/courseclass";
import {
  getCoursesByCourseclass,
  createCourseForClass,
  removeCoursesFromClass,
} from "@/api/course";
import type { Courseclass, Student, MongoDate } from "@/api/courseclass";
import type { Course } from "@/api/course";
import {
  PlusOutlined,
  UserOutlined,
  CopyOutlined,
  SelectOutlined,
  CalendarOutlined,
  BookOutlined,
  DeleteOutlined,
  SyncOutlined,
  EditOutlined,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";

import { getClassAnalysisReport, updateClassReport } from "@/api/studentanswer";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

export default defineComponent({
  name: "CourseClassDetail",
  components: {
    PlusOutlined,
    UserOutlined,
    CopyOutlined,
    SelectOutlined,
    CalendarOutlined,
    BookOutlined,
    DeleteOutlined,
    SyncOutlined,
    EditOutlined,
  },
  setup() {
    const route = useRoute();
    const courseclassId = ref<number>(0);
    const courseclassDetail = ref<Courseclass | null>(null);
    const courses = ref<Course[]>([]);
    const students = ref<Student[]>([]);
    const loading = ref<boolean>(true);
    const error = ref<string | null>(null);
    const selectedCourseIds = ref<number[]>([]); // 选中的课程 ID 列表
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

    // 添加渲染后的报告内容
    const renderedReport = ref<string>("");
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
            console.error(err);
          }
        }
        return (
          '<pre class="hljs"><code>' +
          md.utils.escapeHtml(str) +
          "</code></pre>"
        );
      },
    });

    const classReport = ref<string | null>(null);
    const updatingReport = ref(false);

    // 获取报告数据
    const loadClassReport = async () => {
      try {
        const { data } = await getClassAnalysisReport(courseclassId.value);
        classReport.value = data.markdown_report;
        console.log("报告内容：", classReport.value);
        renderedReport.value = md.render(classReport.value || "");
      } catch (error) {
        message.error("获取报告失败");
      }
    };

    // 更新报告
    const handleUpdateReport = async () => {
      try {
        updatingReport.value = true;
        const { data } = await updateClassReport(courseclassId.value);
        classReport.value = data.markdown_report;
        console.log("报告内容：", classReport.value);
        message.success("报告更新成功");
        renderedReport.value = md.render(classReport.value);
      } catch (error) {
        message.error("报告更新失败");
      } finally {
        updatingReport.value = false;
      }
    };

    const handleCourseClick = (courseId: number, courseName: string) => {
      router.push({
        path: `/home/t-course/${courseId}`,
        query: {
          courseclassName: courseclassDetail.value?.name || "未知班级",
          courseclassId: courseclassId.value,
          courseName: courseName,
        },
      });
    };

    const filteredCourses = computed(() => {
      return courses.value.filter((c) =>
        c.name.toLowerCase().includes(searchCourseKey.value.toLowerCase())
      );
    });

    const filteredStudents = computed(() => {
      return students.value.filter((s) =>
        s.username.toLowerCase().includes(searchStudentKey.value.toLowerCase())
      );
    });

    const toggleMultiSelect = () => {
      multiSelecting.value = !multiSelecting.value;
      if (!multiSelecting.value) selectedCourseIds.value = [];
    };

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
        await loadClassReport();
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

    // 删除选中的课程
    const deleteSelectedCourses = async () => {
      if (selectedCourseIds.value.length === 0) {
        return;
      }

      try {
        await removeCoursesFromClass(courseclassId.value, {
          course_ids: selectedCourseIds.value,
        });

        // 更新课程列表
        courses.value = courses.value.filter(
          (course) => !selectedCourseIds.value.includes(course.id)
        );
        selectedCourseIds.value = [];
      } catch (err) {
        error.value = "删除课程失败";
        console.error(err);
      }
    };

    // 切换课程选中状态
    const toggleCourseSelection = (courseId: number) => {
      if (selectedCourseIds.value.includes(courseId)) {
        selectedCourseIds.value = selectedCourseIds.value.filter(
          (id) => id !== courseId
        );
      } else {
        selectedCourseIds.value.push(courseId);
      }
    };

    // 复制功能实现
    const copyInviteCode = async (code: string) => {
      try {
        await navigator.clipboard.writeText(code);
        message.success("邀请码已复制到剪贴板");
      } catch (err) {
        message.error("复制失败，请手动复制");
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

    const authStore = useAuthStore();
    const editVisible = ref(false);
    const editing = ref(false);
    const editForm = ref({
      name: "",
      description: "",
    });

    // 提交编辑
    const handleEditSubmit = async () => {
      try {
        editing.value = true;
        const updated = await updateCourseclass(courseclassId.value, {
          name: editForm.value.name,
          description: editForm.value.description,
        });

        courseclassDetail.value = updated;
        message.success("更新成功");
        editVisible.value = false;
        router.push(route.path);
      } catch (error) {
        message.error("更新失败");
      } finally {
        editing.value = false;
      }
    };

    // 删除课程班
    const handleDeleteClass = () => {
      Modal.confirm({
        title: "确认删除？",
        content: "此操作将永久删除该课程班及所有关联数据",
        okText: "确认",
        okType: "danger",
        cancelText: "取消",
        async onOk() {
          try {
            await deleteCourseclass(courseclassId.value);
            message.success("删除成功");
            router.push("/home/my-class");
          } catch (error) {
            message.error("删除失败");
          }
        },
      });
    };
    return {
      handleCourseClick,
      courseclassId,
      courseclassDetail,
      courses,
      students,
      loading,
      error,
      selectedCourseIds,
      newCourseName,
      newCourseDescription,
      addNewCourse,
      deleteSelectedCourses,
      toggleCourseSelection,
      activeTab,
      multiSelecting,
      searchCourseKey,
      searchStudentKey,
      createVisible,
      creating,
      newCourse,
      filteredCourses,
      filteredStudents,
      toggleMultiSelect,
      showCreateModal: () => (createVisible.value = true),
      copyInviteCode,
      formatCreatedAt,
      classReport,
      handleUpdateReport,
      updatingReport,
      renderedReport,
      authStore,
      editVisible,
      editing,
      editForm,
      showEditModal: () => (editVisible.value = true),
      handleEditSubmit,
      handleDeleteClass,
    };
  },
});
</script>
<style scoped>
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

.class-header {
  padding: 0px 24px;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  border-bottom: 1px solid #f0f0f0;
}

.class-basic {
  flex: 1;
  min-width: 300px;
}

.class-basic h1 {
  font-size: 24px;
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.85);
}

.class-meta {
  display: flex;
  flex-direction: column;
  align-items: left;
  margin-left: 30px;
  color: rgba(0, 0, 0, 0.45);
}

.class-description {
  color: rgba(0, 0, 0, 0.65);
  line-height: 1.6;
}

.teacher-section {
  padding-left: 24px;
  border-left: 1px solid #f0f0f0;
  min-width: 280px;
}

.teacher-section h3 {
  font-size: 16px;
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.85);
}

.class-tabs {
  padding: 0 24px;
}

.tab-content {
  padding: 24px 0;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.course-item,
.student-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
}

.course-item:hover,
.student-item:hover {
  background: #fafafa;
}

.course-title {
  font-weight: 500;
}

.course-description {
  color: rgba(0, 0, 0, 0.45);
}

.edit-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.course-item:hover .edit-btn {
  opacity: 1;
}

.remove-btn {
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #ff4d4f;
  color: white;
}

.invite-code {
  display: flex;
  max-width: 250px;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  margin-top: 20px;
  margin-bottom: 15px;
}

@media (max-width: 768px) {
  .class-header {
    flex-direction: column;
  }

  .teacher-section {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid #f0f0f0;
    padding-top: 24px;
  }

  .action-bar {
    flex-direction: column;
    gap: 16px;
  }

  .class-container {
    padding: 12px;
  }
}

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
/* 复制图标动画 */
.anticon-copy {
  transition: transform 0.2s;
}

.ant-tag:hover .anticon-copy {
  transform: translateX(2px);
}

/* 课程列表样式 */
.course-list-container {
  margin-top: 16px;
}

.empty-placeholder {
  padding: 40px 0;
  background: #fff;
  border-radius: 8px;
}

/* 调整课程列表布局 */
.course-grid {
  grid-template-columns: 1fr;
  gap: 8px;
}

.course-card {
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background-color: #ffffff;
  border-radius: 8px;
  margin: 20px;
}

.course-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.course-card-header {
  margin-bottom: 8px;
}

.course-description {
  font-size: 14px;
  line-height: 1.4;
  margin-bottom: 12px;
  -webkit-line-clamp: 2; /* 限制描述显示两行 */
}

/* 调整操作按钮位置 */
.course-actions {
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

/* 学生列表样式 */
.student-list-container {
  margin-top: 16px;
}

.student-table {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
  border: 1px solid #f0f0f0;
}

.student-table-header {
  display: flex;
  background-color: #fafafa;
  padding: 12px 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  border-bottom: 1px solid #f0f0f0;
}

.student-table-row {
  display: flex;
  padding: 12px 16px;
  align-items: center;
  transition: background-color 0.3s;
}

.student-table-row:hover {
  background-color: #fafafa;
}

.student-table-row:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}

.student-cell {
  display: flex;
  align-items: center;
  padding: 0 8px;
}

.student-icon {
  color: #1890ff;
  margin-right: 8px;
  font-size: 14px;
}

.student-name {
  margin-left: 10px;
  color: rgba(0, 0, 0, 0.85);
  font-weight: 500;
}

.student-id {
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .course-grid {
    grid-template-columns: 1fr;
  }

  .student-table-header {
    display: none;
  }

  .student-table-row {
    flex-direction: column;
    align-items: flex-start;
    padding: 16px;
  }

  .student-cell {
    width: 100%;
    padding: 4px 0;
    justify-content: space-between;
    border-bottom: none !important;
  }

  .student-cell::before {
    content: attr(data-label);
    color: rgba(0, 0, 0, 0.45);
    margin-right: 8px;
  }

  .student-cell[style*="flex: 2"]::before {
    content: "学生姓名";
  }

  .student-cell[style*="flex: 3"]::before {
    content: "学号";
  }

  .student-cell[style*="flex: 1"] {
    justify-content: flex-end;
    width: 100%;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed #f0f0f0;
  }

  .student-cell[style*="flex: 1"]::before {
    content: none;
  }
}

/* 课程列表容器 - 单列布局 */
.course-list-container {
  margin-top: 16px;
  max-height: 53vh;
  overflow-y: auto;
  padding-right: 8px;
}

/* 课程卡片 - 单列布局 */
.course-card {
  padding: 16px;
  margin-bottom: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  cursor: pointer;
}

.course-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.course-card.selected {
  background-color: #f0f9ff;
  border-left: 3px solid #1890ff;
}

/* 学生列表容器 - 单列布局 */
.student-list-container {
  margin-top: 16px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

/* 学生表格 - 单列布局 */
.student-table {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  border: 1px solid #f0f0f0;
}

.student-table-row {
  display: flex;
  padding: 12px 16px;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
}

.student-table-row:last-child {
  border-bottom: none;
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

/* 在style部分新增 */
.teacher-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #f0f0f0;
}

.teacher-actions .ant-btn {
  margin-right: 8px;
}
</style>
