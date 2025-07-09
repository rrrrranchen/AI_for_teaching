<template>
  <div class="public-courseclass-detail">
    <a-page-header title="公开课程详情" @back="() => router.go(-1)" />

    <div v-if="courseclass" class="courseclass-container">
      <!-- 顶部图片区域 -->
      <div class="courseclass-banner">
        <a-image
          v-if="courseclass.image_path"
          :src="'http://localhost:5000/' + courseclass.image_path"
          class="banner-image"
          :preview="false"
          :width="'100%'"
        />
        <div class="banner-overlay"></div>
        <div class="banner-content">
          <h1>{{ courseclass.name }}</h1>
          <p class="description">{{ courseclass.description }}</p>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <a-card class="courseclass-card">
        <!-- 统计信息 -->
        <div class="stats-container">
          <!-- 教师展示 -->
          <div class="teacher-section">
            <h2 class="section-title"><user-outlined /> 授课教师</h2>
            <div class="teacher-list">
              <a-card
                v-for="(teacher, index) in courseclass.teachers"
                :key="index"
                hoverable
                class="teacher-card"
              >
                <div class="teacher-avatar-container">
                  <a-avatar
                    :src="'http://localhost:5000/' + teacher.avatar"
                    :size="80"
                    class="teacher-avatar"
                  />
                </div>
                <div class="teacher-info">
                  <h3>{{ teacher.username }}</h3>
                  <p v-if="index === 0" class="primary-teacher">主讲教师</p>
                  <p v-else class="assistant-teacher">助教教师</p>
                </div>
              </a-card>
            </div>
          </div>

          <div class="stat-item">
            <team-outlined class="stat-icon" />
            <div>
              <div class="stat-value">{{ courseclass.student_count }}</div>
              <div class="stat-label">学生人数</div>
            </div>
          </div>
          <div class="stat-item">
            <book-outlined class="stat-icon" />
            <div>
              <div class="stat-value">{{ courseclass.course_count }}</div>
              <div class="stat-label">课程数量</div>
            </div>
          </div>
        </div>
        <!-- 加入按钮 -->
        <div class="action-section">
          <a-button
            type="primary"
            size="large"
            :loading="joining"
            @click="handleJoinCourseclass"
            v-if="
              !courseclass.is_joined
              // && !courseclass.has_pending_application
            "
            class="join-button"
          >
            申请加入课程班
          </a-button>
          <a-button
            type="default"
            size="large"
            disabled
            v-else-if="courseclass.is_joined"
          >
            已加入
          </a-button>
          <a-button type="default" size="large" disabled v-else>
            申请已提交
          </a-button>
        </div>
      </a-card>
    </div>

    <a-empty v-else description="课程班不存在或无法访问" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { message } from "ant-design-vue";
import {
  UserOutlined,
  TeamOutlined,
  BookOutlined,
} from "@ant-design/icons-vue";
import { getCourseclassDetail, applyToCourseclass } from "@/api/courseclass";
import type { Courseclass } from "@/api/courseclass";

const route = useRoute();
const router = useRouter();

const courseclass = ref<Courseclass | null>(null);
const loading = ref(false);
const joining = ref(false);

const fetchCourseclassDetail = async () => {
  try {
    loading.value = true;
    const id = Number(route.params.id);
    const data = await getCourseclassDetail(id);
    courseclass.value = data;
  } catch (error) {
    message.error("获取课程班详情失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const handleJoinCourseclass = async () => {
  if (!courseclass.value) return;

  try {
    joining.value = true;
    // 使用新的申请接口
    const result = await applyToCourseclass(courseclass.value.id, {
      message: "申请加入课程班", // 可以自定义申请消息
    });

    message.success("申请已提交，等待审核");
    // 更新状态，显示"申请已提交"按钮
    // courseclass.value.has_pending_application = true;
  } catch (error: any) {
    message.error(error.response?.data?.message || "提交申请失败");
  } finally {
    joining.value = false;
  }
};

onMounted(() => {
  fetchCourseclassDetail();
});
</script>

<style scoped>
.public-courseclass-detail {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.courseclass-container {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 顶部图片区域样式 */
.courseclass-banner {
  position: relative;
  height: 400px;
  overflow: hidden;
}

.banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.courseclass-banner:hover .banner-image {
  transform: scale(1.05);
}

.banner-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60%;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.8) 0%,
    rgba(0, 0, 0, 0.5) 50%,
    transparent 100%
  );
}

.banner-content {
  position: absolute;
  bottom: 40px;
  left: 40px;
  right: 40px;
  color: white;
}

.banner-content h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.banner-content .description {
  font-size: 1.1rem;
  opacity: 0.9;
  max-width: 80%;
}

/* 卡片样式 */
.courseclass-card {
  border-radius: 0 0 12px 12px;
  border-top: none;
}

/* 统计信息样式 */
.stats-container {
  display: flex;
  justify-content: space-around;
  margin: 0 auto;
  max-width: 800px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 28px;
  color: #1890ff;
  background: #e6f7ff;
  padding: 12px;
  border-radius: 50%;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #1890ff;
}

.stat-label {
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
}

/* 教师区域样式 */
.teacher-section {
  margin: 40px 0;
}

.section-title {
  font-size: 1.5rem;
  margin-bottom: 20px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
}

.teacher-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.teacher-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.teacher-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.teacher-avatar-container {
  margin-bottom: 15px;
}

.teacher-avatar {
  border: 3px solid #1890ff;
}

.teacher-info {
  text-align: center;
}

.teacher-info h3 {
  margin-bottom: 5px;
}

.primary-teacher {
  color: #1890ff;
  font-weight: 500;
}

.assistant-teacher {
  color: #888;
}

/* 按钮区域样式 */
.action-section {
  text-align: center;
}

.join-button {
  padding: 0 40px;
  height: 48px;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .banner-content {
    left: 20px;
    right: 20px;
    bottom: 20px;
  }

  .banner-content h1 {
    font-size: 1.8rem;
  }

  .stats-container {
    flex-direction: column;
    gap: 20px;
    align-items: center;
  }

  .teacher-list {
    grid-template-columns: 1fr;
  }
}
</style>
