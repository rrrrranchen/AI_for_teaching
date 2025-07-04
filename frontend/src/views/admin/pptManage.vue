<template>
  <div class="ppt-template-management">
    <a-card title="PPT模板管理" :bordered="false">
      <div class="table-header">
        <a-space>
          <a-button type="primary" @click="showUploadModal">
            <template #icon><UploadOutlined /></template>
            上传模板
          </a-button>
          <a-button
            danger
            @click="batchDelete"
            :disabled="selectedRowKeys.length === 0"
          >
            <template #icon><DeleteOutlined /></template>
            批量删除
          </a-button>
        </a-space>
      </div>

      <a-table
        :columns="columns"
        :data-source="templates"
        :row-key="(record: any) => record.id"
        :row-selection="{
          selectedRowKeys: selectedRowKeys,
          onChange: onSelectChange,
        }"
        :pagination="pagination"
        :loading="loading"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'preview'">
            <a-image
              :width="120"
              :src="'http://localhost:5000/' + record.image_url"
              :preview="{
                src: 'http://localhost:5000/' + record.image_url,
              }"
            />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" :href="record.url" target="_blank">
                <template #icon><DownloadOutlined /></template>
                下载
              </a-button>
              <a-popconfirm
                title="确定要删除此模板吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="deleteTemplate(record.id)"
              >
                <a-button type="link" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 上传模板模态框 -->
    <a-modal
      v-model:visible="uploadModalVisible"
      title="上传PPT模板"
      @ok="handleUpload"
      @cancel="handleUploadCancel"
      :confirm-loading="uploading"
      :ok-button-props="{ disabled: !canUpload }"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="PPT文件" required>
          <a-upload
            :before-upload="beforePptUpload"
            :max-count="1"
            accept=".pptx"
            :file-list="pptFileList"
          >
            <a-button>
              <template #icon><UploadOutlined /></template>
              选择PPT文件 (.pptx)
            </a-button>
          </a-upload>
        </a-form-item>
        <a-form-item label="预览图片" required>
          <a-upload
            :before-upload="beforeImageUpload"
            :max-count="1"
            accept=".png,.jpg,.jpeg"
            :file-list="imageFileList"
            list-type="picture-card"
          >
            <div v-if="imageFileList.length < 1">
              <plus-outlined />
              <div style="margin-top: 8px">上传预览图</div>
            </div>
          </a-upload>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from "vue";
import { message } from "ant-design-vue";
import {
  UploadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  PlusOutlined,
} from "@ant-design/icons-vue";
import pptTemplateApi from "@/api/pptmanage";
import type { PPTTemplate } from "@/api/pptmanage";

// 表格列定义
const columns = [
  {
    title: "ID",
    dataIndex: "id",
    key: "id",
    width: 80,
  },
  {
    title: "模板名称",
    dataIndex: "name",
    key: "name",
  },
  {
    title: "预览图",
    key: "preview",
    width: 150,
  },
  {
    title: "操作",
    key: "action",
    width: 200,
  },
];

// 数据状态
const templates = ref<PPTTemplate[]>([]);
const loading = ref(false);
const selectedRowKeys = ref<number[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  pageSizeOptions: ["10", "20", "50"],
});

// 上传相关状态
const uploadModalVisible = ref(false);
const uploading = ref(false);
const pptFileList = ref<any[]>([]);
const imageFileList = ref<any[]>([]);

// 计算属性 - 是否可以上传
const canUpload = computed(() => {
  return pptFileList.value.length > 0 && imageFileList.value.length > 0;
});

// 获取模板列表
const fetchTemplates = async () => {
  try {
    loading.value = true;
    const result = await pptTemplateApi.getTemplates();
    console.log("获取模板列表:", result);
    templates.value = result;
    pagination.total = result.length;
  } catch (error) {
    message.error("获取模板列表失败");
  } finally {
    loading.value = false;
  }
};

// 选择行变化
const onSelectChange = (selectedKeys: number[]) => {
  selectedRowKeys.value = selectedKeys;
};

// 显示上传模态框
const showUploadModal = () => {
  uploadModalVisible.value = true;
};

// PPT文件上传前处理
const beforePptUpload = (file: any) => {
  pptFileList.value = [file];
  return false; // 阻止自动上传
};

// 图片上传前处理
const beforeImageUpload = (file: any) => {
  const isImage = file.type.includes("image");
  if (!isImage) {
    message.error("只能上传图片文件!");
    return false;
  }
  imageFileList.value = [file];
  return false; // 阻止自动上传
};

// 处理上传
const handleUpload = async () => {
  if (!canUpload.value) {
    message.warning("请先选择PPT文件和预览图片");
    return;
  }

  try {
    uploading.value = true;
    const formData = new FormData();
    formData.append("file", pptFileList.value[0]);
    formData.append("image", imageFileList.value[0]);

    await pptTemplateApi.createTemplate(formData);
    message.success("模板上传成功");
    uploadModalVisible.value = false;
    resetUpload();
    fetchTemplates();
  } catch (error) {
    message.error("模板上传失败");
  } finally {
    uploading.value = false;
  }
};

// 取消上传
const handleUploadCancel = () => {
  uploadModalVisible.value = false;
  resetUpload();
};

// 重置上传状态
const resetUpload = () => {
  pptFileList.value = [];
  imageFileList.value = [];
};

// 删除模板
const deleteTemplate = async (id: number) => {
  try {
    await pptTemplateApi.deleteTemplate(id);
    message.success("模板删除成功");
    fetchTemplates();
  } catch (error) {
    message.error("模板删除失败");
  }
};

// 批量删除
const batchDelete = async () => {
  try {
    await Promise.all(
      selectedRowKeys.value.map((id) => pptTemplateApi.deleteTemplate(id))
    );
    message.success(`成功删除 ${selectedRowKeys.value.length} 个模板`);
    selectedRowKeys.value = [];
    fetchTemplates();
  } catch (error) {
    message.error("批量删除模板失败");
  }
};

// 初始化加载数据
onMounted(() => {
  fetchTemplates();
});
</script>

<style scoped>
.ppt-template-management {
  padding: 16px;
  background: #fff;
}

.table-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

:deep(.ant-upload-select-picture-card i) {
  font-size: 32px;
  color: #999;
}

:deep(.ant-upload-select-picture-card .ant-upload-text) {
  margin-top: 8px;
  color: #666;
}
</style>
