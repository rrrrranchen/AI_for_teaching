<!-- src/views/community/PostEditor.vue -->
<template>
  <div class="post-editor">
    <a-page-header
      title="发布新帖子"
      @back="() => router.go(-1)"
      class="editor-header"
    >
      <template #extra>
        <a-button type="primary" @click="handlePublish" :loading="publishing">
          发布
        </a-button>
      </template>
    </a-page-header>

    <div class="editor-container">
      <a-row :gutter="24">
        <!-- 左侧编辑区（2/3宽度） -->
        <a-col :span="16">
          <div class="left-panel">
            <a-input
              v-model:value="form.title"
              placeholder="请输入标题（必填）"
              class="title-input"
              :maxlength="100"
              allow-clear
            />
            <div id="vditor-container" class="vditor-wrapper"></div>
          </div>
        </a-col>

        <!-- 右侧设置区（1/3宽度） -->
        <a-col :span="8">
          <div class="right-panel">
            <!-- 标签设置 -->
            <div class="setting-block">
              <h3 class="block-title"><tags-outlined /> 添加标签</h3>
              <a-select
                v-model:value="form.tags"
                mode="tags"
                placeholder="输入标签后回车"
                :token-separators="[',']"
                style="width: 100%"
                :max-tag-count="3"
              >
                <template #suffixIcon><smile-outlined /></template>
              </a-select>
            </div>

            <!-- 图片上传 -->
            <div class="setting-block">
              <h3 class="block-title"><picture-outlined /> 上传图片</h3>
              <a-upload
                v-model:file-list="fileList"
                list-type="picture-card"
                :customRequest="handleUpload"
                :multiple="true"
                :show-upload-list="false"
                :accept="'image/*'"
                :beforeUpload="beforeUpload"
                @preview="handlePreview"
                :disabled="fileList.length >= 5"
              >
                <div v-if="fileList.length < 5">
                  <plus-outlined />
                  <div class="ant-upload-text">点击上传</div>
                  <div class="ant-upload-hint">支持JPG/PNG格式</div>
                </div>
              </a-upload>

              <!-- 图片预览列表 -->
              <div class="image-list">
                <div
                  v-for="file in fileList"
                  :key="file.uid"
                  class="image-item"
                  :class="{ uploading: file.status === 'uploading' }"
                >
                  <div class="image-wrapper">
                    <img
                      :src="file.thumbUrl || file.url"
                      alt="preview"
                      @click="handlePreview(file)"
                    />
                    <a-progress
                      v-if="file.status === 'uploading'"
                      type="circle"
                      :percent="file.percent"
                      :width="40"
                      class="progress"
                    />
                    <div class="image-actions">
                      <eye-filled @click="handlePreview(file)" />
                      <delete-filled
                        @click="handleRemoveFile(file)"
                        class="delete-btn"
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div class="upload-tip">最多可上传5张图片（每张不超过2MB）</div>
            </div>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 图片预览模态框 -->
    <a-modal
      :visible="previewVisible"
      :footer="null"
      @cancel="previewVisible = false"
      width="80vw"
    >
      <img :src="previewImage" style="max-width: 100%; max-height: 80vh" />
    </a-modal>
  </div>
</template>

<script lang="ts">
import {
  defineComponent,
  reactive,
  ref,
  onMounted,
  onBeforeUnmount,
} from "vue";
import { useRouter } from "vue-router";
import Vditor from "vditor";
import "vditor/dist/index.css";
import { message } from "ant-design-vue";
import type { UploadFile } from "ant-design-vue/es/upload/interface";
import {
  PlusOutlined,
  DeleteFilled,
  EyeFilled,
  TagsOutlined,
  SmileOutlined,
  PictureOutlined,
} from "@ant-design/icons-vue";
import forumApi from "@/api/forum";

interface EditorForm {
  title: string;
  content: string;
  tags: string[];
  attachments: number[];
}

