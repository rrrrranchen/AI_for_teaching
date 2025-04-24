<template>
  <div class="post-detail-view">
    <a-page-header
      :title="post.title"
      class="page-header"
      @back="() => router.go(-1)"
    >
      <template #extra>
        <a-space>
          <a-button @click="handleLike" :loading="likeLoading">
            <template #icon>
              <component :is="post.is_liked ? LikeFilled : LikeOutlined" />
            </template>
            {{ post.like_count }}
          </a-button>
          <a-button @click="handleFavorite" :loading="favoriteLoading">
            <template #icon>
              <component :is="post.is_favorited ? StarFilled : StarOutlined" />
            </template>
            {{ post.favorite_count }}
          </a-button>
          <a-button @click="router.push({ name: 'forum-home' })">
            <template #icon><arrow-left-outlined /></template>
            返回列表
          </a-button>
        </a-space>
      </template>
    </a-page-header>
    <!-- 修改后的滚动容器 -->
    <div class="content-wrapper">
      <a-spin :spinning="loading" class="post-content">
        <div class="post-container">
          <!-- 作者信息卡片 -->
          <a-card class="author-card" :bordered="false">
            <a-row align="middle" :gutter="16">
              <a-col :span="4">
                <a-avatar
                  :src="'http://localhost:5000/' + post.author_avatar"
                  :size="80"
                  class="author-avatar"
                />
              </a-col>
              <a-col :span="14">
                <div class="author-info">
                  <h3 class="author-name">{{ post.authorname }}</h3>
                  <div class="post-meta">
                    <span class="post-time">
                      <clock-circle-outlined />
                      {{ formatDate(post?.created_at?.$date) }}
                    </span>
                    <span class="view-count">
                      <eye-outlined />
                      {{ post.view_count }} 浏览
                    </span>
                  </div>
                </div>
              </a-col>
              <a-col :span="6" class="action-buttons">
                <a-button type="primary" size="small" @click="showFollowModal">
                  <template #icon><user-add-outlined /></template>
                  关注
                </a-button>
              </a-col>
            </a-row>
          </a-card>

          <!-- 内容区域 -->
          <div class="content-section">
            <!-- Markdown内容 -->
            <a-card class="content-card" :bordered="false">
              <div class="markdown-content" v-html="compiledContent"></div>
            </a-card>

            <!-- 图片附件展示 -->
            <a-card
              v-if="imageAttachments.length > 0"
              class="image-gallery-card"
              title="图片附件"
            >
              <a-image-preview-group>
                <a-row :gutter="16">
                  <a-col
                    v-for="(image, index) in imageAttachments"
                    :key="index"
                    :span="8"
                    :xs="12"
                    :sm="8"
                    :md="6"
                    :lg="4"
                  >
                    <a-image
                      :src="'http://localhost:5000/' + image.file_path"
                      :alt="
                        getFileName('http://localhost:5000/' + image.file_path)
                      "
                      class="gallery-image"
                    />
                    <div class="image-actions">
                      <a-button
                        type="link"
                        :href="'http://localhost:5000/' + image.file_path"
                        download
                        size="small"
                      >
                        <download-outlined /> 下载
                      </a-button>
                    </div>
                  </a-col>
                </a-row>
              </a-image-preview-group>
            </a-card>

            <!-- 其他附件 -->
            <a-card
              v-if="otherAttachments.length > 0"
              class="attachments-card"
              title="其他附件"
            >
              <a-list
                :data-source="otherAttachments"
                :grid="{ gutter: 16, column: 4 }"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-card hoverable class="attachment-item">
                      <template #actions>
                        <a-button
                          type="link"
                          :href="'http://localhost:5000/' + item.file_path"
                          download
                          size="small"
                        >
                          <download-outlined /> 下载
                        </a-button>
                      </template>
                      <a-card-meta>
                        <template #description>
                          <file-icon
                            :type="
                              getFileType(
                                'http://localhost:5000/' + item.file_path
                              )
                            "
                          />
                          {{
                            getFileName(
                              "http://localhost:5000/" + item.file_path
                            )
                          }}
                        </template>
                      </a-card-meta>
                    </a-card>
                  </a-list-item>
                </template>
              </a-list>
            </a-card>

            <!-- 评论区域 -->
            <a-card class="comments-card" title="评论">
              <a-comment
                v-for="comment in comments"
                :key="comment.id"
                :author="comment.author_name"
                :avatar="'http://localhost:5000/' + comment.author_avatar"
                :datetime="formatDate(comment.created_at?.$date)"
              >
                <template #actions>
                  <span @click="replyTo(comment)">回复</span>
                </template>
                <p>{{ comment.content }}</p>

                <!-- 回复评论 -->
                <div v-if="comment.replies && comment.replies.length">
                  <a-comment
                    v-for="reply in comment.replies"
                    :key="reply.id"
                    :author="reply.author_name"
                    :avatar="'http://localhost:5000/' + reply.author_avatar"
                    :datetime="formatDate(reply.created_at?.$date)"
                  >
                    <p>{{ reply.content }}</p>
                  </a-comment>
                </div>
              </a-comment>

              <!-- 添加评论 -->
              <a-comment>
                <template #avatar>
                  <a-avatar
                    :src="'http://localhost:5000/' + authStore.user?.avatar"
                  />
                </template>
                <template #content>
                  <a-textarea
                    v-model:value="newComment"
                    :rows="4"
                    placeholder="写下你的评论..."
                  />
                  <div class="comment-actions">
                    <a-button
                      type="primary"
                      @click="submitComment"
                      :loading="commentLoading"
                    >
                      发表评论
                    </a-button>
                  </div>
                </template>
              </a-comment>
            </a-card>
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import DOMPurify from "dompurify";
import { message } from "ant-design-vue";
import forumApi from "@/api/forum";
import type { ForumPost, ForumAttachment, ForumComment } from "@/api/forum";
import {
  ArrowLeftOutlined,
  EyeOutlined,
  LikeOutlined,
  StarOutlined,
  LikeFilled,
  StarFilled,
  DownloadOutlined,
  ClockCircleOutlined,
  UserAddOutlined,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";

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

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// 数据状态
const post = ref<ForumPost>({} as ForumPost);
const attachments = ref<ForumAttachment[]>([]);
const comments = ref<ForumComment[]>([]);
const loading = ref(true);
const likeLoading = ref(false);
const favoriteLoading = ref(false);
const commentLoading = ref(false);
const compiledContent = ref("");
const newComment = ref("");

// 计算属性：图片附件和其他附件
const imageAttachments = computed(() =>
  attachments.value.filter((att) =>
    ["jpg", "jpeg", "png", "gif", "webp"].some((ext) =>
      att.file_path.toLowerCase().endsWith(ext)
    )
  )
);

const otherAttachments = computed(() =>
  attachments.value.filter(
    (att) =>
      !["jpg", "jpeg", "png", "gif", "webp"].some((ext) =>
        att.file_path.toLowerCase().endsWith(ext)
      )
  )
);

// 获取文件类型
const getFileType = (fileName: string) => {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (!ext) return "file";

  if (["jpg", "jpeg", "png", "gif", "webp"].includes(ext)) return "image";
  if (ext === "pdf") return "pdf";
  if (["doc", "docx"].includes(ext)) return "word";
  if (["xls", "xlsx"].includes(ext)) return "excel";
  if (["ppt", "pptx"].includes(ext)) return "ppt";
  if (ext === "txt") return "text";
  if (["zip", "rar", "7z"].includes(ext)) return "zip";
  return "file";
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
    const [postRes, attachmentsRes, commentsRes] = await Promise.all([
      forumApi.getPostDetail(postId),
      forumApi.getAttachments(postId),
      forumApi.getComments(postId),
    ]);

    post.value = postRes;
    attachments.value = attachmentsRes;
    comments.value = commentsRes;

    // 安全处理Markdown内容
    compiledContent.value = DOMPurify.sanitize(md.render(postRes.content));
  } catch (error) {
    message.error("加载帖子失败");
    router.push({ name: "forum-home" });
  } finally {
    loading.value = false;
  }
};

