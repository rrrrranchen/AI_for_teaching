<template>
  <div class="user-categories-container">
    <div class="header">
      <h2>我的类目</h2>
      <a-button type="primary" @click="categoryCreateModal.showModal()">
        <template #icon><plus-outlined /></template>
        新建类目
      </a-button>
    </div>

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="all" tab="全部类目"></a-tab-pane>
      <a-tab-pane key="structural" tab="结构化类目"></a-tab-pane>
      <a-tab-pane key="non_structural" tab="非结构化类目"></a-tab-pane>
    </a-tabs>

    <a-list
      :data-source="filteredCategories"
      :loading="loading"
      item-layout="vertical"
    >
      <template #renderItem="{ item }">
        <a-list-item style="background-color: #edf6fbcc; margin-bottom: 8px">
          <template #actions>
            <span>
              <file-text-outlined />
              {{ item.file_count }} 个文件
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
              v-if="!item.is_system"
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
              />
              <up-outlined v-else style="margin-left: 8px" />
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
                v-if="item.files && item.files.length > 0"
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
                      />
                    </template>
                    <a-list-item-meta>
                      <template #title>
                        <a
                          :href="'http://localhost:5000/' + file.url"
                          target="_blank"
                          download
                        >
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
                    <template #actions>
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

    <CategoryCreateModal ref="categoryCreateModal" @created="fetchCategories" />
    <CategoryUploadModal
      ref="categoryUploadModal"
      :category-id="currentCategory?.id || 0"
      :category-name="currentCategory?.name || ''"
      :category-type="currentCategory?.type || 'structural'"
      @uploaded="fetchCategories"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from "vue";
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
  FileTextOutlined as FileTxtOutlined,
  FileMarkdownOutlined,
  FileImageOutlined,
} from "@ant-design/icons-vue";
import {
  getCategories,
  getCategoryFiles,
  deleteCategoryFiles,
} from "@/api/knowledgebase";
import CategoryCreateModal from "./CategoryCreateModal.vue";
import CategoryUploadModal from "./CategoryUploadModal.vue";

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
  files?: any[];
}

const loading = ref(false);
const categories = ref<Category[]>([]);
const expandedCategories = ref<number[]>([]);
const activeTab = ref("all");

const categoryCreateModal = ref();
const categoryUploadModal = ref();

const currentCategory = ref<{
  id: number;
  name: string;
  type: "structural" | "non_structural";
}>();

const filteredCategories = computed(() => {
  if (activeTab.value === "all") return categories.value;
  return categories.value.filter(
    (cat) => cat.category_type === activeTab.value
  );
});

onMounted(() => {
  fetchCategories();
});

const fetchCategories = async () => {
  loading.value = true;
  try {
    const result = await getCategories();
    categories.value = [
      ...result.structured_categories,
      ...result.non_structured_categories,
    ];
  } catch (error) {
    message.error("获取类目列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 新增状态
const selectedFileIds = ref<number[]>([]);
const selectAllFiles = ref(false);

// 获取文件图标 - 根据文件后缀名
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
      return FileTxtOutlined;
    case "md":
      return FileMarkdownOutlined;
    case "jpg":
    case "jpeg":
    case "png":
    case "gif":
    case "bmp":
    case "webp":
      return FileImageOutlined;
    case "html":
    case "htm":
      return FileOutlined; // 或者可以添加一个HTML图标
    default:
      return FileOutlined;
  }
};

// 格式化文件大小
// const formatFileSize = (bytes: number) => {
//   if (bytes === 0) return "0 Bytes";
//   const k = 1024;
//   const sizes = ["Bytes", "KB", "MB", "GB"];
//   const i = Math.floor(Math.log(bytes) / Math.log(k));
//   return parseFloat(bytes / Math.pow(k, i)).toFixed(2) + " " + sizes[i];
// };

// 处理文件选择变化
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

// 处理全选/取消全选
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

// 批量删除文件
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
        const result = await deleteCategoryFiles(
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

        // 重新获取文件列表
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

// 修改单个文件删除方法
const handleDeleteFile = async (categoryId: number, fileId: number) => {
  try {
    await deleteCategoryFiles(categoryId, [fileId]);
    message.success("文件删除成功");
    // 重新获取文件列表
    await fetchCategoryFiles(categoryId);
    // 从选中列表中移除
    selectedFileIds.value = selectedFileIds.value.filter((id) => id !== fileId);
  } catch (error) {
    message.error("文件删除失败");
    console.error(error);
  }
};

// 修改获取文件列表方法，初始化checked状态
const fetchCategoryFiles = async (categoryId: number) => {
  try {
    const files = await getCategoryFiles(categoryId);
    console.log("获取到的文件列表：", files);
    // 初始化checked状态
    const checkedFiles = files.map((file) => ({
      ...file,
      checked: false,
    }));

    // 找到对应的类目并更新文件列表
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
    await fetchCategoryFiles(categoryId); // 新增：获取文件列表
  } else {
    expandedCategories.value.splice(index, 1);
  }
};

const showUploadModal = (category: Category) => {
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
.user-categories-container {
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

.category-files {
  margin-top: 12px;
  padding-left: 24px;
}

.file-actions {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}
/* 调整文件项的行高和间距 */
:deep(.ant-list-item) {
  padding: 12px 16px;
  align-items: center;
}

/* 调整标题区域的布局 */
:deep(.ant-list-item-meta) {
  flex: 1;
  min-width: 0;
}

/* 调整描述文本的样式 */
.file-description {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-left: 8px;
  white-space: nowrap;
}
</style>
