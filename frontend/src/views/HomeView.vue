<template>
  <div class="home">
    <!-- 顶部搜索栏 -->
    <div class="search-bar">
      <a-input-search
        v-model:value="searchQuery"
        placeholder="搜索课程..."
        size="large"
        @search="handleSearch"
        class="header-search-input"
      >
        <template #enterButton>
          <a-button type="primary">
            <SearchOutlined />
          </a-button>
        </template>
      </a-input-search>
    </div>

    <a-row :gutter="24" class="main-content">
      <!-- 左边区域 (2/3宽度) - 可滚动 -->
      <a-col :span="16">
        <div class="left-section scrollable-content">
          <!-- 轮播图 - 包含功能入口图片 -->
          <div class="carousel-section">
            <a-carousel autoplay>
              <div v-for="(image, index) in carouselImages" :key="index">
                <img
                  :src="image.src"
                  class="carousel-image"
                  alt="轮播图"
                  @click="handleCarouselClick(image.action)"
                />
              </div>
            </a-carousel>
          </div>

          <!-- 在推荐课程区域上方添加搜索结果展示区域 -->
          <div v-if="showSearchResults" class="search-results-section">
            <div class="section-title">
              <h2>搜索结果</h2>
              <a-button type="link" @click="clearSearch">返回推荐课程</a-button>
            </div>
            <a-row :gutter="16">
              <a-col
                :span="8"
                v-for="courseclass in searchResults"
                :key="courseclass.id"
              >
                <a-card
                  hoverable
                  class="course-card"
                  @click="goToCourseDetail(courseclass.id)"
                >
                  <template #cover>
                    <img
                      :src="
                        courseclass.image_path
                          ? 'http://localhost:5000/' + courseclass.image_path
                          : '/default-course.png'
                      "
                      alt="课程班封面"
                      class="course-cover"
                    />
                  </template>
                  <a-card-meta :title="courseclass.name">
                    <template #description>
                      <div class="course-meta">
                        <div class="description">
                          {{ courseclass.description || "暂无描述" }}
                        </div>
                        <div class="stats">
                          <span
                            ><user-outlined />
                            {{ courseclass.teacher_count || 0 }}位教师</span
                          >
                          <span
                            ><team-outlined />
                            {{ courseclass.student_count || 0 }}位学生</span
                          >
                        </div>
                      </div>
                    </template>
                  </a-card-meta>
                </a-card>
              </a-col>
            </a-row>
            <a-empty
              v-if="searchResults.length === 0"
              description="没有找到相关课程"
            />
          </div>

          <!-- 推荐课程班区域 - 使用卡片布局 -->
          <div class="section-title">
            <h2>推荐课程</h2>
          </div>
          <div class="recommend-courses">
            <a-row :gutter="16">
              <a-col
                :span="8"
                v-for="courseclass in recommendedClasses"
                :key="courseclass.id"
              >
                <a-card
                  hoverable
                  class="course-card"
                  @click="goToCourseDetail(courseclass.id)"
                >
                  <template #cover>
                    <img
                      :src="'http://localhost:5000/' + courseclass.image_path"
                      alt="课程班封面"
                      class="course-cover"
                    />
                  </template>
                  <a-card-meta :title="courseclass.name">
                    <template #description>
                      <div class="course-meta">
                        <div class="description">
                          {{ courseclass.description }}
                        </div>
                        <div class="stats">
                          <span
                            ><user-outlined />
                            {{ courseclass.student_count || 0 }}人</span
                          >
                          <span
                            ><book-outlined />
                            {{ courseclass.course_count || 0 }}课</span
                          >
                        </div>
                        <div class="reason">
                          推荐理由: {{ courseclass.reason }}
                        </div>
                      </div>
                    </template>
                  </a-card-meta>
                </a-card>
              </a-col>
            </a-row>
          </div>
        </div>
      </a-col>

      <!-- 右边区域 (1/3宽度) -->
      <a-col :span="8">
        <div class="right-section">
          <div class="section-title">
            <h2>我教的课程</h2>
            <p>最近参与的课程</p>
          </div>
          <a-list
            item-layout="horizontal"
            :data-source="courseClasses.slice(0, 5)"
            :loading="loading"
            class="my-classes-list"
          >
            <template #renderItem="{ item }">
              <a-list-item class="class-item">
                <a-list-item-meta>
                  <template #title>
                    <router-link :to="`/home/courseclass/${item.id}`">
                      {{ item.name }}
                    </router-link>
                  </template>
                  <template #description>
                    <span class="class-description">{{
                      item.description || "暂无描述"
                    }}</span>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <span><book-outlined /> {{ item.course_count || 0 }}课</span>
                </template>
              </a-list-item>
            </template>

            <template #loadMore>
              <div class="view-more">
                <a @click="$router.push('/home/my-class')">查看全部课程 →</a>
              </div>
            </template>
          </a-list>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from "vue";
