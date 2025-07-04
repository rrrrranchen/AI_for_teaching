<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo" />
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="1">
          <pie-chart-outlined />
          <span>数据统计</span>
        </a-menu-item>
        <a-menu-item key="2">
          <desktop-outlined />
          <span>PPT模板</span>
        </a-menu-item>
        <a-menu-item key="3">
          <user-outlined />
          <span>用户管理</span>
        </a-menu-item>
        <a-menu-item key="4">
          <team-outlined />
          <span>课程班管理</span>
        </a-menu-item>
        <a-menu-item key="5">
          <file-outlined />
          <span>本地知识库管理</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header
        style="
          height: 6vh;
          background: #fff;
          padding: 0 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
        "
      >
        <!-- Left side - Logo and system name -->
        <div style="display: flex; align-items: center; gap: 12px">
          <img
            src="../assets/sys_logo.png"
            alt="Logo"
            style="height: 32px; width: 32px"
          />
          <span style="font-size: 18px; font-weight: 600; color: #1890ff"
            >教备通管理端</span
          >
        </div>

        <!-- Right side - User info -->
        <div style="display: flex; align-items: center; gap: 12px">
          <a-button type="primary" danger @click="handleLogout">
            <template #icon><logout-outlined /></template>
            退出登录
          </a-button>
          <span v-if="!collapsed" class="username" style="font-weight: 500">{{
            auth.user?.username
          }}</span>
          <a-avatar
            v-if="auth.user?.avatar"
            :size="40"
            :src="'http://localhost:5000/' + auth.user?.avatar"
            class="nav-avatar"
          >
          </a-avatar>
          <a-avatar
            v-else
            :size="40"
            class="nav-avatar"
            style="background-color: #1890ff"
          >
            <UserOutlined />
          </a-avatar>
        </div>
      </a-layout-header>
      <a-layout-content style="height: 94vh; overflow-y: auto">
        <!-- <a-breadcrumb style="margin: 16px 0">
          <a-breadcrumb-item>User</a-breadcrumb-item>
          <a-breadcrumb-item>Bill</a-breadcrumb-item>
        </a-breadcrumb> -->
        <div
          :style="{ padding: '12px', background: '#fff', minHeight: '360px' }"
        >
          <router-view> </router-view>
        </div>
      </a-layout-content>
      <!-- <a-layout-footer style="text-align: center">
        Ant Design ©2018 Created by Ant UED
      </a-layout-footer> -->
    </a-layout>
  </a-layout>
</template>
<script lang="ts" setup>
import { ref, watch } from "vue";
import { message } from "ant-design-vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();
import {
  PieChartOutlined,
  DesktopOutlined,
  UserOutlined,
  TeamOutlined,
  FileOutlined,
  LogoutOutlined,
} from "@ant-design/icons-vue";
const collapsed = ref<boolean>(false);
const selectedKeys = ref<string[]>(["1"]);

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
      router.push("/admin");
      break;
    case "2":
      router.push("/admin/ppt-manage");
      break;
    case "3":
      router.push("/admin/user-manage");
      break;
    case "4":
      router.push("/admin/class-manage");
      break;
    case "5":
      router.push("/admin/local-knowledge-base");
      break;
  }
};

const handleLogout = async () => {
  try {
    await auth.logout();
    message.success("已安全退出");
  } catch (error) {
    message.error("退出登录失败");
  }
};
</script>
<style scoped>
#components-layout-demo-side .logo {
  height: 32px;
  margin: 16px;
  background: rgba(255, 255, 255, 0.3);
}

.site-layout .site-layout-background {
  background: #fff;
}
[data-theme="dark"] .site-layout .site-layout-background {
  background: #141414;
}
</style>
