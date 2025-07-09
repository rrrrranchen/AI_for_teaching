<template>
  <div class="knowledge-management">
    <a-layout>
      <!-- 简洁顶部导航栏 -->
      <a-layout-header class="header">
        <a-menu
          v-model:selectedKeys="activeTab"
          mode="horizontal"
          class="nav-menu"
        >
          <a-menu-item key="categories">
            <template #icon>
              <folder-outlined />
            </template>
            系统类目
          </a-menu-item>
          <a-menu-item key="knowledge-bases">
            <template #icon>
              <database-outlined />
            </template>
            知识库管理
          </a-menu-item>
        </a-menu>
      </a-layout-header>

      <!-- 内容区域 -->
      <a-layout-content class="content">
        <!-- 类目管理 -->
        <div v-show="activeTab[0] === 'categories'" class="tab-content-wrapper">
          <div class="tab-content">
            <AdminCategories ref="userCategories" />
          </div>
        </div>

        <!-- 知识库管理 -->
        <div
          v-show="activeTab[0] === 'knowledge-bases'"
          class="tab-content-wrapper"
        >
          <div class="tab-content">
            <KnowledgeBases ref="knowledgeBases" />
          </div>
        </div>
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { FolderOutlined, DatabaseOutlined } from "@ant-design/icons-vue";
import AdminCategories from "@/components/adminknowledge/AdminCategoriesList.vue";
import KnowledgeBases from "@/components/adminknowledge/AdminKnowledgeBasesList.vue";

const activeTab = ref<string[]>(["categories"]);
const userCategories = ref();
const knowledgeBases = ref();
</script>

<style scoped>
.knowledge-management {
  height: 100%;
}

.header {
  height: 75px;
  padding: 0 20px;
  background: #edf6fbcc;
  display: flex;
  align-items: center;
}

.nav-menu {
  width: 100%;
  line-height: 46px;
  border-bottom: none;
}

.content {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 48px);
}

.tab-content-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
}

.tab-content {
  width: 70%;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
