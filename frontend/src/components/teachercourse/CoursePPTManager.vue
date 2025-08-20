<template>
  <div class="ppt-layout">
    <!-- 上方功能区 -->
    <div class="top-panel">
      <!-- 左侧上传和PPT信息 -->
      <div class="left-section">
        <a-card title="PPT管理" class="upload-card">
          <a-upload-dragger
            :before-upload="beforeUpload"
            :show-upload-list="false"
            :accept="'.ppt,.pptx,.pdf'"
            class="upload-area"
          >
            <p class="ant-upload-drag-icon">
              <cloud-upload-outlined />
            </p>
            <p class="ant-upload-text">点击或拖拽PPT文件到此处上传</p>
            <p class="ant-upload-hint">支持 .ppt, .pptx, .pdf 格式文件</p>
          </a-upload-dragger>

          <div
            v-if="uploadStatus.message"
            :class="['upload-status', uploadStatus.type]"
          >
            <check-circle-outlined v-if="uploadStatus.type === 'success'" />
            <close-circle-outlined v-else />
            {{ uploadStatus.message }}
          </div>

          <a-button
            type="primary"
            :loading="uploading"
            :disabled="!selectedFile"
            @click="handleUpload"
            class="upload-btn"
          >
            {{ pptPath ? "重新上传" : "上传PPT" }}
          </a-button>

          <div v-if="pptPath" class="ppt-info">
            <p>当前PPT文件：{{ getFileName(pptPath) }}</p>
            <a-space>
              <a-button type="link" :href="fullPptUrl" target="_blank" download>
                <download-outlined /> 下载PPT
              </a-button>
            </a-space>
          </div>
        </a-card>
      </div>

      <!-- 右侧跳转区域 -->
      <div class="right-section">
        <a-card
          hoverable
          class="jump-card"
          @click="$router.push('/home/smart-preparation')"
        >
          <div class="jump-content">
            <rocket-outlined class="jump-icon" />
            <h3>生成 PPT 页面</h3>
            <p>点击跳转到智能生成 PPT 页面</p>
          </div>
        </a-card>
      </div>
    </div>

    <!-- 下方PPT预览区 -->
    <div class="bottom-panel">
      <a-card title="PPT预览" class="preview-card">
        <div class="preview-container">
          <template v-if="pptPath">
            <template v-if="isPDF(pptPath)">
              <embed
                :src="fullPptUrl"
                type="application/pdf"
                width="100%"
                height="100%"
              />
            </template>
            <template v-else>
              <iframe
                class="m-iframe"
                :src="`/ppt/index.html?file=${encodeURIComponent(fullPptUrl)}`"
              ></iframe>
            </template>
          </template>
          <div v-else class="empty-preview">
            <file-image-outlined class="empty-icon" />
            <p>暂无 PPT 文件</p>
            <p class="empty-hint">请先上传PPT文件</p>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from "vue";
import { message } from "ant-design-vue";
import {
  CloudUploadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  RocketOutlined,
  FileImageOutlined,
} from "@ant-design/icons-vue";
import { uploadCoursePPT, getCoursePPT } from "@/api/course";

interface UploadStatus {
  type: "success" | "error" | "";
  message: string;
}

export default defineComponent({
  name: "CoursePPTManager",
  components: {
    CloudUploadOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    DownloadOutlined,
    RocketOutlined,
    FileImageOutlined,
  },
  props: {
    courseId: { type: Number, required: true },
  },
  setup(props) {
    const selectedFile = ref<File | null>(null);
    const uploading = ref(false);
    const loading = ref(false);
    const pptPath = ref<string>("");
    const uploadStatus = ref<UploadStatus>({ type: "", message: "" });

    const API_BASE_URL = "http://localhost:5000/";
    const fullPptUrl = computed(() =>
      pptPath.value
        ? `${API_BASE_URL}${
            pptPath.value.startsWith("/")
              ? pptPath.value.slice(1)
              : pptPath.value
          }`
        : ""
    );

    const getFileName = (path: string) => path.split("/").pop() || "未知文件";
    const isPDF = (path: string) => path.toLowerCase().endsWith(".pdf");

    const allowedTypes = [
      "application/pdf",
      "application/vnd.ms-powerpoint",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ];

    const beforeUpload = (file: File) => {
      const isValid =
        allowedTypes.includes(file.type) || /\.(pptx?|pdf)$/i.test(file.name);
      if (!isValid) {
        message.error("只支持 PPT / PDF 格式文件");
        return false;
      }
      if (file.size > 50 * 1024 * 1024) {
        message.error("文件大小不能超过 50MB");
        return false;
      }
      selectedFile.value = file;
      uploadStatus.value = { type: "", message: "" };
      return false;
    };

    const handleUpload = async () => {
      if (!selectedFile.value) return;
      uploading.value = true;
      uploadStatus.value = { type: "", message: "上传中..." };
      try {
        const res = await uploadCoursePPT(props.courseId, selectedFile.value);
        pptPath.value = res.ppt_path;
        uploadStatus.value = { type: "success", message: "上传成功！" };
        message.success("PPT 上传成功");
        selectedFile.value = null;
      } catch (e: any) {
        const msg = e.response?.data?.error || "上传失败";
        uploadStatus.value = { type: "error", message: msg };
        message.error(msg);
      } finally {
        uploading.value = false;
      }
    };

    const fetchPPT = async () => {
      loading.value = true;
      try {
        const res = await getCoursePPT(props.courseId);
        pptPath.value = res.ppt_path;
      } catch (e: any) {
        if (e.response?.status !== 404) message.error("获取 PPT 信息失败");
      } finally {
        loading.value = false;
      }
    };

    onMounted(fetchPPT);

    return {
      selectedFile,
      uploading,
      loading,
      pptPath,
      fullPptUrl,
      uploadStatus,
      beforeUpload,
      handleUpload,
      getFileName,
      isPDF,
    };
  },
});
</script>

<style scoped>
.ppt-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 16px;
  height: 85vh;
  overflow-y: auto;
}

/* 上方功能区 */
.top-panel {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.left-section {
  flex: 3;
}

.right-section {
  flex: 1;
}

.upload-card {
  height: 100%;
}

.jump-card {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.jump-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.jump-content {
  text-align: center;
  padding: 20px;
}

.jump-icon {
  font-size: 36px;
  color: #1890ff;
  margin-bottom: 12px;
}

/* 下方预览区 */
.bottom-panel {
  flex: 1;
  min-height: 400px;
}

.preview-card {
  height: 700px;
}

.preview-container {
  width: 100%;
  height: 600px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
  background-color: #fff;
}

.m-iframe,
embed {
  width: 100%;
  height: 100%;
  border: none;
}

.upload-area {
  margin-bottom: 16px;
}

.upload-status {
  margin: 16px 0;
  padding: 8px 12px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-status.success {
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

.upload-status.error {
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
}

.upload-btn {
  margin-top: 16px;
  width: 100%;
}

.ppt-info {
  margin-top: 16px;
  padding: 12px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.empty-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  background-color: #f5f5f5;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #d9d9d9;
}

.empty-hint {
  margin-top: 8px;
  font-size: 14px;
  color: #bfbfbf;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .top-panel {
    flex-direction: column;
  }

  .preview-container {
    height: 400px;
  }
}
</style>
