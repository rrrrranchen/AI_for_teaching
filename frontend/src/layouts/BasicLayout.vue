<template>
  <a-layout has-sider>
    <a-layout-sider
      theme="light"
      :width="240"
      :collapsedWidth="90"
      :style="{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
      }"
      v-model:collapsed="collapsed"
      collapsible
    >
      <div class="logo">
        <img src="../assets/sys_logo.png" alt="系统Logo" class="logo-img" />
        <h1 class="system-name" v-if="!collapsed">教备通</h1>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="light"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="1">
          <HomeFilled />
          <span class="nav-text">主页</span>
        </a-menu-item>
        <a-menu-item key="2">
          <TeamOutlined />
          <span class="nav-text">我的课程</span>
        </a-menu-item>
        <a-menu-item v-if="auth.user?.role === 'teacher'" key="3">
          <ReconciliationFilled />
          <span class="nav-text">智能备课</span>
        </a-menu-item>
        <a-menu-item key="4">
          <SlackCircleFilled />
          <span class="nav-text">学习社区</span>
        </a-menu-item>
        <a-menu-item v-if="auth.user?.role === 'teacher'" key="5">
          <DatabaseFilled />
          <span class="nav-text">我的知识库</span>
        </a-menu-item>
      </a-menu>
      <div
        class="user-info-container"
        :style="{
          bottom: 20,
          position: 'fixed',
          width: collapsed ? '90px' : '250px',
        }"
      >
        <div
          class="user-info"
          v-if="auth.isAuthenticated"
          @click="goToProfile"
          :style="collapsed ? { justifyContent: 'center' } : {}"
        >
          <a-avatar
            v-if="auth.user?.avatar"
            :size="48"
            :src="'http://localhost:5000/' + auth.user?.avatar"
            class="nav-avatar"
          >
          </a-avatar>
          <a-avatar v-else :size="48" class="nav-avatar">
            <UserOutlined />
          </a-avatar>
          <span v-if="!collapsed" class="username">{{
            auth.user?.username
          }}</span>
        </div>
      </div>
    </a-layout-sider>
    <a-layout
      :style="{
        marginLeft: collapsed ? '90px' : '240px',
        transition: 'margin 0.2s',
      }"
    >
      <a-layout-content
        :style="{
          overflow: 'initial',
          height: '98vh',
          padding: '0',
          margin: '0 16px 16px 8px',
        }"
      >
        <div class="g-card">
          <router-view v-slot="{ Component }">
            <keep-alive :include="['t-class', 's-class', 'CourseClassDetail']">
              <component
                :is="Component"
                v-if="$route.meta.keepAlive"
                :key="$route.fullPath"
              />
            </keep-alive>
            <component
              :is="Component"
              v-if="!$route.meta.keepAlive"
              :key="$route.fullPath"
            />
          </router-view>
          <!-- 悬浮按钮 -->
          <a-float-button
            type="primary"
            :style="{
              right: '48px',
              bottom: '48px',
            }"
            @click="showAIChatDialog"
          >
            <template #icon>
              <QuestionCircleOutlined />
            </template>
          </a-float-button>
        </div>
      </a-layout-content>
    </a-layout>

    <!-- AI聊天对话框 -->
    <AIChatDialog v-model:visible="showAIChat" />
  </a-layout>
</template>

