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
            <a-tab-pane key="courses" tab="课程管理">
              <!-- 课程管理内容 -->
              <div class="tab-content">
                <div class="action-bar">
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
                      @click="handleCourseClick(course.id, course.name)"
                    >
                      <div class="course-card-header">
                        <a-checkbox
                          v-if="multiSelecting"
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
  DeleteOutlined,
} from "@ant-design/icons-vue";

export default defineComponent({
  name: "CourseClassDetail",
  components: {
    UserOutlined,
    CalendarOutlined,
    BookOutlined,
    DeleteOutlined,
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
</style>
