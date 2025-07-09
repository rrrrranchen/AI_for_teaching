<template>
  <a-modal
    v-model:visible="visible"
    title="关联知识库"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
    width="800px"
  >
    <div class="knowledge-base-container">
      <div class="search-section">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索知识库"
          @search="handleSearch"
          style="width: 300px"
        />
      </div>

      <a-table
        :columns="columns"
        :data-source="filteredKnowledgeBases"
        :row-selection="rowSelection"
        :pagination="false"
        :loading="loading"
        rowKey="id"
        size="middle"
        class="knowledge-base-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag
              :color="record.base_type === 'structural' ? 'blue' : 'purple'"
            >
              {{ record.base_type === "structural" ? "结构化" : "非结构化" }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'public'">
            <a-tag :color="record.is_public ? 'green' : 'orange'">
              {{ record.is_public ? "公开" : "私有" }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'categories'">
            <div class="category-tags">
              <a-tag v-for="cat in record.categories" :key="cat.id">
                {{ cat.name }}
              </a-tag>
            </div>
          </template>
        </template>
      </a-table>
    </div>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, computed, defineEmits, defineExpose, defineProps } from "vue";
import { message } from "ant-design-vue";
import {
  getKnowledgeBases,
  addKnowledgeBasesToCourseclass,
  type KnowledgeBase,
} from "@/api/knowledgebase";

const props = defineProps({
  courseclassId: {
    type: Number,
    required: true,
  },
  currentKnowledgeBases: {
    type: Array as () => KnowledgeBase[],
    default: () => [],
  },
});

const emit = defineEmits(["linked"]);

const visible = ref(false);
const confirmLoading = ref(false);
const loading = ref(false);
const knowledgeBases = ref<KnowledgeBase[]>([]);
const selectedKnowledgeBaseIds = ref<number[]>([]);
const searchText = ref("");

const columns = [
  {
    title: "知识库名称",
    dataIndex: "name",
    key: "name",
    width: "25%",
  },
  {
    title: "类型",
    key: "type",
    width: "15%",
  },
  {
    title: "可见性",
    key: "public",
    width: "15%",
  },
  {
    title: "关联类目",
    key: "categories",
    width: "45%",
  },
];

const filteredKnowledgeBases = computed(() => {
  if (!searchText.value) return knowledgeBases.value;
  return knowledgeBases.value.filter(
    (kb) =>
      kb.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
      kb.description?.toLowerCase().includes(searchText.value.toLowerCase())
  );
});

const rowSelection = computed(() => ({
  selectedRowKeys: selectedKnowledgeBaseIds.value,
  onChange: (selectedRowKeys: number[]) => {
    selectedKnowledgeBaseIds.value = selectedRowKeys;
  },
  getCheckboxProps: (record: KnowledgeBase) => ({
    disabled: props.currentKnowledgeBases.some((kb) => kb.id === record.id),
  }),
}));

const showModal = async () => {
  visible.value = true;
  if (knowledgeBases.value.length === 0) {
    await fetchKnowledgeBases();
  }
  // 初始化已选中的知识库
  selectedKnowledgeBaseIds.value = props.currentKnowledgeBases.map(
    (kb) => kb.id
  );
};

const fetchKnowledgeBases = async () => {
  try {
    loading.value = true;
    const data = await getKnowledgeBases();
    knowledgeBases.value = data;
  } catch (error) {
    message.error("获取知识库列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
};

const handleOk = async () => {
  try {
    confirmLoading.value = true;
    await addKnowledgeBasesToCourseclass(
      props.courseclassId,
      selectedKnowledgeBaseIds.value
    );
    message.success("关联知识库成功");
    emit("linked");
    visible.value = false;
  } catch (error) {
    message.error("关联知识库失败");
    console.error(error);
  } finally {
    confirmLoading.value = false;
  }
};

const handleCancel = () => {
  visible.value = false;
};

defineExpose({
  showModal,
});
</script>

<style scoped>
.knowledge-base-container {
  padding: 16px;
}

.search-section {
  margin-bottom: 16px;
}

.knowledge-base-table {
  margin-top: 16px;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
