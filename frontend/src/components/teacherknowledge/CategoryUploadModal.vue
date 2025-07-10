<!-- 教师用 -->
<template>
  <a-modal
    v-model:visible="visible"
    :title="`上传文件到 ${categoryName}`"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
    :width="800"
    :ok-button-props="{ disabled: isUploading }"
  >
    <a-alert
      v-if="categoryType"
      :message="`当前类目类型: ${
        categoryType === 'structural' ? '结构化' : '非结构化'
      }`"
      :description="`允许上传的文件类型: ${allowedExtensions.join(', ')}`"
      type="info"
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
    >
      <p class="ant-upload-drag-icon">
        <inbox-outlined></inbox-outlined>
      </p>
      <p class="ant-upload-text">点击或拖拽文件到此处上传</p>
      <p class="ant-upload-hint">支持单次上传多个文件，但总大小不超过100MB</p>
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
      <h4>上传结果:</h4>
      <a-list item-layout="horizontal" :data-source="uploadResults">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :description="item.message">
              <template #title>
                {{ item.name }}
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
    </div>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, computed, defineExpose, defineProps, defineEmits } from "vue";
import { InboxOutlined } from "@ant-design/icons-vue";
import { message } from "ant-design-vue";
import { uploadFilesToCategory } from "@/api/knowledgebase";
import type { UploadFile } from "ant-design-vue";

interface CustomUploadFile extends UploadFile {
  originFileObj: File & {
    uid: string;
    lastModifiedDate: Date;
  };
}

const ALLOWED_STRUCTURAL_EXTENSIONS = ["csv", "xlsx", "xls"];
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
});

const emit = defineEmits(["uploaded"]);

const visible = ref(false);
const confirmLoading = ref(false);
const fileList = ref<CustomUploadFile[]>([]);
const uploadResults = ref<
  Array<{
    name: string;
    success: boolean;
    message: string;
  }>
>([]);

// 新增上传状态相关变量
const isUploading = ref(false);
const uploadProgress = ref(0);
const uploadStatus = ref<"active" | "success" | "exception">("active");
const uploadStatusText = ref("文件上传中，请稍候...");
// 修改定时器类型声明
const progressInterval = ref<number | null>(null); // 使用 number 替代 NodeJS.Timeout

const allowedExtensions = computed(() => {
  return props.categoryType === "structural"
    ? ALLOWED_STRUCTURAL_EXTENSIONS
    : ALLOWED_NON_STRUCTURAL_EXTENSIONS;
});

const acceptExtensions = computed(() => {
  return allowedExtensions.value.map((ext) => `.${ext}`).join(",");
});

const showModal = () => {
  visible.value = true;
  fileList.value = [];
  uploadResults.value = [];
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

  return true;
};

const handleOk = async () => {
  if (fileList.value.length === 0) {
    message.warning("请先选择要上传的文件");
    return;
  }

  // 重置状态
  resetUploadStatus();
  isUploading.value = true;
  confirmLoading.value = true;

  const startTime = Date.now();
  const duration = 20000; // 最大模拟时长20秒

  // 开始模拟进度
  progressInterval.value = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(99, Math.floor((elapsed / duration) * 100));
    uploadProgress.value = progress;
  }, 100);

  try {
    // 同时发起实际API请求
    const result = await uploadFilesToCategory(
      props.categoryId,
      fileList.value.map((f) => f.originFileObj)
    );

    // API完成后立即处理结果
    clearInterval(progressInterval.value!);
    progressInterval.value = null;

    // 如果进度还没到99%，直接跳到100%
    if (uploadProgress.value < 99) {
      uploadProgress.value = 100;
    }

    uploadStatus.value = "success";
    uploadStatusText.value = "上传成功！";

    // 处理上传结果
    uploadResults.value = [
      ...result.succeeded.map((item) => ({
        name: item.name,
        success: true,
        message: "上传成功",
      })),
      ...result.failed.map((item) => ({
        name: item.name,
        success: false,
        message: item.error,
      })),
    ];

    // 上传成功后清空文件列表
    fileList.value = [];

    // 显示结果消息
    if (result.failed.length === 0) {
      message.success("所有文件上传成功");
      emit("uploaded");
    } else if (result.succeeded.length > 0) {
      message.warning("部分文件上传失败");
    } else {
      message.error("文件上传失败");
    }
  } catch (error) {
    clearInterval(progressInterval.value!);
    progressInterval.value = null;

    uploadProgress.value = 100;
    uploadStatus.value = "exception";
    uploadStatusText.value = "上传失败";

    message.error("上传过程中出错");
    console.error(error);
  } finally {
    isUploading.value = false;
    confirmLoading.value = false;
  }
};

// 修改取消逻辑
const handleCancel = () => {
  if (progressInterval.value !== null) {
    window.clearInterval(progressInterval.value); // 使用 window.clearInterval
    progressInterval.value = null;
  }
  visible.value = false;
  fileList.value = [];
  uploadResults.value = [];
  resetUploadStatus();
};

defineExpose({
  showModal,
});
</script>