// 点赞处理
const handleLike = async () => {
  try {
    likeLoading.value = true;
    if (post.value.is_liked) {
      await forumApi.unlikePost(post.value.id);
      post.value.like_count--;
    } else {
      await forumApi.likePost(post.value.id);
      post.value.like_count++;
    }
    post.value.is_liked = !post.value.is_liked;
  } catch (error) {
    message.error("操作失败");
  } finally {
    likeLoading.value = false;
  }
};

// 收藏处理
const handleFavorite = async () => {
  try {
    favoriteLoading.value = true;
    if (post.value.is_favorited) {
      await forumApi.unfavoritePost(post.value.id);
      post.value.favorite_count--;
    } else {
      await forumApi.favoritePost(post.value.id);
      post.value.favorite_count++;
    }
    post.value.is_favorited = !post.value.is_favorited;
  } catch (error) {
    message.error("操作失败");
  } finally {
    favoriteLoading.value = false;
  }
};

// 提交评论
const submitComment = async () => {
  if (!newComment.value.trim()) {
    message.warning("请输入评论内容");
    return;
  }

  try {
    commentLoading.value = true;
    const comment = await forumApi.addComment(post.value.id, {
      content: newComment.value,
    });
    comments.value.push(comment);
    newComment.value = "";
    message.success("评论发表成功");
  } catch (error) {
    message.error("评论发表失败");
  } finally {
    commentLoading.value = false;
  }
};

