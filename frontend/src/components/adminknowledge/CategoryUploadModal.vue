<!-- 管理员用 -->
<template>
  <a-modal
    v-model:visible="visible"
    :title="`上传文件到系统类目: ${categoryName}`"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
    :width="800"
    :ok-button-props="{ disabled: isUploading }"
    :mask-closable="false"
  >
    <a-alert
      v-if="categoryType"
      :message="`系统类目类型: ${
        categoryType === 'structural' ? '结构化' : '非结构化'
      }`"
      :description="`允许上传的文件类型: ${allowedExtensions.join(', ')}`"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <a-alert
      message="管理员上传提示"
      description="您正在向系统类目上传文件，这些文件将对所有用户可见（如果类目设置为公开）"
      type="warning"
      show-icon
      style="margin-bottom: 16px"
    />

    <a-upload-dragger
      v-model:fileList="fileList"
      name="files"
      :multiple="true"
      :before-upload="beforeUpload"
      :accept="acceptExtensions"
      :disabled="isUploading"
      :max-count="50"
    >
      <p class="ant-upload-drag-icon">
        <inbox-outlined></inbox-outlined>
      </p>
      <p class="ant-upload-text">点击或拖拽文件到此处上传</p>
      <p class="ant-upload-hint">
        支持批量上传最多10个文件，单个文件不超过20MB，总大小不超过200MB
      </p>
    </a-upload-dragger>

    <!-- 上传进度条 -->
    <div v-if="isUploading" style="margin-top: 16px">
      <a-progress
        :percent="uploadProgress"
        :status="uploadStatus"
        :stroke-color="{
          '0%': '#108ee9',
          '100%': '#87d068',
        }"
      />
      <p style="text-align: center; margin-top: 8px">
        {{ uploadStatusText }}
      </p>
    </div>

    <div v-if="uploadResults.length > 0" style="margin-top: 16px">
      <h4>上传结果统计:</h4>
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="8">
          <a-statistic
            title="总文件数"
            :value="uploadResults.length"
            :value-style="{ color: '#3f8600' }"
          />
        </a-col>
        <a-col :span="8">
          <a-statistic
            title="成功数"
            :value="successCount"
            :value-style="{ color: '#3f8600' }"
          />
        </a-col>
        <a-col :span="8">
          <a-statistic
            title="失败数"
            :value="failedCount"
            :value-style="{ color: '#cf1322' }"
          />
        </a-col>
      </a-row>

      <a-collapse v-model:activeKey="activeCollapseKey" ghost>
        <a-collapse-panel key="1" header="上传详情">
          <a-list
            item-layout="horizontal"
            :data-source="uploadResults"
            :pagination="{
              pageSize: 5,
              showSizeChanger: false,
            }"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :description="item.message">
                  <template #title>
                    <span
                      :style="{ color: item.success ? '#389e0d' : '#cf1322' }"
                    >
                      {{ item.name }}
                    </span>
                    <a-tag
                      :color="item.success ? 'green' : 'red'"
                      style="margin-left: 8px"
                    >
                      {{ item.success ? "成功" : "失败" }}
                    </a-tag>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, computed, defineExpose, defineProps, defineEmits } from "vue";
import { InboxOutlined } from "@ant-design/icons-vue";
import { message } from "ant-design-vue";
import { adminUploadFilesToCategory } from "@/api/knowledgebasemanage";
import type { UploadFile } from "ant-design-vue";

interface CustomUploadFile extends UploadFile {
  originFileObj: File & {
    uid: string;
    lastModifiedDate: Date;
  };
}

interface UploadResult {
  name: string;
  success: boolean;
  message: string;
}

const ALLOWED_STRUCTURAL_EXTENSIONS = ["csv", "xlsx", "xls", "json"];
const ALLOWED_NON_STRUCTURAL_EXTENSIONS = [
  "txt",
  "md",
  "doc",
  "docx",
  "pdf",
  "html",
  "htm",
  "ppt",
  "pptx",
  "png",
  "jpg",
  "jpeg",
  "gif",
  "mp3",
  "mp4",
];

const props = defineProps({
  categoryId: {
    type: Number,
    required: true,
  },
  categoryName: {
    type: String,
    required: true,
  },
  categoryType: {
    type: String as () => "structural" | "non_structural",
    required: true,
  },
  isSystem: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(["uploaded"]);

const visible = ref(false);
const confirmLoading = ref(false);
const fileList = ref<CustomUploadFile[]>([]);
const uploadResults = ref<UploadResult[]>([]);
const activeCollapseKey = ref<string[]>(["1"]);

// 上传状态
const isUploading = ref(false);
const uploadProgress = ref(0);
const uploadStatus = ref<"active" | "success" | "exception">("active");
const uploadStatusText = ref("文件上传中，请稍候...");
const progressInterval = ref<number | null>(null);

const allowedExtensions = computed(() => {
  return props.categoryType === "structural"
    ? ALLOWED_STRUCTURAL_EXTENSIONS
    : ALLOWED_NON_STRUCTURAL_EXTENSIONS;
});

const acceptExtensions = computed(() => {
  return allowedExtensions.value.map((ext) => `.${ext}`).join(",");
});

const successCount = computed(() => {
  return uploadResults.value.filter((item) => item.success).length;
});

const failedCount = computed(() => {
  return uploadResults.value.filter((item) => !item.success).length;
});

const showModal = () => {
  visible.value = true;
  resetUploadStatus();
};

const resetUploadStatus = () => {
  isUploading.value = false;
  uploadProgress.value = 0;
  uploadStatus.value = "active";
  uploadStatusText.value = "文件上传中，请稍候...";
  if (progressInterval.value) {
    clearInterval(progressInterval.value);
    progressInterval.value = null;
  }
};

const beforeUpload = (file: File) => {
  const extension = file.name.split(".").pop()?.toLowerCase();
  const isValid = allowedExtensions.value.includes(extension || "");

  if (!isValid) {
    message.error(
      `不支持的文件类型: ${extension}。请上传${allowedExtensions.value.join(
        ", "
      )}格式的文件`
    );
    return false;
  }

  // 检查文件大小 (50MB限制)
  const MAX_SIZE = 20 * 1024 * 1024; // 20MB
  if (file.size > MAX_SIZE) {
    message.error(`文件 ${file.name} 超过20MB限制`);
    return false;
  }

  return true;
};

const handleOk = async () => {
  console.log("handleOk，文件数量: " + fileList.value.length);
  if (fileList.value.length === 0) {
    message.warning("请先选择要上传的文件");
    return;
  }

  // 检查总大小 (500MB限制)
  const TOTAL_MAX_SIZE = 200 * 1024 * 1024; // 500MB
  const totalSize = fileList.value.reduce(
    (sum, file) => sum + (file.size || 0),
    0
  );
  if (totalSize > TOTAL_MAX_SIZE) {
    message.warning("总文件大小超过200MB限制");
    return;
  }

  resetUploadStatus();
  isUploading.value = true;
  confirmLoading.value = true;

  // 模拟进度
  const startTime = Date.now();
  const duration = 20000; // 最大模拟时长20秒
  progressInterval.value = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(99, Math.floor((elapsed / duration) * 100));
    uploadProgress.value = progress;
  }, 100);

  try {
    console.log("文件数量：", fileList.value.length);
    const files = fileList.value.map((f) => f.originFileObj);
    const result = await adminUploadFilesToCategory(props.categoryId, files);

    clearInterval(progressInterval.value!);
    progressInterval.value = null;

    uploadProgress.value = 100;
    uploadStatus.value = "success";
    uploadStatusText.value = "上传成功！";

    // 处理上传结果
    uploadResults.value = [
      ...result.data.succeeded.map((item: any) => ({
        name: item.name,
        success: true,
        message: "上传成功",
      })),
      ...result.data.failed.map((item: any) => ({
        name: item.name,
        success: false,
        message: item.error,
      })),
    ];

    // 显示结果消息
    if (result.data.failed.length === 0) {
      message.success(`成功上传 ${result.data.succeeded.length} 个文件`);
      emit("uploaded");
    } else if (result.data.succeeded.length > 0) {
      message.warning(
        `成功上传 ${result.data.succeeded.length} 个文件，失败 ${result.data.failed.length} 个`
      );
    } else {
      message.error("所有文件上传失败");
    }
  } catch (error: any) {
    clearInterval(progressInterval.value!);
    progressInterval.value = null;

    uploadProgress.value = 100;
    uploadStatus.value = "exception";
    uploadStatusText.value = "上传失败";

    const errorMessage = error.response?.data?.message || "上传过程中出错";
    message.error(errorMessage);
    console.error("上传错误:", error);
  } finally {
    isUploading.value = false;
    confirmLoading.value = false;
  }
};

const handleCancel = () => {
  if (isUploading.value) {
    message.warning("文件正在上传中，请等待上传完成");
    return;
  }

  if (progressInterval.value !== null) {
    window.clearInterval(progressInterval.value);
    progressInterval.value = null;
  }

  visible.value = false;
  resetUploadStatus();
};

defineExpose({
  showModal,
});
</script>

<style scoped>
.ant-upload-drag-icon {
  color: #1890ff;
  font-size: 24px;
  margin-bottom: 8px;
}
.ant-upload-text {
  font-size: 16px;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 4px;
}
.ant-upload-hint {
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
}
</style>
