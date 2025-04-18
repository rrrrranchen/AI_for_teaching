<template>
  <div class="home">
    <a-row :gutter="24">
      <!-- 左边区域 (2/3宽度) -->
      <a-col :span="16">
        <div class="left-section">
          <!-- 轮播图 -->
          <div class="carousel-section">
            <a-carousel autoplay>
              <div v-for="(image, index) in carouselImages" :key="index">
                <img :src="image" class="carousel-image" alt="轮播图" />
              </div>
            </a-carousel>
          </div>

          <!-- 下方卡片 -->
          <a-row :gutter="24" class="card-container">
            <a-col :span="12">
              <a-card title="智能备课" class="info-card">
                <!-- 原有智能备课内容 -->
                <a-list
                  item-layout="horizontal"
                  :data-source="teachingDesigns.slice(0, 5)"
                >
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <router-link
                        :to="`/home/teaching-design/${item.design_id}`"
                      >
                        {{ item.title }}
                      </router-link>
                    </a-list-item>
                  </template>
                </a-list>
                <template #actions>
                  <a-button
                    type="primary"
                    @click="$router.push('/home/smart-preparation')"
                  >
                    进行智能备课
                  </a-button>
                </template>
              </a-card>
            </a-col>
            <a-col :span="12">
              <a-card title="学习社区" class="info-card">
                <!-- 原有学习社区内容 -->
                <template #cover></template>
                <template #actions>
                  <a-button
                    type="primary"
                    @click="$router.push('/home/community')"
                  >
                    进入学习社区
                  </a-button>
                </template>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </a-col>

      <!-- 右边区域 (1/3宽度) -->
      <a-col :span="8" class="right-section">
        <a-card title="创建课程班" class="create-card">
          <a-form layout="vertical" @submit.prevent="handleCreateCourseclass">
            <a-form-item label="课程班名称" required>
              <a-input v-model:value="newCourseclass.name" />
            </a-form-item>
            <a-form-item label="课程班描述">
              <a-textarea
                v-model:value="newCourseclass.description"
                :rows="3"
              />
            </a-form-item>
            <a-button type="primary" html-type="submit" block>
              创建新课程班
            </a-button>
          </a-form>
        </a-card>

        <a-card title="我的班级" class="class-list-card">
          <a-list
            item-layout="horizontal"
            :data-source="courseClasses.slice(0, 4)"
            :loading="loading"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :description="item.description">
                  <template #title>
                    <router-link :to="`/home/courseclass/${item.id}`">
                      {{ item.name }}
                    </router-link>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>

            <template #loadMore>
              <div class="view-more">
                <a @click="$router.push('/home/my-class')">查看更多课程班 →</a>
              </div>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from "vue";
import { message } from "ant-design-vue";
import { useAuthStore } from "@/stores/auth";
import { getAllCourseclasses, createCourseclass } from "@/api/courseclass";
import { getMyDesigns } from "@/api/teachingdesign";

export default defineComponent({
  name: "HomeView",
  setup() {
    const authStore = useAuthStore();
    const courseClasses = ref<any[]>([]);
    const teachingDesigns = ref<any[]>([]);
    const loading = ref<boolean>(false); // 新增loading属性

    // 本地轮播图片路径
    const carouselImages = ref([
      require("@/assets/carousel1.png"),
      require("@/assets/carousel1.png"),
      require("@/assets/carousel1.png"),
      require("@/assets/carousel1.png"),
    ]);
    // 获取课程班数据
    const loadCourseClasses = async () => {
      try {
        loading.value = true; // 显示加载状态
        const data = await getAllCourseclasses();
        courseClasses.value = data;
      } catch (error) {
        console.error("获取课程班失败:", error);
      } finally {
        loading.value = false; // 隐藏加载状态
      }
    };

    // 获取教学设计数据
    const loadTeachingDesigns = async () => {
      try {
        loading.value = true; // 显示加载状态
        const data = await getMyDesigns();
        teachingDesigns.value = data;
      } catch (error) {
        console.error("获取教学设计失败:", error);
      } finally {
        loading.value = false; // 隐藏加载状态
      }
    };

    // 新增课程班创建表单
    const newCourseclass = ref({
      name: "",
      description: "",
    });

    // 创建课程班方法
    const handleCreateCourseclass = async () => {
      if (!newCourseclass.value.name.trim()) {
        message.warning("请输入课程班名称");
        return;
      }

      try {
        loading.value = true; // 显示加载状态
        await createCourseclass({
          name: newCourseclass.value.name,
          description: newCourseclass.value.description,
        });
        message.success("课程班创建成功");
        newCourseclass.value = { name: "", description: "" };
        loadCourseClasses(); // 刷新列表
      } catch (error) {
        message.error("课程班创建失败");
      } finally {
        loading.value = false; // 隐藏加载状态
      }
    };

    // 初始化加载数据
    if (authStore.isAuthenticated) {
      loadCourseClasses();
      loadTeachingDesigns();
    }

    return {
      courseClasses,
      teachingDesigns,
      carouselImages,
      newCourseclass,
      handleCreateCourseclass,
      loading, // 返回loading属性
    };
  },
});
</script>

<style scoped>
.home {
  padding: 16px;
}

.left-section {
  padding: 2vh;
  background-color: rgb(212, 248, 235);
  height: 94vh;
  border-radius: 16px;
}

.right-section {
  padding-top: 2vh;
  background-color: rgb(194, 237, 244);
  height: 94vh;
  border-radius: 16px;
}

.carousel-section {
  margin-bottom: 24px;
}

.carousel-image {
  width: 100%;
  height: 400px;
  object-fit: cover;
}

/* 调整原有样式 */
.card-container {
  margin-top: 24px;
}

.info-card {
  background-color: #faf5df;
  margin-bottom: 24px;
  height: calc(100% - 24px);
}

/* 确保内容自适应高度 */
.ant-col-16,
.ant-col-8 {
  display: flex;
  flex-direction: column;
}

/* 响应式处理 */
@media (max-width: 992px) {
  .ant-col-16,
  .ant-col-8 {
    width: 100%;
    max-width: 100%;
    flex: 0 0 100%;
  }
}
/* 轮播器圆角设置 */
:deep(.ant-carousel) {
  border-radius: 12px; /* 调整圆角大小 */
  overflow: hidden; /* 确保内容也遵循圆角 */
}

/* 轮播图片圆角设置 */
.carousel-image {
  border-radius: 12px; /* 与容器保持一致 */
}

/* 响应式处理 */
@media (max-width: 768px) {
  :deep(.ant-carousel),
  .carousel-image {
    border-radius: 8px; /* 移动端可以小一点 */
  }
}

/* 新增右边区域样式 */
.create-card {
  margin-bottom: 24px;
}

.class-list-card {
  max-height: 500px;
  overflow-y: auto;
}

.view-more {
  text-align: center;
  padding: 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