import { message } from "ant-design-vue";
import { useRouter } from "vue-router";
import {
  UserOutlined,
  BookOutlined,
  SearchOutlined,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import {
  getAllCourseclasses,
  getRecommendedCourseclasses,
  type Courseclass,
  searchPublicCourseclasses,
} from "@/api/courseclass";
import { getMyDesigns } from "@/api/teachingdesign";

export default defineComponent({
  name: "HomeView",
  components: {
    UserOutlined,
    BookOutlined,
    SearchOutlined,
  },
  setup() {
    const authStore = useAuthStore();
    const courseClasses = ref<any[]>([]);
    const recommendedClasses = ref<any[]>([]);
    const teachingDesigns = ref<any[]>([]);
    const loading = ref<boolean>(false);
    const showMoreContent = ref<boolean>(true); // 控制是否显示更多内容

    const router = useRouter();
    const searchQuery = ref<string>("");
    const searchResults = ref<Courseclass[]>([]);
    const showSearchResults = ref<boolean>(false);
    const searchLoading = ref<boolean>(false);

    // 处理搜索
    const handleSearch = async () => {
      if (!searchQuery.value.trim()) {
        message.warning("请输入搜索关键词");
        return;
      }

      try {
        searchLoading.value = true;
        const results = await searchPublicCourseclasses(searchQuery.value);
        searchResults.value = results;
        showSearchResults.value = true;
      } catch (error) {
        message.error("搜索失败，请稍后重试");
        console.error("搜索错误:", error);
      } finally {
        searchLoading.value = false;
      }
    };

    // 清除搜索
    const clearSearch = () => {
      searchQuery.value = "";
      searchResults.value = [];
      showSearchResults.value = false;
    };

    // 跳转到课程详情
    const goToCourseDetail = (id: number) => {
      router.push(`/home/public-courseclass/${id}`);
    };

    // 轮播图片配置
    const carouselImages = ref([
      {
        src: require("@/assets/carousel1.png"),
        action: () => (window.location.href = "/home"),
      },
      {
        src: require("@/assets/aiforedu.png"),
        action: () => (window.location.href = "/home/smart-preparation"),
      },
      {
        src: require("@/assets/community.png"),
        action: () => (window.location.href = "/home/community"),
      },
    ]);

    // 处理轮播图点击
    const handleCarouselClick = (action: () => void) => {
      action();
    };

    // 获取课程班数据
    const loadCourseClasses = async () => {
      try {
        loading.value = true;
        const data = await getAllCourseclasses();
        courseClasses.value = data;
      } catch (error) {
        console.error("获取课程班失败:", error);
      } finally {
        loading.value = false;
      }
    };

    // 获取推荐课程班
    const loadRecommendedClasses = async () => {
      try {
        loading.value = true;
        const data = await getRecommendedCourseclasses();
        recommendedClasses.value = data;
        console.log(data);
      } catch (error) {
        console.error("获取推荐课程班失败:", error);
      } finally {
        loading.value = false;
      }
    };

    // 获取教学设计数据
    const loadTeachingDesigns = async () => {
      try {
        loading.value = true;
        const data = await getMyDesigns();
        teachingDesigns.value = data;
      } catch (error) {
        console.error("获取教学设计失败:", error);
      } finally {
        loading.value = false;
      }
    };

    // 初始化加载数据
    if (authStore.isAuthenticated) {
      loadCourseClasses();
      loadTeachingDesigns();
      loadRecommendedClasses();
    }

    return {
      courseClasses,
      recommendedClasses,
      teachingDesigns,
      carouselImages,
      searchQuery,
      searchResults,
      showSearchResults,
      searchLoading,
      handleSearch,
      clearSearch,
      goToCourseDetail,
      showMoreContent,
      handleCarouselClick,
      loading,
    };
  },
});
</script>

<style scoped lang="less">
.home {
  padding: 0 24px 24px;
  background-color: #edf6fbcc;
  height: 100vh;
}
.search-bar {
  padding: 16px 0;
  margin-bottom: 16px;
  :deep(.ant-input-search) {
    max-width: 800px;
    margin: 0 auto;
    display: block;
  }
}

.header-search-input :deep(.ant-input) {
  height: 40px;
  border-radius: 20px 0 0 20px !important;
}

.header-search-input :deep(.ant-input-group-addon) {
  background: transparent;
}

.header-search-input :deep(.ant-input-search-button) {
  height: 40px;
  border-radius: 0 20px 20px 0 !important;
}

.main-content {
  margin-top: 16px;
  height: calc(100vh - 120px); /* 根据实际情况调整 */
}

.left-section {
  padding: 24px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  height: auto;
  max-height: calc(100vh - 120px); /* 根据实际情况调整 */
  overflow-y: auto;

  &.scrollable-content {
    overflow-y: auto;
    height: 100%;

    /* 自定义滚动条样式 */
    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb:hover {
      background: #a8a8a8;
    }
  }
}

.right-section {
  padding: 24px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  height: 800px;
}

.section-title {
  margin-bottom: 24px;

  h2 {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 4px;
    color: #1a1a1a;
  }

  p {
    font-size: 14px;
    color: #8c8c8c;
    margin: 0;
  }
}

.carousel-section {
  margin-bottom: 32px;

  .carousel-image {
    width: 100%;
    height: 300px;
    object-fit: cover;
    cursor: pointer;
    border-radius: 8px;
    transition: transform 0.3s;

    &:hover {
      transform: scale(1.01);
    }
  }
}

.recommend-courses {
  margin-top: 16px;
  margin-bottom: 32px;
}

.additional-section {
  margin-top: 32px;
}

.course-card {
  margin-bottom: 16px;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-4px);
  }

  :deep(.ant-card-meta-title) {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.course-cover {
  height: 150px;
  object-fit: cover;
}

.course-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;

  .description {
    color: #666;
    font-size: 13px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    min-height: 40px;
  }

  .reason {
    color: #8c8c8c;
    font-size: 12px;
    font-style: italic;
    background: #fafafa;
    padding: 4px 8px;
    border-radius: 4px;
  }

  .stats {
    display: flex;
    justify-content: space-between;
    color: #8c8c8c;
    font-size: 12px;
  }
}

.my-classes-list {
  .class-item {
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;
    transition: all 0.3s;

    &:hover {
      background-color: #fafafa;
    }

    :deep(.ant-list-item-meta-title) {
      font-weight: 500;
    }

    .class-description {
      color: #8c8c8c;
      font-size: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 1;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.view-more {
  text-align: center;
  padding: 12px;
  margin-top: 8px;

  a {
    color: #1890ff;
    font-size: 14px;

    &:hover {
      color: #40a9ff;
    }
  }
}

/* 响应式处理 */
@media (max-width: 992px) {
  .course-card {
    margin-bottom: 16px;
  }

  .ant-col-8 {
    width: 50%;
  }
}

@media (max-width: 768px) {
  .ant-col-8 {
    width: 100%;
  }

  .carousel-image {
    height: 200px;
  }

  .home {
    padding: 0 12px 12px;
    height: auto;
    overflow: auto;
  }

  .main-content {
    height: auto;
  }

  .left-section,
  .right-section {
    padding: 16px;
    height: auto;
  }

  .left-section.scrollable-content {
    overflow-y: visible;
  }
}
</style>
