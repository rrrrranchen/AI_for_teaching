<template>
  <div class="forum-container">
    <!-- 左侧标签栏 -->
    <div class="left-sidebar">
      <div class="tags-header">
        <h3><TagOutlined /> 热门标签</h3>
      </div>
      <div class="tags-container">
        <a-spin :spinning="loadingTags">
          <div class="tag-list">
            <a-tag
              v-for="tag in tags"
              :key="tag.id"
              :class="{ 'active-tag': activeTag === tag.id }"
              :color="getTagColor(tag.id)"
              @click="handleTagClick(tag)"
              class="custom-tag"
            >
              {{ tag.name }}
            </a-tag>
          </div>
        </a-spin>
      </div>
    </div>

    <!-- 中间内容区 -->
    <div class="main-content">
      <RecommendedDesigns />
      <!-- 搜索和排序控制栏 -->
      <div class="control-bar">
        <div class="sort-controls">
          <span class="sort-label">排序方式：</span>
          <a-select
            v-model:value="sortBy"
            @change="fetchPosts"
            class="premium-select"
          >
            <a-select-option
              v-for="option in sortOptions"
              :key="option.value"
              :value="option.value"
            >
              <template #suffixIcon>
                <component :is="option.icon" />
              </template>
              {{ option.label }}
            </a-select-option>
          </a-select>
        </div>
      </div>

      <!-- 帖子列表组件 -->
      <PostList
        :posts="displayPosts"
        :tags="tags"
        :loading="loading"
        :current="pagination.current"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        :empty-text="emptyText"
        @like="handleLike"
        @favorite="handleFavorite"
        @page-change="handlePageChange"
      />
    </div>

    <!-- 右侧公告栏 -->
    <div class="right-sidebar">
      <div class="announcement-section">
        <h3>系统公告</h3>
        <div class="announcement-list">
          <div class="announcement-item">
            <div class="announcement-title">系统维护通知</div>
            <div class="announcement-content">
              平台将于本周六凌晨2:00-4:00进行系统维护，期间可能无法访问。
            </div>
            <div class="announcement-date">2025-07-11</div>
          </div>
          <div class="announcement-item">
            <div class="announcement-title">新功能上线</div>
            <div class="announcement-content">
              论坛新增标签筛选功能，方便您更快找到感兴趣的内容。
            </div>
            <div class="announcement-date">2025-07-13</div>
          </div>
          <div class="announcement-item">
            <div class="announcement-title">社区规范更新</div>
            <div class="announcement-content">
              请各位用户遵守新版社区规范，共同维护良好讨论环境。
            </div>
            <div class="announcement-date">2025-06-28</div>
          </div>
        </div>
      </div>

      <div class="ad-section">
        <h3>推荐内容</h3>
        <div class="ad-item">
          <div class="ad-title">专业课程推荐</div>
          <div class="ad-content">
            最新前端开发课程，限时免费学习，点击了解详情。
          </div>
        </div>
        <div class="ad-item">
          <div class="ad-title">开发者大会</div>
          <div class="ad-content">
            2025全球开发者大会即将召开，早鸟票限时抢购中。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted, watch, defineProps } from "vue";
import {
  TagOutlined,
  SearchOutlined,
  LikeOutlined as LikeSortIcon,
  StarOutlined as StarSortIcon,
  EyeOutlined as ViewSortIcon,
  ClockCircleOutlined as TimeSortIcon,
  AppstoreOutlined as CompositeSortIcon,
} from "@ant-design/icons-vue";
import PostList from "@/components/community/PostList.vue";
import RecommendedDesigns from "@/components/community/RecommendedDesigns.vue";
import forumApi from "@/api/forum";
import type { ForumPost, ForumTag } from "@/api/forum";
import { message } from "ant-design-vue";

// Add props definition
const props = defineProps({
  searchKeyword: {
    type: String,
    default: "",
  },
});

// Modify the searchKeyword ref to use the prop
const searchKeyword = ref(props.searchKeyword);

// Watch for changes in the prop
watch(
  () => props.searchKeyword,
  (newVal) => {
    searchKeyword.value = newVal;
    if (newVal) {
      handleSearch();
    }
  }
);

// 状态管理
const posts = ref<ForumPost[]>([]);
const tags = ref<ForumTag[]>([]);
const loading = ref(false);
const loadingTags = ref(false);
const activeTag = ref<number | null>(null);
const sortBy = ref<
  "composite" | "created_at" | "like_count" | "favorite_count" | "view_count"
>("composite");

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
});

// 排序选项配置
const sortOptions = ref([
  { value: "composite", label: "综合排序", icon: CompositeSortIcon },
  { value: "like_count", label: "点赞最多", icon: LikeSortIcon },
  { value: "favorite_count", label: "收藏最多", icon: StarSortIcon },
  { value: "view_count", label: "浏览最多", icon: ViewSortIcon },
  { value: "created_at", label: "最新发布", icon: TimeSortIcon },
]);

// 空状态文本
const emptyText = computed(() => {
  if (searchKeyword.value)
    return `没有找到与"${searchKeyword.value}"相关的帖子`;
  if (activeTag.value) {
    const tag = tags.value.find((t) => t.id === activeTag.value);
    return tag ? `没有找到与"${tag.name}"标签相关的帖子` : "暂无帖子";
  }
  return "暂无帖子";
});

