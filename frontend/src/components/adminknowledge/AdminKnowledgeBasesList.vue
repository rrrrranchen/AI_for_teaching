<template>
  <div class="admin-knowledge-bases-container">
    <div class="header">
      <h2>知识库管理</h2>
      <div class="search-bar">
        <a-input-search
          v-model:value="searchParams.name"
          placeholder="搜索知识库名称"
          style="width: 300px"
          @search="handleSearch"
          allow-clear
        />
        <a-select
          v-model:value="searchParams.base_type"
          placeholder="知识库类型"
          style="width: 120px; margin-left: 8px"
          allow-clear
        >
          <a-select-option value="structural">结构化</a-select-option>
          <a-select-option value="non_structural">非结构化</a-select-option>
        </a-select>
        <a-select
          v-model:value="searchParams.is_system"
          placeholder="知识库属性"
          style="width: 120px; margin-left: 8px"
          allow-clear
        >
          <a-select-option :value="true">系统知识库</a-select-option>
          <a-select-option :value="false">用户知识库</a-select-option>
        </a-select>
        <a-button type="primary" @click="handleSearch" style="margin-left: 8px">
          <template #icon><search-outlined /></template>
          搜索
        </a-button>
        <a-button @click="resetSearch" style="margin-left: 8px">
          <template #icon><redo-outlined /></template>
          重置
        </a-button>
      </div>
      <div class="actions">
        <a-button type="primary" @click="knowledgeBaseCreateModal.showModal()">
          <template #icon><plus-outlined /></template>
          新建系统知识库
        </a-button>
        <a-button
          @click="handleBatchUpdate"
          :loading="batchUpdating"
          :disabled="pendingUpdateKBs.length === 0"
          style="margin-left: 8px"
        >
          <template #icon><sync-outlined /></template>
          批量更新({{ pendingUpdateKBs.length }})
        </a-button>
      </div>
    </div>

    <a-alert
      message="管理员操作提示"
      description="您可以管理所有知识库，系统知识库将由管理员维护"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <a-modal
      v-model:visible="showUpdateProgress"
      title="知识库更新中"
      :footer="null"
      :closable="false"
      :width="600"
    >
      <a-progress
        :percent="updateProgress"
        :status="updateStatus"
        :stroke-color="{
          '0%': '#108ee9',
          '100%': '#87d068',
        }"
      />
      <p style="text-align: center; margin-top: 8px">
        {{ updateStatusText }}
        <span v-if="currentUpdatingKB">{{ currentUpdatingKB.name }}</span>
      </p>
    </a-modal>

    <a-list
      :data-source="knowledgeBases"
      :loading="loading"
      :pagination="pagination"
      item-layout="vertical"
      bordered
    >
      <template #renderItem="{ item }">
        <a-list-item
          :style="{
            backgroundColor: item.is_system ? '#f0f7ff' : '#f6f6f6',
            marginBottom: '8px',
          }"
        >
          <template #actions>
            <span>
              <folder-outlined />
              {{ item.categories.length }} 个类目
            </span>
            <span>
              <user-outlined />
              {{ item.author_name || "系统" }}
            </span>
            <span>
              <clock-circle-outlined />
              {{ formatDate(item.created_at) }}
            </span>
            <a-tag :color="item.is_public ? 'green' : 'orange'">
              {{ item.is_public ? "公开" : "私有" }}
            </a-tag>
            <a-tag :color="item.need_update ? 'red' : 'green'">
              {{ item.need_update ? "需更新" : "已更新" }}
            </a-tag>
            <a-button
              type="link"
              size="small"
              @click="handleUpdateKB(item.id)"
              :loading="item.updating"
              :disabled="!item.need_update"
            >
              <sync-outlined /> 更新
            </a-button>
            <a-popconfirm
              title="确定要删除这个知识库吗？"
              @confirm="handleDeleteKB(item.id)"
            >
              <a-button type="link" danger size="small">
                <delete-outlined /> 删除
              </a-button>
            </a-popconfirm>
            <a-button
              type="link"
              size="small"
              @click="showAddCategoriesModal(item)"
            >
              <template #icon><folder-add-outlined /></template>
              添加类目
            </a-button>
            <a-button
              type="link"
              danger
              size="small"
              @click="showRemoveCategoriesModal(item)"
              :disabled="item.categories.length === 0"
            >
              <template #icon><delete-outlined /></template>
              移除类目
            </a-button>
            <a-button type="link" size="small" @click="showMap">
              <template #icon><RadarChartOutlined /></template>
              知识图谱
            </a-button>
          </template>

          <a-list-item-meta>
            <template #title>
              <a style="font-size: large; margin-right: 8px">{{ item.name }}</a>
              <a-tag
                :color="item.base_type === 'structural' ? 'blue' : 'purple'"
              >
                {{ item.base_type === "structural" ? "结构化" : "非结构化" }}
              </a-tag>
              <a-tag v-if="item.is_system" color="red">系统知识库</a-tag>
            </template>
            <template #description>
              {{ item.description || "暂无描述" }}
            </template>
          </a-list-item-meta>

          <div class="kb-categories" v-if="item.categories.length > 0">
            <h4>关联类目:</h4>
            <div class="category-tags">
              <a-tag
                v-for="cat in item.categories"
                :key="cat.id"
                :color="cat.type === 'structural' ? 'blue' : 'purple'"
              >
                {{ cat.name }}
                <span style="margin-left: 4px; font-size: 12px">
                  ({{ cat.type === "structural" ? "结构化" : "非结构化" }})
                </span>
              </a-tag>
            </div>
          </div>
        </a-list-item>
      </template>
    </a-list>

    <AdminKnowledgeBaseCreateModal
      ref="knowledgeBaseCreateModal"
      @created="fetchKnowledgeBases"
    />

    <!-- 添加类目模态框 -->
    <a-modal
      v-model:visible="addCategoriesVisible"
      :title="`为 ${currentKB?.name} 添加类目`"
      @ok="handleAddCategories"
      @cancel="addCategoriesVisible = false"
      :confirm-loading="categoriesLoading"
    >
      <a-alert
        v-if="currentKB"
        :message="`知识库类型: ${
          currentKB.base_type === 'structural' ? '结构化' : '非结构化'
        }`"
        description="只能添加与知识库类型相同的类目"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-select
        v-model:value="selectedCategories"
        mode="multiple"
        style="width: 100%"
        placeholder="请选择要添加的类目"
        :options="filteredCategoryOptions"
        :filter-option="filterOption"
        :loading="categoriesLoading"
      />
    </a-modal>

    <!-- 移除类目模态框 -->
    <a-modal
      v-model:visible="removeCategoriesVisible"
      :title="`从 ${currentKB?.name} 移除类目`"
      @ok="handleRemoveCategories"
      @cancel="removeCategoriesVisible = false"
      :confirm-loading="categoriesLoading"
    >
      <a-select
        v-model:value="selectedCategories"
        mode="multiple"
        style="width: 100%"
        placeholder="请选择要移除的类目"
        :options="currentKBCategoriesOptions"
        :filter-option="filterOption"
      />
    </a-modal>

    <knowledgeMap v-model:visible="showKMap" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted, onUnmounted } from "vue";
import { message } from "ant-design-vue";
import {
  PlusOutlined,
  SyncOutlined,
  FolderOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  FolderAddOutlined,
  SearchOutlined,
  RedoOutlined,
  UserOutlined,
  RadarChartOutlined,
} from "@ant-design/icons-vue";
import {
  adminGetKnowledgeBases,
  adminBatchUpdateSystemKnowledgeBases,
  adminBatchDeleteKnowledgeBases,
  adminUpdateSingleKnowledgeBase,
  adminBatchAddCategoriesToKnowledgeBase,
  adminBatchRemoveCategoriesFromKnowledgeBase,
  adminSearchCategories,
} from "@/api/knowledgebasemanage";
import AdminKnowledgeBaseCreateModal from "./KnowledgeBaseCreateModal.vue";
import { type KnowledgeBase } from "@/api/knowledgebase";
import knowledgeMap from "@/components/knowledgeMap.vue";

const showKMap = ref<boolean>(false);
const showMap = () => {
  showKMap.value = true;
};

interface SearchParams {
  name?: string;
  base_type?: "structural" | "non_structural";
  is_system?: boolean;
  author_id?: number;
  author_name?: string;
  page?: number;
  per_page?: number;
}

const loading = ref(false);
const batchUpdating = ref(false);
const knowledgeBases = ref<KnowledgeBase[]>([]);
const pendingUpdateKBs = ref<KnowledgeBase[]>([]);
const searchParams = reactive<SearchParams>({
  name: undefined,
  base_type: undefined,
  is_system: undefined,
  page: 1,
  per_page: 10,
});
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  onChange: (page: number, pageSize: number) => {
    searchParams.page = page;
    searchParams.per_page = pageSize;
    fetchKnowledgeBases();
  },
});

const knowledgeBaseCreateModal = ref();

// 更新状态
const showUpdateProgress = ref(false);
const updateProgress = ref(0);
const updateStatus = ref<"active" | "success" | "exception">("active");
const updateStatusText = ref("正在更新知识库...");
const currentUpdatingKB = ref<KnowledgeBase | null>(null);
const updateInterval = ref<number | null>(null);

// 类目操作状态
const addCategoriesVisible = ref(false);
const removeCategoriesVisible = ref(false);
const currentKB = ref<KnowledgeBase | null>(null);
const selectedCategories = ref<number[]>([]);
const categoryOptions = ref<{ value: number; label: string; type: string }[]>(
  []
);
const categoriesLoading = ref(false);

onMounted(() => {
  fetchKnowledgeBases();
});

const fetchKnowledgeBases = async () => {
  loading.value = true;
  try {
    const result = await adminGetKnowledgeBases(searchParams);

    knowledgeBases.value = result.data.map((kb: KnowledgeBase) => ({
      ...kb,
      updating: false,
    }));

    // 获取需要更新的知识库
    pendingUpdateKBs.value = knowledgeBases.value.filter(
      (kb) => kb.need_update
    );

    pagination.total = result.pagination.total;
    pagination.current = result.pagination.current_page;
    pagination.pageSize = result.pagination.per_page;
  } catch (error) {
    message.error("获取知识库列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  searchParams.page = 1;
  fetchKnowledgeBases();
};

const resetSearch = () => {
  searchParams.name = undefined;
  searchParams.base_type = undefined;
  searchParams.is_system = undefined;
  searchParams.page = 1;
  fetchKnowledgeBases();
};

const handleUpdateKB = async (kbId: number) => {
  const kb = knowledgeBases.value.find((kb) => kb.id === kbId);
  if (!kb) return;

  kb.updating = true;
  currentUpdatingKB.value = kb;
  showUpdateProgress.value = true;
  updateProgress.value = 0;
  updateStatus.value = "active";
  updateStatusText.value = `正在更新 ${kb.name}...`;

  const startTime = Date.now();
  const duration = 20000;

  updateInterval.value = window.setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(99, Math.floor((elapsed / duration) * 100));
    updateProgress.value = progress;
  }, 100);

  try {
    await adminUpdateSingleKnowledgeBase(kbId);

    if (updateInterval.value !== null) {
      window.clearInterval(updateInterval.value);
      updateInterval.value = null;
    }

    updateProgress.value = 100;
    updateStatus.value = "success";
    updateStatusText.value = "更新成功！";

    setTimeout(() => {
      showUpdateProgress.value = false;
      message.success(`${kb.name} 更新成功`);
      fetchKnowledgeBases();
    }, 800);
  } catch (error) {
    if (updateInterval.value !== null) {
      window.clearInterval(updateInterval.value);
      updateInterval.value = null;
    }

    updateProgress.value = 100;
    updateStatus.value = "exception";
    updateStatusText.value = "更新失败";

    message.error(`${kb.name} 更新失败`);
    console.error(error);

    setTimeout(() => {
      showUpdateProgress.value = false;
    }, 1500);
  } finally {
    kb.updating = false;
    currentUpdatingKB.value = null;
  }
};

const handleBatchUpdate = async () => {
  batchUpdating.value = true;
  showUpdateProgress.value = true;
  updateProgress.value = 0;
  updateStatus.value = "active";
  updateStatusText.value = `正在批量更新 ${pendingUpdateKBs.value.length} 个知识库...`;

  const startTime = Date.now();
  const duration = Math.max(20000, pendingUpdateKBs.value.length * 5000);

  updateInterval.value = window.setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(99, Math.floor((elapsed / duration) * 100));
    updateProgress.value = progress;
  }, 100);

  try {
    const result = await adminBatchUpdateSystemKnowledgeBases();

    if (updateInterval.value !== null) {
      window.clearInterval(updateInterval.value);
      updateInterval.value = null;
    }

    updateProgress.value = 100;
    updateStatus.value = "success";
    updateStatusText.value = `批量更新完成 (成功 ${result.updated_count} 个)`;

    setTimeout(() => {
      showUpdateProgress.value = false;
      message.success(`批量更新完成，成功 ${result.updated_count} 个`);
      fetchKnowledgeBases();
    }, 800);
  } catch (error) {
    if (updateInterval.value !== null) {
      window.clearInterval(updateInterval.value);
      updateInterval.value = null;
    }

    updateProgress.value = 100;
    updateStatus.value = "exception";
    updateStatusText.value = "批量更新失败";

    message.error("批量更新失败");
    console.error(error);

    setTimeout(() => {
      showUpdateProgress.value = false;
    }, 1500);
  } finally {
    batchUpdating.value = false;
  }
};

const handleDeleteKB = async (kbId: number) => {
  try {
    const kbIds = [kbId];
    await adminBatchDeleteKnowledgeBases(kbIds);
    message.success("知识库删除成功");
    fetchKnowledgeBases();
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || "知识库删除失败";
    message.error(errorMessage);
    console.error(error);
  }
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString();
};

// 类目操作相关方法
const fetchCategories = async () => {
  categoriesLoading.value = true;
  try {
    const result = await adminSearchCategories({
      is_system: true,
      per_page: 1000,
    });

    categoryOptions.value = result.data.map((cat: any) => ({
      value: cat.id,
      label: `${cat.name} (${
        cat.category_type === "structural" ? "结构化" : "非结构化"
      })`,
      type: cat.category_type,
    }));
  } catch (error) {
    message.error("获取系统类目列表失败");
    console.error(error);
  } finally {
    categoriesLoading.value = false;
  }
};

const filteredCategoryOptions = computed(() => {
  if (!currentKB.value) return categoryOptions.value;
  const addedIds = currentKB.value.categories.map((c) => c.id);
  return categoryOptions.value.filter(
    (opt) =>
      !addedIds.includes(opt.value) && opt.type === currentKB.value?.base_type
  );
});

const currentKBCategoriesOptions = computed(() => {
  if (!currentKB.value) return [];
  return currentKB.value.categories.map((cat) => ({
    value: cat.id,
    label: cat.name,
  }));
});

const showAddCategoriesModal = async (kb: KnowledgeBase) => {
  currentKB.value = kb;
  selectedCategories.value = [];
  if (categoryOptions.value.length === 0) {
    await fetchCategories();
  }
  addCategoriesVisible.value = true;
};

const showRemoveCategoriesModal = (kb: KnowledgeBase) => {
  currentKB.value = kb;
  selectedCategories.value = [];
  removeCategoriesVisible.value = true;
};

const handleAddCategories = async () => {
  if (!currentKB.value || selectedCategories.value.length === 0) return;

  try {
    await adminBatchAddCategoriesToKnowledgeBase(
      currentKB.value.id,
      selectedCategories.value
    );
    message.success("添加类目成功");
    fetchKnowledgeBases();
    addCategoriesVisible.value = false;
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || "添加类目失败";
    message.error(errorMessage);
    console.error(error);
  }
};

const handleRemoveCategories = async () => {
  if (!currentKB.value || selectedCategories.value.length === 0) return;

  try {
    await adminBatchRemoveCategoriesFromKnowledgeBase(
      currentKB.value.id,
      selectedCategories.value
    );
    message.success("移除类目成功");
    fetchKnowledgeBases();
    removeCategoriesVisible.value = false;
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || "移除类目失败";
    message.error(errorMessage);
    console.error(error);
  }
};

const filterOption = (input: string, option: any) => {
  return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};

// 组件卸载时清理定时器
onUnmounted(() => {
  if (updateInterval.value !== null) {
    window.clearInterval(updateInterval.value);
  }
});
</script>

<style scoped>
.admin-knowledge-bases-container {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}
.search-bar {
  display: flex;
  align-items: center;
  flex-grow: 1;
  max-width: 800px;
  margin-right: 16px;
}
.actions {
  display: flex;
  align-items: center;
}
.kb-categories {
  margin-top: 12px;
}
.kb-categories h4 {
  margin-bottom: 8px;
  font-weight: 500;
}
.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
  .search-bar {
    width: 100%;
    margin-bottom: 16px;
    margin-right: 0;
  }
}
</style>
