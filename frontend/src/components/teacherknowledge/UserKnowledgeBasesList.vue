<template>
  <div class="knowledge-bases-container">
    <div class="header">
      <h2>我的知识库</h2>
      <div class="actions">
        <a-button type="primary" @click="knowledgeBaseCreateModal.showModal()">
          <template #icon><plus-outlined /></template>
          新建知识库
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
      item-layout="vertical"
      bordered
    >
      <template #renderItem="{ item }">
        <a-list-item style="background-color: #edf6fbcc">
          <template #actions>
            <span>
              <folder-outlined />
              {{ item.categories.length }} 个类目
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
            <!-- 新增单个知识库的类目操作按钮 -->
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
          </template>

          <a-list-item-meta>
            <template #title>
              <a style="font-size: large; margin-right: 8px">{{ item.name }}</a>
              <a-tag
                :color="item.base_type === 'structural' ? 'blue' : 'purple'"
              >
                {{ item.base_type === "structural" ? "结构化" : "非结构化" }}
              </a-tag>
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
                :color="cat.category_type === 'structural' ? 'blue' : 'purple'"
              >
                {{ cat.name }}
                <span style="margin-left: 4px; font-size: 12px">
                  ({{
                    cat.category_type === "structural" ? "结构化" : "非结构化"
                  }})
                </span>
              </a-tag>
            </div>
          </div>
        </a-list-item>
      </template>
    </a-list>

    <KnowledgeBaseCreateModal
      ref="knowledgeBaseCreateModal"
      @created="fetchKnowledgeBases"
    />
  </div>
  <!-- 添加类目模态框 -->
  <a-modal
    v-model:visible="addCategoriesVisible"
    :title="`为 ${currentKB?.name} 添加类目`"
    @ok="handleAddCategories"
    @cancel="addCategoriesVisible = false"
  >
    <a-select
      v-model:value="selectedCategories"
      mode="multiple"
      style="width: 100%"
      placeholder="请选择要添加的类目"
      :options="filteredCategoryOptions"
      :filter-option="filterOption"
    />
  </a-modal>

  <!-- 移除类目模态框 -->
  <a-modal
    v-model:visible="removeCategoriesVisible"
    :title="`从 ${currentKB?.name} 移除类目`"
    @ok="handleRemoveCategories"
    @cancel="removeCategoriesVisible = false"
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
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { message } from "ant-design-vue";
import {
  PlusOutlined,
  SyncOutlined,
  FolderOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  FolderAddOutlined,
} from "@ant-design/icons-vue";
import {
  getKnowledgeBases,
  getPendingUpdateKnowledgeBases,
  batchUpdateKnowledgeBases,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  batchAddCategoriesToKnowledgeBase,
  batchRemoveCategoriesFromKnowledgeBase,
  getCategories,
} from "@/api/knowledgebase";
import KnowledgeBaseCreateModal from "./KnowledgeBaseCreateModal.vue";

interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  stored_basename: string;
  author_id: number;
  is_public: boolean;
  need_update: boolean;
  created_at: string;
  updated_at?: string;
  file_path: string;
  base_type: "structural" | "non_structural";
  categories: {
    id: number;
    name: string;
  }[];
  updating?: boolean;
}

const loading = ref(false);
const batchUpdating = ref(false);
const knowledgeBases = ref<KnowledgeBase[]>([]);
const pendingUpdateKBs = ref<KnowledgeBase[]>([]);

const knowledgeBaseCreateModal = ref();

// 新增状态变量
const showUpdateProgress = ref(false);
const updateProgress = ref(0);
const updateStatus = ref<"active" | "success" | "exception">("active");
const updateStatusText = ref("正在更新知识库...");
const currentUpdatingKB = ref<KnowledgeBase | null>(null);
const updateInterval = ref<number | null>(null);

onMounted(() => {
  fetchKnowledgeBases();
});

