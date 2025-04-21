<!-- src/views/community/FavoritesView.vue -->
<template>
  <div class="favorites-view">
    <a-page-header title="我的收藏" class="page-header" :back-icon="false">
      <template #extra>
        <a-button @click="router.push({ name: 'forum-home' })">
          <template #icon><arrow-left-outlined /></template>
          返回论坛
        </a-button>
      </template>
    </a-page-header>

    <a-list
      class="favorites-list"
      :loading="loading"
      :data-source="favorites"
      :pagination="pagination"
    >
      <template #renderItem="{ item }">
        <a-list-item class="favorite-item">
          <a-card hoverable class="post-card">
            <!-- 帖子信息 -->
            <router-link :to="`/posts/${item.post_id}`">
              <h3 class="post-title">{{ item.post_title }}</h3>
              <div class="meta">
                <div class="author-info">
                  <div class="author-name">{{ item.author_name }}</div>
                  <div class="post-time">{{ formatDate(item.created_at) }}</div>
                </div>
              </div>
            </router-link>

            <!-- 统计信息 -->
            <div class="stats">
              <div class="stat-item">
                <eye-outlined />
                <span>{{ item.view_count }}</span>
              </div>
              <div class="stat-item">
                <like-outlined
                  :style="{ color: item.is_liked ? '#1890ff' : '' }"
                />
                <span>{{ item.like_count }}</span>
              </div>
              <div class="stat-item">
                <star-filled :style="{ color: '#ffd666' }" />
                <span>{{ item.favorite_count }}</span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="actions">
              <a-button
                type="link"
                danger
                @click="handleUnfavorite(item.post_id)"
              >
                <delete-outlined />
                取消收藏
              </a-button>
            </div>
          </a-card>
        </a-list-item>
      </template>

      <template #empty>
        <a-empty description="您还没有收藏任何帖子">
          <a-button type="primary" @click="router.push({ name: 'forum-home' })">
            去发现精彩内容
          </a-button>
        </a-empty>
      </template>
    </a-list>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { message } from "ant-design-vue";
import forumApi from "@/api/forum";
import { ForumFavorite } from "@/api/forum";
import {
  ArrowLeftOutlined,
  EyeOutlined,
  LikeOutlined,
  StarFilled,
  DeleteOutlined,
} from "@ant-design/icons-vue";

// 状态管理
const favorites = ref<ForumFavorite[]>([]);
const loading = ref(false);
const router = useRouter();

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  pageSizeOptions: ["10", "20", "50"],
  onChange: (page: number, pageSize: number) => {
    pagination.current = page;
    pagination.pageSize = pageSize;
    fetchFavorites();
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

// 获取收藏数据
const fetchFavorites = async () => {
  try {
    loading.value = true;
    const response = await forumApi.getUserFavorites();
    // 假设接口返回完整帖子信息，实际需要根据接口调整
    favorites.value = response;
    pagination.total = response.length;
  } catch (error) {
    message.error("获取收藏列表失败");
  } finally {
    loading.value = false;
  }
};

// 取消收藏
const handleUnfavorite = async (postId: number) => {
  try {
    await forumApi.unfavoritePost(postId);
    message.success("已取消收藏");
    favorites.value = favorites.value.filter((item) => item.post_id !== postId);
  } catch (error) {
    message.error("操作失败");
  }
};

// 初始加载
onMounted(fetchFavorites);
</script>

<style scoped>
.favorites-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  padding: 0;
  margin-bottom: 24px;
}

.favorites-list {
  background: #fff;
  padding: 24px;
  height: 70vh;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.favorite-item {
  padding: 8px 0;
}

.favorite-item .post-card {
  width: 100%;
  border-radius: 8px;
}

.favorite-item .post-card .meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.favorite-item .post-card .meta .author-info .author-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.favorite-item .post-card .meta .author-info .post-time {
  color: #666;
  font-size: 12px;
}

.favorite-item .post-card .post-title {
  font-size: 18px;
  margin-bottom: 8px;
  color: #333;
}

.favorite-item .post-card .post-content {
  color: #666;
  line-height: 1.6;
  margin-bottom: 16px;
}

.favorite-item .post-card .stats {
  display: flex;
  gap: 24px;
  margin: 16px 0;
}

.favorite-item .post-card .stats .stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
}

.favorite-item .post-card .stats .stat-item span {
  font-size: 14px;
}

.favorite-item .post-card .actions {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  text-align: right;
}

@media (max-width: 768px) {
  .favorites-view {
    padding: 16px;
  }

  .favorites-list {
    padding: 16px;
  }
}
</style>
