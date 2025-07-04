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

    <PostList
      :posts="formattedFavorites"
      :loading="loading"
      :current="pagination.current"
      :page-size="pagination.pageSize"
      :total="pagination.total"
      empty-text="您还没有收藏任何帖子"
      :show-actions="true"
      :show-favorite-action="false"
      @unfavorite="handleUnfavorite"
      @page-change="handlePageChange"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { message } from "ant-design-vue";
import { ArrowLeftOutlined } from "@ant-design/icons-vue";
import forumApi from "@/api/forum";
import PostList from "@/components/community/PostList.vue";
import type { ForumPost } from "@/api/forum";

// 状态管理
const favorites = ref<any[]>([]);
const loading = ref(false);
const router = useRouter();

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  pageSizeOptions: ["10", "20", "50"],
});

// 格式化收藏数据为PostList需要的格式
const formattedFavorites = computed<ForumPost[]>(() => {
  return favorites.value.map((item) => ({
    ...item,
    id: item.post_id,
    title: item.post_title,
    author_id: item.author_id,
    author_name: item.author_name,
    author_avatar: item.author_avatar,
    created_at: item.created_at,
    view_count: item.view_count,
    like_count: item.like_count,
    favorite_count: item.favorite_count,
    is_liked: item.is_liked,
    is_favorited: true, // 收藏页面所有帖子都是已收藏状态
    content: item.content || "",
    tags: item.tags || [],
  }));
});

// 获取收藏数据
const fetchFavorites = async () => {
  try {
    loading.value = true;
    const response = await forumApi.getUserFavorites();
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

// 处理分页变化
const handlePageChange = ({ page, size }: { page: number; size: number }) => {
  pagination.current = page;
  pagination.pageSize = size;
  fetchFavorites();
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

@media (max-width: 768px) {
  .favorites-view {
    padding: 16px;
  }
}
</style>
