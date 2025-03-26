<template>
  <a-layout has-sider>
    <a-layout-sider
      theme="light"
      :width="250"
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
          <span class="nav-text">我的班级</span>
        </a-menu-item>
        <a-menu-item key="3">
          <ReconciliationFilled />
          <span class="nav-text">智能备课</span>
        </a-menu-item>
        <a-menu-item key="4">
          <SlackCircleFilled />
          <span class="nav-text">社区</span>
        </a-menu-item>
        <a-menu-item key="5">
          <cloud-outlined />
          <span class="nav-text">nav 5</span>
        </a-menu-item>
        <a-menu-item key="6">
          <appstore-outlined />
          <span class="nav-text">nav 6</span>
        </a-menu-item>
        <a-menu-item key="7">
          <team-outlined />
          <span class="nav-text">nav 7</span>
        </a-menu-item>
        <a-menu-item key="8">
          <shop-outlined />
          <span class="nav-text">nav 8</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout
      :style="{
        marginLeft: collapsed ? '80px' : '250px',
        transition: 'margin 0.2s',
      }"
    >
      <a-layout-content :style="{ overflow: 'initial' }">
        <router-view />
      </a-layout-content>
      <a-layout-footer :style="{ textAlign: 'center' }"> </a-layout-footer>
    </a-layout>
  </a-layout>
</template>
<script lang="ts" setup>
import { ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";

import {
  HomeFilled,
  TeamOutlined,
  ReconciliationFilled,
  SlackCircleFilled,
  CloudOutlined,
  AppstoreOutlined,
  ShopOutlined,
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
      router.push("/home");
      break;
    case "2":
      router.push("/home/my-class");
      break;
    case "3":
      router.push("/home/smart-preparation");
      break;
    case "4":
      router.push("/home/community");
      break;
    // 其他菜单项...
  }
};
</script>
<style scoped>
.logo {
  height: 96px;
  background: transparent;
  display: flex;
  align-items: center;
  padding-left: 24px; /* 增加左侧内边距 */
  overflow: hidden;
}

.logo-img {
  width: 60px;
  height: 60px;
  object-fit: contain;
  margin-right: 12px; /* 只保留右侧外边距 */
}

.system-name {
  margin-bottom: 0;
  font-size: 24px;
  font-weight: bold;
  color: #1890ff;
  white-space: nowrap;
  transition: opacity 0.3s;
}

/* 折叠状态调整 */
.ant-layout-sider-collapsed .logo {
  padding-left: 12px; /* 折叠后减少左侧间距 */
  justify-content: flex-start; /* 确保折叠后仍然左对齐 */
}

.ant-layout-sider-collapsed .system-name {
  display: none;
}
.site-layout .site-layout-background {
  background: #fff;
}

/* 修改 light 主题侧边栏背景色 */
:deep(.ant-layout-sider-light) {
  background-color: #f9fbff !important; /* 改为浅灰色背景 */
  border-right: 1px solid #f9fbff !important; /* 添加右边框 */
}

/* 修改 light 主题菜单样式 */
:deep(.ant-menu-light) {
  background-color: transparent !important; /* 透明背景 */
}

/* 核心修复：确保过渡作用在文字元素上 */
.ant-menu-item .nav-text {
  display: inline-block;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); /* 明确指定过渡属性 */
}

/* 方案一：添加动画轨迹 */
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
  height: 72px !important; /* 增加高度 */
  line-height: 72px !important; /* 保持垂直居中 */
  font-size: 20px !important; /* 增大字体 */
  transition: all 0.3s ease !important;
  border-radius: 20px !important;
  margin: 4px 4px !important; /* 增加水平边距避免圆角被裁剪 */

  .anticon {
    font-size: 24px !important; /* 图标大小 */
    margin-right: 18px !important; /* 图标与文字间距 */
    margin-left: 0px !important;
  }
}
</style>
