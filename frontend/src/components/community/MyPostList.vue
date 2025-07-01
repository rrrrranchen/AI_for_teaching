<!-- src/components/forum/PostList.vue -->
<template>
  <div class="posts-list">
    <a-spin :spinning="loading">
      <div v-if="posts.length === 0" class="empty-state">
        <a-empty :description="emptyText || '暂无帖子'">
          <template v-if="emptyText === '您还没有发布过帖子'" #extra>
            <a-button type="primary" @click="$emit('create-post')">
              立即创建第一篇帖子
            </a-button>
          </template>
        </a-empty>
      </div>

      <div v-else class="posts-container">
        <div
          v-for="(post, index) in posts"
          :key="post.id"
          class="post-item"
          :style="{ 'animation-delay': `${index * 0.05}s` }"
        >
          <!-- 顶部作者信息 -->
          <div class="post-author">
            <a-avatar :src="getAvatarUrl(post.author_avatar)" size="small" />
            <div class="author-info">
              <div class="author-name-line">
                <span class="author-name">{{ post.author_name }}</span>
              </div>
              <span class="post-date">{{ formatDate(post.created_at) }}</span>
            </div>
          </div>

          <div class="post-content-wrapper">
            <!-- 标题 -->
            <router-link :to="getPostLink(post.id)" class="post-title">
              {{ post.title }}
            </router-link>

            <!-- 内容预览 -->
            <div class="post-content-preview">
              {{ truncateContent(post.content) }}
            </div>

            <!-- 底部标签和统计 -->
            <div class="post-footer">
              <div class="post-tags">
                <a-tag
                  v-for="tag in post.tags"
                  :key="tag"
                  :color="
                    getTagColor(tags.find((t) => t.name === tag)?.id || 0)
                  "
                  class="post-tag"
                >
                  {{ tag }}
                </a-tag>
              </div>
              <div class="post-stats">
                <span class="stat-item">
                  <EyeOutlined /> {{ post.view_count }}
                </span>
                <span class="stat-item" @click="$emit('like', post)">
                  <component
                    :is="post.is_liked ? LikeFilled : LikeOutlined"
                    :style="{
                      color: post.is_liked ? '#ff4d4f' : 'inherit',
                    }"
                  />
                  {{ post.like_count }}
                </span>
                <span class="stat-item" @click="$emit('favorite', post)">
                  <component
                    :is="post.is_favorited ? StarFilled : StarOutlined"
                    :style="{
                      color: post.is_favorited ? '#faad14' : 'inherit',
                    }"
                  />
                  {{ post.favorite_count }}
                </span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div v-if="showActions" class="post-actions">
              <a-button type="link" @click="$emit('edit', post.id)">
                <EditOutlined />
                编辑
              </a-button>
              <a-button type="link" danger @click="$emit('delete', post.id)">
                <DeleteOutlined />
                删除
              </a-button>
            </div>
          </div>

          <!-- 右侧图片预览 -->
          <div class="post-image-preview" v-if="hasImageAttachment(post)">
            <a-image :src="getImageUrl(getFirstImageUrl(post))" />
          </div>
        </div>
      </div>
    </a-spin>

    <div class="pagination-container" v-if="showPagination && posts.length > 0">
      <a-pagination
        v-model:current="currentPage"
        v-model:pageSize="pageSize"
        :total="total"
        show-size-changer
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, defineProps, defineEmits } from "vue";
import {
  EyeOutlined,
  LikeOutlined,
  StarOutlined,
  LikeFilled,
  StarFilled,
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons-vue";
import type { ForumPost, ForumTag } from "@/api/forum";

const props = defineProps({
  posts: {
    type: Array as () => ForumPost[],
    default: () => [],
  },
  tags: {
    type: Array as () => ForumTag[],
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  emptyText: {
    type: String,
    default: "",
  },
  // 分页相关
  showPagination: {
    type: Boolean,
    default: true,
  },
  current: {
    type: Number,
    default: 1,
  },
  pageSize: {
    type: Number,
    default: 10,
  },
  total: {
    type: Number,
    default: 0,
  },
  // 是否显示操作按钮
  showActions: {
    type: Boolean,
    default: false,
  },
  // 自定义链接生成
  postLinkPrefix: {
    type: String,
    default: "/home/community/posts/",
  },
  // 图片URL前缀
  imagePrefix: {
    type: String,
    default: "http://localhost:5000/",
  },
  // 头像URL前缀
  avatarPrefix: {
    type: String,
    default: "http://localhost:5000/",
  },
});

const emit = defineEmits([
  "like",
  "favorite",
  "page-change",
  "edit",
  "delete",
  "create-post",
]);

const currentPage = ref(props.current);
const pageSize = ref(props.pageSize);

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

// 格式化日期
const formatDate = (date: any): string => {
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

const truncateContent = (content: string, length = 125) => {
  if (!content) return "";
  return content.length > length
    ? content.substring(0, length) + "..."
    : content;
};

const hasImageAttachment = (post: any) => {
  return post.first_image !== "";
};

const getFirstImageUrl = (post: any) => {
  return post.first_image || "";
};

const getImageUrl = (url: string) => {
  return props.imagePrefix + url;
};

const getAvatarUrl = (url: string) => {
  if (!url) return "";
  return url.startsWith("http") ? url : props.avatarPrefix + url;
};

const getPostLink = (id: string | number) => {
  return props.postLinkPrefix + id;
};

const handlePageChange = (page: number, size: number) => {
  currentPage.value = page;
  pageSize.value = size;
  emit("page-change", { page, size });
};
</script>

<style scoped>
/* 帖子列表容器 */
.posts-list {
  width: 100%;
  margin: 0 auto;
}

/* 空状态样式 */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  background: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 帖子容器 */
.posts-container {
  display: grid;
  gap: 8px;
}

/* 单个帖子项 */
.post-item {
  display: flex;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  overflow: hidden;
  transition: all 0.1s ease;
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
  position: relative;
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 作者信息区域 */
.post-author {
  display: flex;
  align-items: center;
  padding-left: 8px;
  padding-right: 8px;
  width: 15vh;
  flex-shrink: 0;
  border-right: 1px solid #f0f0f0;
}

.author-info {
  margin-left: 8px;
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 500;
  color: #333;
  font-size: 14px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

.post-date {
  font-size: 12px;
  color: #999;
}

/* 帖子内容区域 */
.post-content-wrapper {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.post-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  transition: color 0.2s;
  text-decoration: none;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-title:hover {
  color: #1890ff;
}

.post-content-preview {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 帖子底部 */
.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.post-tag {
  margin-right: 0 !important;
  font-size: 12px !important;
  border-radius: 4px !important;
}

.post-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}

.stat-item:hover {
  color: #1890ff;
}

/* 操作按钮 */
.post-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  gap: 8px;
}

/* 图片预览区域 */
.post-image-preview {
  width: 160px;
  height: 120px;
  flex-shrink: 0;
  overflow: hidden;
  border-left: 1px solid #f0f0f0;
}

.post-image-preview .ant-image {
  width: 100%;
  height: 100%;
}

.post-image-preview .ant-image-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .post-item {
    flex-direction: column;
  }

  .post-author {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #f0f0f0;
  }

  .post-image-preview {
    width: 100%;
    height: 180px;
    border-left: none;
    border-top: 1px solid #f0f0f0;
  }

  .post-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .post-stats {
    width: 100%;
    justify-content: space-between;
  }

  .post-actions {
    justify-content: flex-start;
  }
}
</style>