export default defineComponent({
  name: "PostEditor",
  components: {
    PlusOutlined,
    DeleteFilled,
    EyeFilled,
    TagsOutlined,
    SmileOutlined,
    PictureOutlined,
  },
  setup() {
    const router = useRouter();
    const vditor = ref<Vditor>();
    const form = reactive<EditorForm>({
      title: "",
      content: "",
      tags: [],
      attachments: [],
    });

    const fileList = ref<UploadFile[]>([]);
    const publishing = ref(false);
    const previewVisible = ref(false);
    const previewImage = ref("");

    // 初始化编辑器
    onMounted(() => {
      vditor.value = new Vditor("vditor-container", {
        height: "calc(100vh - 200px)",
        placeholder: "请输入内容...（支持Markdown语法）",
        mode: "ir",
        toolbar: [
          "emoji",
          "headings",
          "bold",
          "italic",
          "strike",
          "link",
          "|",
          "list",
          "ordered-list",
          "check",
          "outdent",
          "indent",
          "|",
          "quote",
          "line",
          "code",
          "inline-code",
          "insert-before",
          "insert-after",
          "|",
          "upload",
          "table",
          "|",
          "undo",
          "redo",
          "|",
          "fullscreen",
          "edit-mode",
          {
            name: "more",
            toolbar: [
              "both",
              "code-theme",
              "content-theme",
              "export",
              "outline",
              "preview",
            ],
          },
        ],
        cache: {
          enable: true,
          id: "vditor-editor-cache",
        },
        after: () => {
          vditor.value?.setValue(form.content);
        },
        input: (content) => {
          form.content = content;
        },
      });
    });

    // 清理编辑器
    onBeforeUnmount(() => {
      vditor.value?.destroy();
    });

    // 上传前校验
    const beforeUpload = (file: File) => {
      const isImage = file.type.startsWith("image/");
      if (!isImage) {
        message.error("只能上传图片文件！");
        return false;
      }
      const isLt2M = file.size / 1024 / 1024 < 2;
      if (!isLt2M) {
        message.error("图片大小不能超过2MB！");
        return false;
      }
      return true;
    };

    // 处理文件上传
    const handleUpload = async ({
      file,
      onProgress,
      onSuccess,
      onError,
    }: any) => {
      try {
        const formData = new FormData();
        formData.append("files", file);

        // 显示上传进度
        const updateProgress = (percent: number) => {
          const targetFile = fileList.value.find((f) => f.uid === file.uid);
          if (targetFile) {
            targetFile.percent = percent;
            targetFile.status = "uploading";
          }
          onProgress({ percent });
        };

        // 模拟上传进度
        const interval = setInterval(() => {
          const current = file.percent || 0;
          const newPercent = Math.min(current + 10, 90);
          updateProgress(newPercent);
        }, 200);

        // 实际上传请求
        const res = await forumApi.uploadAttachments([file]);
        clearInterval(interval);
        updateProgress(100);

        // 添加附件ID和预览图
        form.attachments.push(res[0].attachment_id);
        file.thumbUrl = URL.createObjectURL(file);
        file.status = "done";
        onSuccess();
      } catch (error) {
        onError(error);
        message.error("上传失败，请重试");
      }
    };

    // 处理文件删除
    const handleRemoveFile = (file: UploadFile) => {
      fileList.value = fileList.value.filter((f) => f.uid !== file.uid);
      form.attachments = form.attachments.filter(
        (id) => id !== Number(file.uid)
      );
    };

    // 图片预览处理
    const handlePreview = async (file: UploadFile) => {
      if (!file.url && !file.preview) {
        file.preview = await getBase64(file.originFileObj!);
      }
      previewImage.value = file.url || file.preview!;
      previewVisible.value = true;
    };

    const getBase64 = (file: File) => {
      return new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result as string);
      });
    };

    // 处理发布
    const handlePublish = async () => {
      if (!form.title.trim()) {
        message.warning("请输入标题");
        return;
      }

      if (!form.content.trim()) {
        message.warning("请输入内容");
        return;
      }

      try {
        publishing.value = true;
        await forumApi.createPost({
          title: form.title,
          content: form.content,
          tags: form.tags,
          attachment_ids: form.attachments,
        });
        message.success("发布成功！");
        // 清除编辑器缓存
        localStorage.removeItem("vditor-editor-cache");
        router.push({ name: "my-posts" });
      } catch (error) {
        message.error("发布失败，请稍后重试");
      } finally {
        publishing.value = false;
      }
    };

    return {
      form,
      fileList,
      publishing,
      previewVisible,
      previewImage,
      handleUpload,
      handleRemoveFile,
      handlePreview,
      handlePublish,
      beforeUpload,
      router,
    };
  },
});
</script>

<style scoped>
.editor-container {
  max-width: 90%;
  margin: 0 auto;
}

.left-panel {
  height: 75vh;
  display: flex;
  flex-direction: column;
  background: #ebf8ff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.title-input {
  font-size: 18px;
  margin-bottom: 16px;
  flex-shrink: 0;

  &:deep(.ant-input) {
    border: none;
    border-bottom: 1px solid #eee;
    border-radius: 0;
    padding-left: 0;

    &:focus {
      box-shadow: none;
      border-color: #1890ff;
    }
  }
}

.vditor-wrapper {
  flex: 1;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;
}

.right-panel {
  padding-left: 20px;
  position: sticky;
  top: 80px;
}

.setting-block {
  margin-bottom: 24px;
  background: #fffdeb;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .block-title {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    color: #333;
    font-weight: 500;

    .anticon {
      margin-right: 8px;
      font-size: 16px;
      color: #666;
    }
  }
}

.image-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;

  &.uploading {
    opacity: 0.6;
  }

  .image-wrapper {
    position: relative;
    width: 100%;
    height: 100%;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      cursor: zoom-in;
    }

    .progress {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 2;
    }

    .image-actions {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(transparent, rgba(0, 0, 0, 0.6));
      padding: 8px;
      display: flex;
      justify-content: center;
      gap: 12px;
      opacity: 0;
      transition: opacity 0.3s;

      .anticon {
        color: #fff;
        font-size: 16px;
        cursor: pointer;
        padding: 4px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        transition: all 0.3s;

        &:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: scale(1.1);
        }
      }
    }

    &:hover .image-actions {
      opacity: 1;
    }
  }
}

.upload-tip {
  color: #999;
  font-size: 12px;
  margin-top: 8px;
  text-align: center;
}

@media (max-width: 992px) {
  .editor-container {
    padding: 16px;
  }

  .left-panel {
    height: 60vh;
  }

  .image-list {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .ant-row {
    flex-direction: column;
  }

  .ant-col-16,
  .ant-col-8 {
    width: 100%;
    max-width: 100%;
  }

  .right-panel {
    padding-left: 0;
    margin-top: 24px;
  }
}
</style>