const fetchKnowledgeBases = async () => {
  loading.value = true;
  try {
    const [allKBs, pendingKBs] = await Promise.all([
      getKnowledgeBases(),
      getPendingUpdateKnowledgeBases(),
    ]);

    knowledgeBases.value = allKBs.map((kb) => ({
      ...kb,
      updating: false,
    }));

    pendingUpdateKBs.value = pendingKBs;
  } catch (error) {
    message.error("获取知识库列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 修改单个知识库更新方法
const handleUpdateKB = async (kbId: number) => {
  const kb = knowledgeBases.value.find((kb) => kb.id === kbId);
  if (!kb) return;

  // 初始化进度状态
  kb.updating = true;
  currentUpdatingKB.value = kb;
  showUpdateProgress.value = true;
  updateProgress.value = 0;
  updateStatus.value = "active";
  updateStatusText.value = `正在更新 ${kb.name}...`;

  const startTime = Date.now();
  const duration = 20000; // 20秒模拟时长

  // 启动进度模拟
  updateInterval.value = window.setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(99, Math.floor((elapsed / duration) * 100));
    updateProgress.value = progress;
  }, 100);

  try {
    // 实际API调用
    await updateKnowledgeBase(kbId);

    // 清除定时器并完成进度
    if (updateInterval.value !== null) {
      window.clearInterval(updateInterval.value);
      updateInterval.value = null;
    }

    updateProgress.value = 100;
    updateStatus.value = "success";
    updateStatusText.value = "更新成功！";

    // 延迟关闭模态框让用户看到成功状态
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

    // 延迟关闭模态框让用户看到错误状态
    setTimeout(() => {
      showUpdateProgress.value = false;
    }, 1500);
  } finally {
    kb.updating = false;
    currentUpdatingKB.value = null;
  }
};
// 修改批量更新方法
const handleBatchUpdate = async () => {
  batchUpdating.value = true;
  showUpdateProgress.value = true;
  updateProgress.value = 0;
  updateStatus.value = "active";
  updateStatusText.value = `正在批量更新 ${pendingUpdateKBs.value.length} 个知识库...`;

  const startTime = Date.now();
  const duration = Math.max(20000, pendingUpdateKBs.value.length * 5000); // 根据数量调整时长

  // 启动进度模拟
  updateInterval.value = window.setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(99, Math.floor((elapsed / duration) * 100));
    updateProgress.value = progress;
  }, 100);

  try {
    const result = await batchUpdateKnowledgeBases();

    // 清除定时器并完成进度
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
    await deleteKnowledgeBase(kbId);
    message.success("知识库删除成功");
    fetchKnowledgeBases();
  } catch (error) {
    message.error("知识库删除失败");
    console.error(error);
  }
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString();
};

// 组件卸载时清理定时器
onUnmounted(() => {
  if (updateInterval.value !== null) {
    window.clearInterval(updateInterval.value);
  }
});

// 新增状态
const addCategoriesVisible = ref(false);
const removeCategoriesVisible = ref(false);
const currentKB = ref<KnowledgeBase | null>(null);
const selectedCategories = ref<number[]>([]);
const categoryOptions = ref<{ value: number; label: string; type: string }[]>(
  []
);

// 获取当前知识库可添加的类目选项（过滤已添加的）
const filteredCategoryOptions = computed(() => {
  if (!currentKB.value) return categoryOptions.value;
  const addedIds = currentKB.value.categories.map((c) => c.id);
  return categoryOptions.value.filter(
    (opt) =>
      !addedIds.includes(opt.value) && opt.type === currentKB.value?.base_type
  );
});

// 获取当前知识库已有类目选项
const currentKBCategoriesOptions = computed(() => {
  if (!currentKB.value) return [];
  return currentKB.value.categories.map((cat) => ({
    value: cat.id,
    label: cat.name,
  }));
});

// 显示添加类目模态框
const showAddCategoriesModal = async (kb: KnowledgeBase) => {
  currentKB.value = kb;
  selectedCategories.value = [];
  if (categoryOptions.value.length === 0) {
    await fetchCategories();
  }
  addCategoriesVisible.value = true;
};

// 显示移除类目模态框
const showRemoveCategoriesModal = async (kb: KnowledgeBase) => {
  currentKB.value = kb;
  selectedCategories.value = [];
  removeCategoriesVisible.value = true;
};

// 处理添加类目
const handleAddCategories = async () => {
  if (!currentKB.value || selectedCategories.value.length === 0) return;

  try {
    await batchAddCategoriesToKnowledgeBase(
      currentKB.value.id,
      selectedCategories.value
    );
    message.success("添加类目成功");
    fetchKnowledgeBases();
    addCategoriesVisible.value = false;
  } catch (error) {
    message.error("添加类目失败");
    console.error(error);
  }
};

// 处理移除类目
const handleRemoveCategories = async () => {
  if (!currentKB.value || selectedCategories.value.length === 0) return;

  try {
    await batchRemoveCategoriesFromKnowledgeBase(
      currentKB.value.id,
      selectedCategories.value
    );
    message.success("移除类目成功");
    fetchKnowledgeBases();
    removeCategoriesVisible.value = false;
  } catch (error) {
    message.error("移除类目失败");
    console.error(error);
  }
};

// 获取类目列表
const fetchCategories = async () => {
  try {
    const result = await getCategories();
    categoryOptions.value = [
      ...result.structured_categories.map((cat) => ({
        value: cat.id,
        label: `${cat.name} (结构化)`,
        type: "structural",
      })),
      ...result.non_structured_categories.map((cat) => ({
        value: cat.id,
        type: "non_structural",
        label: `${cat.name} (非结构化)`,
      })),
    ];
  } catch (error) {
    message.error("获取类目列表失败");
    console.error(error);
  }
};

// 筛选选项
const filterOption = (input: string, option: any) => {
  return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};
</script>

<style scoped>
.knowledge-bases-container {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
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
</style>
