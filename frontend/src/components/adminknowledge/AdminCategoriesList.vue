<template>
  <div class="admin-categories-container">
    <div class="header">
      <h2>类目管理</h2>
      <div class="search-bar">
        <a-input-search
          v-model:value="searchParams.name"
          placeholder="搜索类目名称"
          style="width: 300px"
          @search="handleSearch"
          allow-clear
        />
        <a-select
          v-model:value="searchParams.type"
          placeholder="类目类型"
          style="width: 120px; margin-left: 8px"
          allow-clear
        >
          <a-select-option value="structural">结构化</a-select-option>
          <a-select-option value="non_structural">非结构化</a-select-option>
        </a-select>
        <a-select
          v-model:value="searchParams.is_system"
          placeholder="类目属性"
          style="width: 120px; margin-left: 8px"
          allow-clear
        >
          <a-select-option :value="true">系统类目</a-select-option>
          <a-select-option :value="false">用户类目</a-select-option>
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
      <a-button type="primary" @click="categoryCreateModal.showModal()">
        <template #icon><plus-outlined /></template>
        新建系统类目
      </a-button>
    </div>

    <a-alert
      message="管理员操作提示"
      description="您可以管理所有类目，但只能为系统类目上传/删除文件"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <a-list
      :data-source="categories"
      :loading="loading"
      :pagination="pagination"
      item-layout="vertical"
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
              <file-text-outlined />
              {{ item.file_count }} 个文件
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
            <a-button
              type="link"
              size="small"
              @click="showUploadModal(item)"
              v-if="item.is_system"
            >
              <upload-outlined /> 上传文件
            </a-button>
          </template>

          <a-list-item-meta>
            <template #title>
              <a @click="toggleExpand(item.id)">
                {{ item.name }}
                <a-tag
                  :color="
                    item.category_type === 'structural' ? 'blue' : 'purple'
                  "
                >
                  {{
                    item.category_type === "structural" ? "结构化" : "非结构化"
                  }}
                </a-tag>
                <a-tag v-if="item.is_system" color="red">系统类目</a-tag>
              </a>
              <down-outlined
                v-if="!expandedCategories.includes(item.id)"
                style="margin-left: 8px"
                @click="toggleExpand(item.id)"
              />
              <up-outlined
                v-else
                style="margin-left: 8px"
                @click="toggleExpand(item.id)"
              />
            </template>
            <template #description>
              {{ item.description || "暂无描述" }}
            </template>
          </a-list-item-meta>
          <div
            v-if="expandedCategories.includes(item.id)"
            class="category-files"
          >
            <a-spin :spinning="!item.files">
              <div
                class="file-actions"
                v-if="item.files && item.files.length > 0 && item.is_system"
              >
                <a-button
                  type="primary"
                  danger
                  size="small"
                  :disabled="selectedFileIds.length === 0"
                  @click="handleBatchDelete(item.id)"
                >
                  <template #icon><delete-outlined /></template>
                  批量删除({{ selectedFileIds.length }})
                </a-button>
                <a-checkbox
                  v-model:checked="selectAllFiles"
                  @change="
                    (e:any) => handleSelectAllChange(item.files, e.target.checked)
                  "
                  style="margin-left: 8px"
                >
                  全选
                </a-checkbox>
              </div>

              <a-empty
                v-if="item.files && item.files.length === 0"
                description="暂无文件"
              />
              <a-list
                v-else-if="item.files"
                :data-source="item.files"
                size="small"
                bordered
                style="margin-top: 12px"
              >
                <template #renderItem="{ item: file }">
                  <a-list-item>
                    <template #extra>
                      <a-checkbox
                        v-model:checked="file.checked"
                        @change="handleFileCheckChange(file)"
                        v-if="item.is_system"
                      />
                    </template>
                    <a-list-item-meta>
                      <template #title>
                        <a :href="file.file_path" target="_blank" download>
                          <component
                            :is="getFileIcon(file.name)"
                            style="margin-right: 8px"
                          />
                          {{ file.name }}
                        </a>
                        <span
                          style="
                            color: rgba(0, 0, 0, 0.45);
                            font-size: 12px;
                            margin-left: 8px;
                          "
                        >
                          {{ formatDate(file.created_at) }}
                        </span>
                      </template>
                    </a-list-item-meta>
                    <template #actions v-if="item.is_system">
                      <a-button
                        danger
                        size="small"
                        @click="handleDeleteFile(item.id, file.id)"
                      >
                        <template #icon><delete-outlined /></template>
                        删除
                      </a-button>
                    </template>
                  </a-list-item>
                </template>
              </a-list>
            </a-spin>
          </div>
        </a-list-item>
      </template>
    </a-list>

    <AdminCategoryCreateModal
      ref="categoryCreateModal"
      @created="fetchCategories"
    />
    <AdminCategoryUploadModal
      ref="categoryUploadModal"
      :category-id="currentCategory?.id || 0"
      :category-name="currentCategory?.name || ''"
      :category-type="currentCategory?.type || 'structural'"
      @uploaded="fetchCategories"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, reactive, onMounted } from "vue";
import { message, Modal } from "ant-design-vue";
import {
  PlusOutlined,
  DownOutlined,
  UpOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  UploadOutlined,
  FileOutlined,
  DeleteOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FilePptOutlined,
  FilePdfOutlined,
  SearchOutlined,
  RedoOutlined,
  UserOutlined,
} from "@ant-design/icons-vue";
import {
  adminSearchCategories,
  adminGetCategoryFiles,
  adminDeleteCategoryFiles,
} from "@/api/knowledgebasemanage";
import AdminCategoryCreateModal from "./CategoryCreateModal.vue";
import AdminCategoryUploadModal from "./CategoryUploadModal.vue";

