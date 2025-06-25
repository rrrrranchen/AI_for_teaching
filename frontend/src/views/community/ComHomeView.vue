<!-- src/views/HomeView.vue -->
<template>
  <div class="home-view">
    <!-- 搜索和排序控制栏 -->
    <div class="control-bar">
      <a-input-search
        v-model:value="searchKeyword"
        placeholder="搜索帖子..."
        enter-button
        @search="handleSearch"
        class="search-input"
      />

      <div class="sort-controls">
        <span class="sort-label">排序方式：</span>
        <a-select
          v-model:value="sortBy"
          style="width: 120px"
          @change="fetchPosts"
        >
          <a-select-option value="composite">综合排序</a-select-option>
          <a-select-option value="like_count">点赞最多</a-select-option>
          <a-select-option value="favorite_count">收藏最多</a-select-option>
          <a-select-option value="view_count">浏览最多</a-select-option>
          <a-select-option value="created_at">最新发布</a-select-option>
        </a-select>
      </div>
    </div>

    <!-- 帖子列表 -->
    <div class="list-container">
      <a-list
        item-layout="vertical"
        size="large"
        :loading="loading"
        :data-source="posts"
        :pagination="pagination"
      >
        <template #renderItem="{ item, index }">
          <a-list-item>
            <!-- 添加滑动动画 -->
            <div
              class="post-wrapper"
              :style="{ 'animation-delay': `${index * 0.1}s` }"
            >
              <a-card hoverable class="post-card">
                <template #actions>
                  <!-- 浏览数 -->
                  <span> <eye-outlined /> {{ item.view_count }} </span>

                  <!-- 点赞按钮 -->
                  <span @click="handleLike(item)">
                    <component
                      :is="item.is_liked ? LikeFilled : LikeOutlined"
                      :style="{ color: item.is_liked ? '#1890ff' : 'inherit' }"
                    />
                    {{ item.like_count }}
                  </span>

                  <!-- 收藏按钮 -->
                  <span @click="handleFavorite(item)">
                    <component
                      :is="item.is_favorited ? StarFilled : StarOutlined"
                      :style="{
                        color: item.is_favorited ? '#ffd666' : 'inherit',
                      }"
                    />
                    {{ item.favorite_count }}
                  </span>
                </template>

                <a-list-item-meta
                  :description="`作者：${
                    item.authorname
                  } | 发布时间：${formatDate(item.created_at)}`"
                >
                  <template #title>
                    <router-link :to="`/home/community/posts/${item.id}`">{{
                      item.title
                    }}</router-link>
                  </template>
                </a-list-item-meta>

                <div class="post-tags" v-if="item.tags?.length">
                  <a-tag v-for="tag in item.tags" :key="tag">{{ tag }}</a-tag>
                </div>
                <div class="content-preview" v-html="item.content"></div>
              </a-card>
            </div>
          </a-list-item>
        </template>
      </a-list>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { defineComponent, ref, reactive } from "vue";
import {
  EyeOutlined,
  LikeOutlined,
  StarOutlined,
  LikeFilled,
  StarFilled,
} from "@ant-design/icons-vue";
import forumApi from "@/api/forum";
import type { ForumPost } from "@/api/forum";
import { message } from "ant-design-vue";

// export default defineComponent({
//   name: "HomeView",
//   components: {
//     EyeOutlined,
//     LikeOutlined,
//     StarOutlined,
//     LikeFilled,
//     StarFilled,
//   },
//   setup() {
// 状态管理
const posts = ref<ForumPost[]>([]);
const loading = ref(false);
const searchKeyword = ref("");
const sortBy = ref<
  "composite" | "created_at" | "like_count" | "favorite_count" | "view_count"
>("composite");

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  onChange: (page: number) => {
    pagination.current = page;
    fetchPosts();
  },
});

export interface MongoDate {
  $date: string;
}
type CreatedAtType = string | MongoDate | Date | null | undefined;
const formatDate = (date: CreatedAtType): string => {
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

// 获取帖子数据
const fetchPosts = async () => {
  try {
    loading.value = true;

    if (searchKeyword.value) {
      // 执行搜索
      const result = await forumApi.searchPosts(searchKeyword.value);
      posts.value = result;
      pagination.total = result.length;
    } else {
      // 获取排序后的帖子
      const result = await forumApi.getPosts(sortBy.value);
      posts.value = result;
      pagination.total = result.length;
    }
  } catch (error) {
    message.error("获取帖子列表失败");
  } finally {
    loading.value = false;
  }
};

// 搜索处理（带防抖）
let searchTimer: number;
const handleSearch = () => {
  clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    pagination.current = 1;
    fetchPosts();
  }, 500);
};

// 初始加载
fetchPosts();

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

//     return {
//       posts,
//       loading,
//       searchKeyword,
//       sortBy,
//       pagination,
//       formatDate,
//       handleSearch,
//       fetchPosts,
//       handleLike,
//       handleFavorite,
//     };
//   },
// });
</script>

<style scoped>
.home-view {
  max-width: 100vh;
  margin: 0 auto;
}

.control-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.search-input {
  width: 400px;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-label {
  color: rgba(0, 0, 0, 0.6);
}

/* 卡片整体字体调整 */
.post-card {
  font-size: 13px;
  border: #e0e0e0 1px solid;
  background-color: #e1f4fe;
  transition: all 0.3s ease;
}

/* 标题字体 */
.post-card :deep(.ant-list-item-meta-title) {
  font-size: 16px !important;
  margin-bottom: 4px;
}

/* 作者信息 */
.post-card :deep(.ant-list-item-meta-description) {
  font-size: 12px !important;
  color: #666;
}

/* 内容预览 */
.content-preview {
  font-size: 13px !important;
  line-height: 1.4;
  -webkit-line-clamp: 3;
  margin: 8px 0;
}

/* 操作栏图标文字 */
.post-card :deep(.ant-card-actions) > li {
  font-size: 15px;
}

/* 标签字体 */
.post-tags :deep(.ant-tag) {
  font-size: 11px;
  padding: 0 6px;
  height: 22px;
  line-height: 20px;
}

/* 调整卡片内边距 */
.post-card :deep(.ant-card-body) {
  padding: 12px 16px !important;
}

/* 调整操作栏间距 */
.post-card :deep(.ant-card-actions) {
  margin: 0 !important;
  /* padding: 8px 0 !important; */
}

.ant-tag {
  margin-bottom: 4px;
}

/* 新增动画效果 */
.post-wrapper {
  opacity: 0;
  transform: translateY(20px);
  animation: slideUp 0.6s ease forwards;
}

@keyframes slideUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.list-container {
  flex: 1;
  overflow-y: auto;
  height: 80vh;
  margin-bottom: 16px;
  padding-left: 8px;
  padding-right: 8px; /* 给滚动条留出空间 */
}

/* 滚动条样式 */
.list-container::-webkit-scrollbar {
  width: 6px;
}

.list-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.list-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.list-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.pagination-container {
  flex-shrink: 0;
  padding: 8px 0;
  background: white;
  border-top: 1px solid #f0f0f0;
}

/* 紧凑布局调整 */
.ant-list-item {
  padding: 8px 0 !important;
}

/* 内容预览样式 */
.content-preview {
  color: rgba(0, 0, 0, 0.7);
  line-height: 1.6;
  margin: 12px 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  max-height: calc(1.6em * 3);
}

/* 调整元信息间距 */
.ant-list-item-meta {
  margin-bottom: 8px !important;
}

/* 调整操作栏间距 */
.ant-card-actions {
  margin-top: 8px !important;
  padding: 0 16px !important;
}

/* 标签样式优化 */
.post-tags {
  margin-top: 8px;
}

.ant-tag {
  margin-right: 8px;
  margin-bottom: 4px;
  padding: 0 8px;
  font-size: 12px;
}
</style>

<!-- 新增全局样式处理Markdown内容 -->
<style>
/* 全局调整图标尺寸 */
.post-card .anticon {
  font-size: 14px !important;
  vertical-align: -0.15em;
}
</style>
