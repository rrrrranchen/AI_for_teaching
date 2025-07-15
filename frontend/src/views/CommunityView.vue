<template>
  <div class="community">
    <a-layout>
      <!-- 顶部导航栏 -->
      <a-layout-header class="header">
        <div class="header-container">
          <!-- 左侧菜单 -->
          <div class="nav-menu-container">
            <a-menu
              v-model:selectedKeys="currentRoute"
              mode="horizontal"
              class="nav-menu"
              @select="handleMenuSelect"
            >
              <a-menu-item key="forum-home">
                <template #icon>
                  <home-outlined />
                </template>
                主页
              </a-menu-item>
              <a-menu-item key="my-posts">
                <template #icon>
                  <file-text-outlined />
                </template>
                我的帖子
              </a-menu-item>
              <a-menu-item key="favorites">
                <template #icon>
                  <star-outlined />
                </template>
                我的收藏
              </a-menu-item>
            </a-menu>
          </div>

          <!-- 中间搜索框 -->
          <div class="search-container">
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索帖子..."
              @search="handleSearch"
              class="custom-search-input"
            >
              <template #enterButton>
                <a-button type="primary" class="search-button">
                  <template #icon><search-outlined /></template>
                  搜索
                </a-button>
              </template>
            </a-input-search>
          </div>

          <!-- 右侧按钮 -->
          <div class="action-buttons">
            <a-button
              type="primary"
              @click="router.push({ name: 'post-editor' })"
              size="large"
            >
              <template #icon><plus-outlined /></template>
              发布
            </a-button>
          </div>
        </div>
      </a-layout-header>

      <!-- 内容区域 -->
      <a-layout-content class="content">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" :searchKeyword="searchKeyword" />
          </keep-alive>
        </router-view>
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import {
  HomeOutlined,
  FileTextOutlined,
  StarOutlined,
  SearchOutlined,
  PlusOutlined,
} from "@ant-design/icons-vue";

const router = useRouter();
const searchKeyword = ref("");

// 当前路由名称计算属性
const currentRoute = computed(() => {
  return [router.currentRoute.value.name?.toString() || "forum-home"];
});

// 处理菜单选择
const handleMenuSelect = ({ key }: { key: string }) => {
  router.push({ name: key });
};

// 处理搜索
const handleSearch = () => {
  if (router.currentRoute.value.name !== "forum-home") {
    router.push({ name: "forum-home" });
  }
};
</script>

<style scoped>
.community {
  height: 100vh;
}

.header {
  height: 75px;
  padding: 0 20px;
  background: #edf6fbcc;
  display: flex;
  align-items: center;
}

.header-container {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.nav-menu-container {
  flex: 1;
  width: 30vh;
}

.search-container {
  flex: 2;
  max-width: 500px;
  margin-top: 20px;
}

.action-buttons {
  flex: 1;
  width: 30vh;
  display: flex;
  justify-content: flex-end;
}

/* 搜索框样式 */
.custom-search-input {
  width: 500px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.custom-search-input:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.custom-search-input :deep(.ant-input) {
  height: 40px;
  padding: 0 16px;
  border: none;
  background-color: #f8f9fa;
}

.custom-search-input :deep(.ant-input:focus) {
  box-shadow: none;
  background-color: #fff;
}

.custom-search-input :deep(.ant-input-group-addon) {
  background: transparent;
}

.search-button {
  height: 40px;
  border-radius: 0 20px 20px 0 !important;
  padding: 0 20px;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  border: none;
  transition: all 0.3s ease;
}

.search-button:hover {
  background: linear-gradient(135deg, #40a9ff, #1890ff);
  transform: translateY(-1px);
}

.content {
  padding: 8px;
  background-color: #ffffff;
  min-height: calc(100vh - 64px);
}

/* 响应式调整 */
@media (max-width: 992px) {
  .header-container {
    flex-wrap: wrap;
    gap: 10px;
  }

  .nav-menu-container,
  .search-container,
  .action-buttons {
    min-width: 100%;
    margin: 5px 0;
  }

  .action-buttons {
    justify-content: center;
  }
}
</style>