interface Category {
  id: number;
  name: string;
  description?: string;
  category_type: "structural" | "non_structural";
  created_at: string;
  updated_at?: string;
  is_public: boolean;
  is_system: boolean;
  file_count: number;
  author_name?: string;
  files?: any[];
}

interface SearchParams {
  name?: string;
  type?: "structural" | "non_structural";
  is_system?: boolean;
  page?: number;
  per_page?: number;
}

const loading = ref(false);
const categories = ref<Category[]>([]);
const expandedCategories = ref<number[]>([]);
const searchParams = reactive<SearchParams>({
  name: undefined,
  type: undefined,
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
    fetchCategories();
  },
});

const categoryCreateModal = ref();
const categoryUploadModal = ref();
const currentCategory = ref<{
  id: number;
  name: string;
  type: "structural" | "non_structural";
}>();

const selectedFileIds = ref<number[]>([]);
const selectAllFiles = ref(false);

onMounted(() => {
  fetchCategories();
});

const fetchCategories = async () => {
  loading.value = true;
  try {
    const result = await adminSearchCategories(searchParams);
    categories.value = result.data;
    pagination.total = result.pagination.total;
    pagination.current = result.pagination.current_page;
    pagination.pageSize = result.pagination.per_page;
  } catch (error) {
    message.error("获取类目列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  searchParams.page = 1;
  fetchCategories();
};

const resetSearch = () => {
  searchParams.name = undefined;
  searchParams.type = undefined;
  searchParams.is_system = undefined;
  searchParams.page = 1;
  fetchCategories();
};

const getFileIcon = (fileName: string) => {
  if (!fileName) return FileOutlined;

  const extension = fileName.split(".").pop()?.toLowerCase();

  switch (extension) {
    case "xls":
    case "xlsx":
    case "csv":
      return FileExcelOutlined;
    case "doc":
    case "docx":
      return FileWordOutlined;
    case "ppt":
    case "pptx":
      return FilePptOutlined;
    case "pdf":
      return FilePdfOutlined;
    case "txt":
      return FileOutlined;
    case "md":
      return FileOutlined;
    case "jpg":
    case "jpeg":
    case "png":
    case "gif":
      return FileOutlined;
    default:
      return FileOutlined;
  }
};

const handleFileCheckChange = (file: any) => {
  if (file.checked) {
    if (!selectedFileIds.value.includes(file.id)) {
      selectedFileIds.value.push(file.id);
    }
  } else {
    selectedFileIds.value = selectedFileIds.value.filter(
      (id) => id !== file.id
    );
  }
  selectAllFiles.value = false;
};

const handleSelectAllChange = (files: any[], checked: boolean) => {
  files.forEach((file) => {
    file.checked = checked;
  });

  if (checked) {
    selectedFileIds.value = files.map((file) => file.id);
  } else {
    selectedFileIds.value = [];
  }
};

const handleBatchDelete = (categoryId: number) => {
  if (selectedFileIds.value.length === 0) {
    message.warning("请先选择要删除的文件");
    return;
  }

  Modal.confirm({
    title: "确认删除",
    content: `确定要删除选中的 ${selectedFileIds.value.length} 个文件吗？`,
    okText: "确认",
    cancelText: "取消",
    onOk: async () => {
      try {
        const result = await adminDeleteCategoryFiles(
          categoryId,
          selectedFileIds.value
        );

        if (result.failed.length > 0) {
          message.warning(
            `成功删除 ${result.deleted.length} 个文件，${result.failed.length} 个文件删除失败`
          );
        } else {
          message.success(`成功删除 ${result.deleted.length} 个文件`);
        }

        await fetchCategoryFiles(categoryId);
        selectedFileIds.value = [];
        selectAllFiles.value = false;
      } catch (error) {
        message.error("批量删除文件失败");
        console.error(error);
      }
    },
  });
};

const handleDeleteFile = async (categoryId: number, fileId: number) => {
  try {
    await adminDeleteCategoryFiles(categoryId, [fileId]);
    message.success("文件删除成功");
    await fetchCategoryFiles(categoryId);
    selectedFileIds.value = selectedFileIds.value.filter((id) => id !== fileId);
  } catch (error) {
    message.error("文件删除失败");
    console.error(error);
  }
};

const fetchCategoryFiles = async (categoryId: number) => {
  try {
    const files = await adminGetCategoryFiles(categoryId);
    const checkedFiles = files.data.files.map((file: any) => ({
      ...file,
      checked: false,
    }));

    const category = categories.value.find((cat) => cat.id === categoryId);
    if (category) {
      category.files = checkedFiles;
    }
  } catch (error) {
    message.error("获取文件列表失败");
    console.error(error);
  }
};

const toggleExpand = async (categoryId: number) => {
  const index = expandedCategories.value.indexOf(categoryId);
  if (index === -1) {
    expandedCategories.value.push(categoryId);
    await fetchCategoryFiles(categoryId);
  } else {
    expandedCategories.value.splice(index, 1);
  }
};

const showUploadModal = (category: Category) => {
  if (!category.is_system) {
    message.warning("只能为系统类目上传文件");
    return;
  }
  currentCategory.value = {
    id: category.id,
    name: category.name,
    type: category.category_type,
  };
  categoryUploadModal.value.showModal();
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString();
};
</script>

<style scoped>
.admin-categories-container {
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

.category-files {
  margin-top: 12px;
  padding-left: 24px;
}

.file-actions {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
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