// 当前显示的帖子(分页后)
const displayPosts = computed(() => {
  const start = (pagination.current - 1) * pagination.pageSize;
  const end = start + pagination.pageSize;
  return posts.value.slice(start, end);
});

// 获取所有标签
const fetchTags = async () => {
  try {
    loadingTags.value = true;
    const result = await forumApi.getAllTags();
    tags.value = result;
  } catch (error) {
    message.error("获取标签失败");
  } finally {
    loadingTags.value = false;
  }
};

// 获取帖子数据
const fetchPosts = async () => {
  try {
    loading.value = true;
    let result: ForumPost[] = [];

    if (searchKeyword.value) {
      result = await forumApi.searchPosts(searchKeyword.value);
    } else if (activeTag.value) {
      const allPosts = await forumApi.getPosts(sortBy.value);
      result = allPosts.filter((post) =>
        post.tags?.some((tag) =>
          tags.value.some((t) => t.name === tag && t.id === activeTag.value)
        )
      );
    } else {
      result = await forumApi.getPosts(sortBy.value);
    }

    posts.value = result;
    pagination.total = result.length;
    pagination.current = 1; // 重置到第一页
  } catch (error) {
    message.error("获取帖子列表失败");
  } finally {
    loading.value = false;
  }
};

// 标签点击处理
const handleTagClick = (tag: ForumTag) => {
  if (activeTag.value === tag.id) {
    activeTag.value = null; // 取消选中
    searchKeyword.value = "";
  } else {
    activeTag.value = tag.id;
    searchKeyword.value = tag.name;
  }
  fetchPosts();
};

// 搜索处理
const handleSearch = () => {
  activeTag.value = null; // 清除标签选择
  fetchPosts();
};

// 分页变化处理
const handlePageChange = ({ page, size }: { page: number; size: number }) => {
  pagination.current = page;
  pagination.pageSize = size;
};

// 处理点赞操作
const handleLike = async (post: ForumPost) => {
  try {
    if (post.is_liked) {
      await forumApi.unlikePost(post.id);
      post.like_count -= 1;
    } else {
      await forumApi.likePost(post.id);
      post.like_count += 1;
    }
    post.is_liked = !post.is_liked;
  } catch (error) {
    message.error("操作失败，请稍后重试");
  }
};

// 处理收藏操作
const handleFavorite = async (post: ForumPost) => {
  try {
    if (post.is_favorited) {
      await forumApi.unfavoritePost(post.id);
      post.favorite_count -= 1;
    } else {
      await forumApi.favoritePost(post.id);
      post.favorite_count += 1;
    }
    post.is_favorited = !post.is_favorited;
  } catch (error) {
    message.error("操作失败，请稍后重试");
  }
};

// 生成标签颜色
const getTagColor = (id: number) => {
  const tagColors = [
    "red",
    "green",
    "orange",
    "blue",
    "pink",
    "cyan",
    "purple",
    "magenta",
    "volcano",
    "gold",
    "lime",
    "geekblue",
  ];
  return tagColors[id % tagColors.length];
};

// 初始加载
onMounted(() => {
  fetchTags();
  fetchPosts();
});
</script>
<style scoped>
.forum-container {
  height: 88vh;
  display: flex;
  margin: 0 auto;
  gap: 8px;
}

/* 左侧标签栏 - 增强样式 */
.left-sidebar {
  width: 25vh; /* 稍微加宽 */
  background: #fff;
  border-radius: 8px;
  /* box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); */
  padding: 16px;
}

.tags-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.tags-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.custom-tag {
  font-size: 14px !important;
  padding: 6px 12px !important;
  border-radius: 8px !important;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.custom-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.active-tag {
  font-weight: 500 !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
  transform: scale(1.05) !important;
}

/* 中间内容区 - 高级样式 */
.main-content {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 40vh;
  flex: 1;
  background: #fff;
  border-radius: 8px;
  /* box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); */
  padding: 20px;
}

.control-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
  align-items: center;
  gap: 16px;
}

/* 高级下拉选框样式 */
.premium-select {
  width: 180px;
}

.premium-select :deep(.ant-select-selector) {
  height: 40px !important;
  border-radius: 20px !important;
  padding: 0 16px !important;
  border: 1px solid #d9d9d9 !important;
  transition: all 0.3s !important;
  display: flex !important;
  align-items: center !important;
}

.premium-select :deep(.ant-select-selector:hover) {
  border-color: #1890ff !important;
}

.premium-select :deep(.ant-select-selection-item) {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}

.premium-select :deep(.ant-select-arrow) {
  right: 16px !important;
}

.sort-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

/* 右侧公告栏样式 */
.right-sidebar {
  width: 30vh;
  flex-shrink: 0;
}

.announcement-section,
.ad-section {
  background: #fff;
  border-radius: 4px;
  /* box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); */
  padding: 16px;
  margin-bottom: 20px;
}

.announcement-section h3,
.ad-section h3 {
  margin: 0 0 16px 0;
  font-size: 20px;
  color: #333;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.announcement-item {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #f0f0f0;
}

.announcement-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.announcement-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.announcement-content {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 4px;
}

.announcement-date {
  font-size: 12px;
  color: #999;
}

.ad-item {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.ad-title {
  font-size: 14px;
  font-weight: 500;
  color: #1890ff;
  margin-bottom: 4px;
}

.ad-content {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

/* 动画效果 */
@keyframes slideUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
