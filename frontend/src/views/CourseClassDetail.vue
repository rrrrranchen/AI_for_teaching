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
            <h1>{{ courseclassDetail?.name }}</h1>
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
              <a-tag
                v-for="teacher in courseclassDetail?.teachers"
                :key="teacher.id"
                color="blue"
              >
                <user-outlined class="mr-1" />
                {{ teacher.username }}
              </a-tag>
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
                    >
                      <div class="course-card-header">
                        <a-checkbox
                          v-if="multiSelecting"
                          :checked="selectedCourseIds.includes(course.id)"
                          @change="() => toggleCourseSelection(course.id)"
                          class="course-checkbox"
                        />
                        <h3 class="course-title">{{ course.name }}</h3>
                      </div>

                      <p class="course-description">
                        {{ course.description || "暂无课程描述" }}
                      </p>

                      <div class="course-actions">
                        <a-button type="text" size="small" class="edit-btn">
                          <template #icon><edit-outlined /></template>
                          编辑
                        </a-button>
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
                        <user-outlined class="student-icon" />
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
import { message } from "ant-design-vue";
import { useRoute } from "vue-router";
import {
  getCourseclassDetail,
  getStudentsByCourseclass,
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
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons-vue";

export default defineComponent({
  name: "CourseClassDetail",
  components: {
    PlusOutlined,
    UserOutlined,
    CopyOutlined,
    SelectOutlined,
    CalendarOutlined,
    BookOutlined,
    EditOutlined,
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
    return {
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

.breadcrumb-section {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.class-header {
  padding: 24px;
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
  gap: 16px;
  align-items: left;
  margin-top: 20px;
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
  margin-bottom: 16px; /* 下间距 */
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

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.course-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  position: relative;
}

.course-card:hover {
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
  border-color: #d9d9d9;
}

.course-card.selected {
  border-color: #1890ff;
  background-color: #f0f8ff;
}

.course-card-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.course-checkbox {
  margin-right: 8px;
}

.course-title {
  font-size: 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  margin: 0;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-description {
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}

.course-actions {
  display: flex;
  justify-content: flex-end;
  border-top: 1px dashed #f0f0f0;
  padding-top: 12px;
}

.edit-btn {
  color: #1890ff;
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
</style>
