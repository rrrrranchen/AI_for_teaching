<!-- src/views/community/MyPostsView.vue -->
<template>
  <div class="my-posts-view">
    <a-page-header title="我的帖子" class="page-header" :back-icon="false">
      <template #extra>
        <a-button type="primary" @click="router.push({ name: 'post-editor' })">
          <template #icon><plus-outlined /></template>
          新建帖子
        </a-button>
      </template>
    </a-page-header>

    <div class="my-posts">
      <a-list
        class="post-list"
        :loading="loading"
        :data-source="posts"
        :pagination="pagination"
      >
        <template #renderItem="{ item }">
          <a-list-item class="post-item">
            <a-card hoverable class="post-card">
              <!-- 卡片头部 -->
              <div class="card-header">
                <div class="meta">
                  <div class="author-info">
                    <div class="post-time">
                      {{ formatDate(item.created_at) }}
                    </div>
                  </div>
                </div>
                <div class="actions">
                  <a-button type="link" @click="handleEdit(item.id)">
                    <edit-outlined />
                    编辑
                  </a-button>
                  <a-button type="link" danger @click="handleDelete(item.id)">
                    <delete-outlined />
                    删除
                  </a-button>
                </div>
              </div>

              <!-- 帖子内容 -->
              <router-link :to="`/posts/${item.id}`">
                <h3 class="post-title">{{ item.title }}</h3>
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
                  <star-outlined
                    :style="{ color: item.is_favorited ? '#ffd666' : '' }"
                  />
                  <span>{{ item.favorite_count }}</span>
                </div>
              </div>
            </a-card>
          </a-list-item>
        </template>

        <template #empty>
          <a-empty description="您还没有发布过帖子">
            <a-button
              type="primary"
              @click="router.push({ name: 'post-editor' })"
            >
              立即创建第一篇帖子
            </a-button>
          </a-empty>
        </template>
      </a-list>

      <!-- 删除确认对话框 -->
      <a-modal
        v-model:visible="deleteVisible"
        title="确认删除"
        @ok="confirmDelete"
        @cancel="deleteVisible = false"
      >
        <p>确定要删除这个帖子吗？删除后无法恢复</p>
      </a-modal>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { message } from "ant-design-vue";
import forumApi from "@/api/forum";
import { ForumPost, ForumUsers } from "@/api/forum";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  LikeOutlined,
  StarOutlined,
} from "@ant-design/icons-vue";

// 状态管理
const posts = ref<ForumUsers[]>([]);
const loading = ref(false);
const deleteVisible = ref(false);
const deletingId = ref<number | null>(null);
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
    const response = await forumApi.getUserPosts();
    posts.value = response;
    pagination.total = response.length;
  } catch (error) {
    message.error("获取帖子列表失败");
  } finally {
    loading.value = false;
  }
};

// 处理编辑
const handleEdit = (postId: number) => {
  router.push({ name: "post-editor", query: { postId } });
};

// 处理删除
const handleDelete = (postId: number) => {
  deletingId.value = postId;
  deleteVisible.value = true;
};

// 确认删除
const confirmDelete = async () => {
  if (!deletingId.value) return;

  try {
    await forumApi.deletePost(deletingId.value);
    message.success("删除成功");
    posts.value = posts.value.filter(
      (post: any) => post.id !== deletingId.value
    );
    deleteVisible.value = false;
  } catch (error) {
    message.error("删除失败");
  }
};

// 初始加载
onMounted(fetchPosts);
</script>

<style scoped>
.my-posts-view {
  max-width: 1200px;
  margin: 0 auto;
}

.my-posts {
  max-width: 1200px;
  height: 80vh; /* 设置高度为视口高度 */
  overflow-y: auto; /* 添加垂直滚动条 */
}

.page-header {
  padding: 0;
  margin-bottom: 24px;
}

.post-list {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.post-item {
  padding: 8px 0;
}

.post-card {
  width: 100%;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.post-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.post-card .card-header .meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.post-card .card-header .meta .author-info {
  display: flex;
  flex-direction: column;
}

.post-card .card-header .meta .author-info .author-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.post-card .card-header .meta .author-info .post-time {
  color: #666;
  font-size: 12px;
}

.post-card .card-header .actions .ant-btn-link {
  padding: 0 8px;
}

.post-card .post-title {
  font-size: 18px;
  margin-bottom: 8px;
  color: #333;
}

.post-card .post-content {
  color: #666;
  line-height: 1.6;
  margin-bottom: 16px;
}

.post-card .stats {
  display: flex;
  gap: 24px;
  margin-top: 16px;
}

.post-card .stats .stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
}

.post-card .stats .stat-item span {
  font-size: 14px;
}

@media (max-width: 768px) {
  .my-posts-view {
    padding: 16px;
  }

  .post-list {
    padding: 16px;
  }

  .post-card .card-header {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 12px;
  }

  .post-card .card-header .actions {
    width: 100%;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
