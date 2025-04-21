<template>
  <div class="community">
    <a-layout>
      <!-- 顶部导航栏 -->
      <a-layout-header class="header">
        <a-layout-header class="header">
          <a-row align="middle">
            <a-col flex="auto">
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
            </a-col>
            <a-col flex="none">
              <a-button
                type="primary"
                @click="router.push({ name: 'post-editor' })"
                size="large"
              >
                <template #icon><plus-outlined /></template>
                发布新帖
              </a-button>
            </a-col>
          </a-row>
        </a-layout-header>
      </a-layout-header>

      <!-- 内容区域 -->
      <a-layout-content class="content">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import {
  HomeOutlined,
  FileTextOutlined,
  StarOutlined,
} from "@ant-design/icons-vue";

const router = useRouter();

// 当前路由名称计算属性
const currentRoute = computed(() => {
  return [router.currentRoute.value.name?.toString() || "forum-home"];
});

// 处理菜单选择
const handleMenuSelect = ({ key }: { key: string }) => {
  router.push({ name: key });
};
</script>

<style scoped>
.community {
  height: 100vh;
}

.header {
  height: 80px;
  padding: 0 20px;
  background: #e1f4fe;
}

.content {
  padding: 24px;
  background: #fff;
  min-height: calc(100vh - 64px);
}
</style>