<script lang="ts" setup>
import { ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { message } from "ant-design-vue";
import AIChatDialog from "@/components/AIChatDialog.vue";

const auth = useAuthStore();

import {
  HomeFilled,
  TeamOutlined,
  ReconciliationFilled,
  SlackCircleFilled,
  UserOutlined,
  QuestionCircleOutlined,
  DatabaseFilled,
} from "@ant-design/icons-vue";

const collapsed = ref<boolean>(false);
const selectedKeys = ref<string[]>(["1"]);
const showAIChat = ref<boolean>(false);
const showAIChatDialog = () => {
  showAIChat.value = true;
};
const router = useRouter();
const route = useRoute();

// 根据当前路由设置选中的菜单项
watch(
  () => route.meta.menuKey,
  (newKey) => {
    if (newKey) {
      selectedKeys.value = [JSON.stringify(newKey)];
    }
  },
  { immediate: true }
);

// 处理菜单点击事件
const handleMenuClick = ({ key }: { key: string }) => {
  switch (key) {
    case "1":
      router.push("/home");
      break;
    case "2":
      if (auth.user?.role === "teacher") {
        router.push("/home/t-class");
      } else {
        router.push("/home/s-class");
      }
      break;
    case "3":
      router.push("/home/smart-preparation");
      break;
    case "4":
      router.push("/home/community");
      break;
    case "5":
      router.push("/home/knowledgebase");
      break;
  }
};

const goToProfile = () => {
  router.push("/home/profile");
};
</script>

<style scoped>
.logo {
  height: 96px;
  background: transparent;
  display: flex;
  align-items: center;
  padding-left: 24px;
  overflow: hidden;
}

.logo-img {
  width: 60px;
  height: 60px;
  object-fit: contain;
  margin-right: 12px;
}

.system-name {
  margin-bottom: 0;
  font-size: 24px;
  font-weight: bold;
  color: #1890ff;
  white-space: nowrap;
  transition: opacity 0.3s;
}

.ant-layout-sider-collapsed .logo {
  padding-left: 12px;
  justify-content: flex-start;
}

.ant-layout-sider-collapsed .system-name {
  display: none;
}

.site-layout .site-layout-background {
  background: #fff;
}

:deep(.ant-layout-sider-light) {
  background-color: #f9fbff !important;
  border-right: 1px solid #f9fbff !important;
}

:deep(.ant-menu-light) {
  background-color: transparent !important;
}

.ant-menu-item .nav-text {
  display: inline-block;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.ant-menu-item:hover .nav-text {
  animation: textSlide 0.2s forwards;
}

@keyframes textSlide {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(12px);
  }
}

.ant-menu-item:nth-child(1) {
  background-color: #f0f9ff;
}

.ant-menu-item:hover {
  background-color: #e6f7ff !important;
}

.ant-menu-item-selected {
  background-color: #1890ff20 !important;
}

:deep(.ant-menu.ant-menu-root .ant-menu-item) {
  height: 72px !important;
  line-height: 72px !important;
  font-size: 20px !important;
  transition: all 0.3s ease !important;
  border-radius: 20px !important;
  margin: 4px 4px !important;

  .anticon {
    font-size: 24px !important;
    margin-right: 18px !important;
    margin-left: 0px !important;
  }
}

.user-info-container {
  padding: 16px;
  background: inherit;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
}

.username {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
  transition: opacity 0.2s;
  margin: auto;
}

.user-info:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.nav-avatar {
  flex-shrink: 0;
  transition: all 0.3s;
  padding: 0;
  border: none;
}

.ant-layout-sider-collapsed .user-info {
  justify-content: center;
  padding: 8px 0;
}

.ant-layout-sider-collapsed .username {
  display: none;
}

.user-info:active {
  transform: scale(0.95);
}

.g-card {
  background: #edf6fbcc no-repeat center center fixed;
  background-size: cover;
  border-radius: 16px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  width: 100%;
  height: 100%;
  overflow: hidden;
  margin: 10px;
}

/* AI聊天窗口样式 */
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #fafafa;
}

.message {
  margin-bottom: 16px;
}

.message-content {
  display: flex;
  align-items: flex-start;
  max-width: 90%;
  margin: 0 auto;
}

.ai-avatar,
.user-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 8px;
}

.ai-avatar {
  background-color: #1890ff;
  color: white;
}

.user-avatar {
  background-color: #f0f0f0;
  color: #666;
}

.text-content {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.5;
  word-break: break-word;
}

.message.assistant .text-content {
  background-color: #e6f7ff;
  color: #333;
  margin-left: 8px;
}

.message.user .text-content {
  background-color: #1890ff;
  color: white;
  margin-right: 8px;
}

.message.user {
  justify-content: flex-end;
}

.message.user .message-content {
  flex-direction: row-reverse;
}

.chat-input {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  background-color: white;
}

:deep(.ant-input-search-button) {
  height: 40px !important;
}
</style>
