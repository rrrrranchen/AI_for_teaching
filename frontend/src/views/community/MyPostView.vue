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

    <MyPostList
      :posts="posts"
      :loading="loading"
      :current="pagination.current"
      :page-size="pagination.pageSize"
      :total="pagination.total"
      :empty-text="emptyText"
      :show-actions="true"
      @edit="handleEdit"
      @delete="handleDelete"
      @page-change="handlePageChange"
    />

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
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { message } from "ant-design-vue";
import { PlusOutlined } from "@ant-design/icons-vue";
import forumApi from "@/api/forum";
import { ForumPost } from "@/api/forum";
import MyPostList from "@/components/community/MyPostList.vue";

// 状态管理
const posts = ref<ForumPost[]>([]);
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
});

const emptyText = "您还没有发布过帖子";

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
    posts.value = posts.value.filter((post) => post.id !== deletingId.value);
    deleteVisible.value = false;
  } catch (error) {
    message.error("删除失败");
  }
};

// 处理分页变化
const handlePageChange = ({ page, size }: { page: number; size: number }) => {
  pagination.current = page;
  pagination.pageSize = size;
  fetchPosts();
};

// 初始加载
onMounted(fetchPosts);
</script>

<style scoped>
.my-posts-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  padding: 0;
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .my-posts-view {
    padding: 16px;
  }
}
</style>