// 回复评论
const replyTo = (comment: ForumComment) => {
  newComment.value = `@${comment.author_name} `;
  // 这里可以添加更多回复逻辑，如聚焦到输入框等
};

// 显示关注模态框
const showFollowModal = () => {
  message.info("关注功能即将上线");
};

onMounted(loadPostData);
</script>

<style scoped>
.post-detail-view {
  max-width: 1200px;
  margin: 0 auto;
  height: 85vh;
  display: flex;
  flex-direction: column;
}
.page-header {
  padding: 0;
  margin-bottom: 24px;
}

.content-wrapper {
  flex: 1;
  position: relative;
  overflow-y: auto; /* 添加此行以启用滚动 */
}

.post-container {
  background: #fff;
  border-radius: 8px;
}

.author-card {
  margin-bottom: 24px;
  background: #f8f9fa;
  border-radius: 8px;
}

.author-avatar {
  border: 2px solid #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.author-info {
  padding: 8px 0;
}

.author-name {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.post-meta {
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 14px;
}

.post-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.content-section {
  padding: 0 24px 24px;
}

.content-card {
  margin-bottom: 24px;
  border-radius: 8px;
}

.markdown-content {
  line-height: 1.8;
  font-size: 15px;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
  margin-top: 24px;
  margin-bottom: 16px;
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

.image-gallery-card,
.attachments-card,
.comments-card {
  margin-bottom: 24px;
  border-radius: 8px;
}

.gallery-image {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
}

.image-actions {
  text-align: center;
}

.attachment-item {
  text-align: center;
}

.comment-actions {
  margin-top: 16px;
  text-align: right;
}

@media (max-width: 768px) {
  .post-detail-view {
    padding: 16px;
  }

  .content-section {
    padding: 0 16px 16px;
  }

  .author-card {
    padding: 16px;
  }

  .author-avatar {
    width: 60px;
    height: 60px;
  }

  .author-name {
    font-size: 16px;
  }

  .post-meta {
    flex-direction: column;
    gap: 4px;
  }

  .gallery-image {
    height: 120px;
  }
}
</style>

<style>
/* 全局样式调整 */
.ant-comment-actions {
  margin-top: 8px;
}

.ant-comment-content-author-name {
  font-weight: 500;
}

.ant-comment-content-detail p {
  margin-bottom: 0;
  line-height: 1.6;
}

.ant-image-preview-img {
  max-height: 80vh;
}

.ant-image-preview-operations {
  background: rgba(0, 0, 0, 0.5);
}
</style>
