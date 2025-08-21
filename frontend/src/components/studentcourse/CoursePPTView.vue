<template>
  <div class="ppt-layout">
    <!-- PPT预览区 -->
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

    <!-- PPT信息区 - 下载按钮在右侧 -->
    <div v-if="pptPath" class="ppt-info-card">
      <a-card title="PPT信息" size="small">
        <div class="ppt-info-content">
          <div class="info-left">
            <p><strong>文件名：</strong>{{ getFileName(pptPath) }}</p>
            <p>
              <strong>文件类型：</strong
              >{{ isPDF(pptPath) ? "PDF" : "PowerPoint" }}
            </p>
          </div>
          <div class="info-right">
            <a-button
              type="primary"
              :href="fullPptUrl"
              target="_blank"
              download
            >
              <download-outlined /> 下载PPT
            </a-button>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from "vue";
import { message } from "ant-design-vue";
import { DownloadOutlined, FileImageOutlined } from "@ant-design/icons-vue";
import { getCoursePPT } from "@/api/course";

export default defineComponent({
  name: "CoursePPTViewer",
  components: {
    DownloadOutlined,
    FileImageOutlined,
  },
  props: {
    courseId: { type: Number, required: true },
  },
  setup(props) {
    const loading = ref(false);
    const pptPath = ref<string>("");

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
      loading,
      pptPath,
      fullPptUrl,
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
  gap: 16px;
  padding: 16px;
  height: 85vh;
}

.preview-container {
  width: 100%;
  flex: 1;
  min-height: 500px;
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

.ppt-info-card {
  width: 100%;
}

.ppt-info-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.info-left p {
  margin-bottom: 8px;
  margin: 0;
  line-height: 1.5;
}

.info-right {
  display: flex;
  align-items: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preview-container {
    height: 400px;
  }

  .ppt-info-card {
    margin-top: 16px;
  }

  .ppt-info-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .info-right {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
