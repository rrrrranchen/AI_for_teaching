<template>
  <div class="post-detail-view">
    <a-page-header
      :title="post.title"
      class="page-header"
      @back="() => router.go(-1)"
    >
      <template #extra>
        <a-button @click="router.push({ name: 'forum-home' })">
          <template #icon><arrow-left-outlined /></template>
          返回列表
        </a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <div class="post-container">
        <!-- 元信息 -->
        <div class="post-meta">
          <a-avatar :src="'http://localhost:5000/' + post.author_avatar" />
          <div class="meta-info">
            <div class="author">{{ post.authorname }}</div>
            <div class="time">{{ formatDate(post.created_at) }}</div>
          </div>
          <div class="stats">
            <span><eye-outlined /> {{ post.view_count }}</span>
            <span><like-outlined /> {{ post.like_count }}</span>
            <span><star-outlined /> {{ post.favorite_count }}</span>
          </div>
        </div>

        <!-- 内容区域 -->
        <a-row :gutter="24">
          <!-- Markdown内容 -->
          <a-col :xl="16" :lg="24" :md="24" :sm="24">
            <div class="markdown-content" v-html="compiledContent"></div>
          </a-col>

          <!-- 附件侧边栏 -->
          <a-col :xl="8" :lg="24" :md="24" :sm="24">
            <div class="attachments-sidebar">
              <h3 class="sidebar-title"><paper-clip-outlined /> 附件列表</h3>
              <div v-if="attachments.length === 0" class="empty-attachments">
                暂无附件
              </div>
              <div v-else class="attachment-list">
                <div
                  v-for="file in attachments"
                  :key="file.attachment_id"
                  class="attachment-item"
                >
                  <div class="file-info">
                    <file-icon :type="getFileType(file.file_path)" />
                    <span class="file-name">{{
                      getFileName(file.file_path)
                    }}</span>
                  </div>
                  <a-button
                    type="link"
                    :href="file.file_path"
                    target="_blank"
                    download
                  >
                    <download-outlined /> 下载
                  </a-button>
                </div>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>
    </a-spin>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import DOMPurify from "dompurify";
import { message } from "ant-design-vue";
import forumApi from "@/api/forum";
import type { ForumPost, ForumAttachment } from "@/api/forum";
import {
  ArrowLeftOutlined,
  EyeOutlined,
  LikeOutlined,
  StarOutlined,
  PaperClipOutlined,
  DownloadOutlined,
} from "@ant-design/icons-vue";

// 初始化Markdown解析器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (err) {
        console.error(err);
      }
    }
    return "";
  },
});

// 文件类型图标映射
const FILE_ICONS = {
  image: "image",
  pdf: "file-pdf",
  word: "file-word",
  excel: "file-excel",
  ppt: "file-ppt",
  text: "file-text",
  zip: "file-zip",
  default: "file",
};

const route = useRoute();
const router = useRouter();
const post = ref<ForumPost>({} as ForumPost);
const attachments = ref<ForumAttachment[]>([]);
const loading = ref(true);
const compiledContent = ref("");

// 获取文件类型
const getFileType = (fileName: string) => {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (!ext) return FILE_ICONS.default;

  if (["jpg", "jpeg", "png", "gif", "webp"].includes(ext))
    return FILE_ICONS.image;
  return FILE_ICONS.default;
};

// 获取文件名
const getFileName = (path: string) => {
  return path.split("/").pop() || "未命名文件";
};

// 日期格式化
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 加载帖子数据
const loadPostData = async () => {
  try {
    const postId = Number(route.params.id);
    const [postRes, attachmentsRes] = await Promise.all([
      forumApi.getPostDetail(postId),
      forumApi.getAttachments(postId),
    ]);

    post.value = postRes;
    attachments.value = attachmentsRes;

    // 安全处理Markdown内容
    compiledContent.value = DOMPurify.sanitize(md.render(postRes.content));
  } catch (error) {
    message.error("加载帖子失败");
    router.push({ name: "forum-home" });
  } finally {
    loading.value = false;
  }
};

onMounted(loadPostData);
</script>
<style scoped>
.post-detail-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  padding: 0;
  margin-bottom: 24px;
}

.post-container {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.post-meta .meta-info {
  flex: 1;
}

.post-meta .meta-info .author {
  font-weight: 500;
  font-size: 16px;
}

.post-meta .meta-info .time {
  color: #666;
  font-size: 12px;
}

.post-meta .stats {
  display: flex;
  gap: 24px;
  color: #666;
}

.post-meta .stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.markdown-content {
  padding-right: 24px;
  line-height: 1.8;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

.markdown-content pre {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-content code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  padding: 0.2em 0.4em;
  background-color: rgba(175, 184, 193, 0.2);
  border-radius: 6px;
}

.markdown-content img {
  max-width: 100%;
  border-radius: 4px;
  margin: 16px 0;
}

.markdown-content blockquote {
  border-left: 4px solid #ddd;
  padding-left: 16px;
  color: #666;
  margin: 16px 0;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.markdown-content table th,
.markdown-content table td {
  border: 1px solid #ddd;
  padding: 8px;
}

.markdown-content table th {
  background-color: #f8f9fa;
}

.attachments-sidebar {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.attachments-sidebar .sidebar-title {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.attachments-sidebar .attachment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attachments-sidebar .attachment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.attachments-sidebar .attachment-item .file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attachments-sidebar .attachment-item .file-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachments-sidebar .empty-attachments {
  color: #666;
  text-align: center;
  padding: 16px;
}

@media (max-width: 768px) {
  .post-detail-view {
    padding: 16px;
  }

  .post-container {
    padding: 16px;
  }

  .markdown-content {
    padding-right: 0;
    margin-bottom: 24px;
  }

  .post-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .post-meta .stats {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
