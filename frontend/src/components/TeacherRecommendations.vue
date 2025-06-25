<!-- src/components/TeacherRecommendations.vue -->
<template>
  <div class="teacher-recommendations">
    <a-spin :spinning="loadingRecommend">
      <div v-if="recommendData">
        <!-- 视频推荐 -->
        <div class="video-recommendations">
          <h3>视频资源推荐</h3>
          <div class="markdown-content" v-html="renderedVideoRecommend"></div>
        </div>

        <div class="image-recommendations">
          <h3>推荐图片素材</h3>
          <a-empty
            v-if="imageRecommendations.length === 0"
            description="暂无推荐图片"
          />
          <div v-else class="image-grid">
            <div
              v-for="(img, index) in imageRecommendations"
              :key="index"
              class="image-item"
            >
              <a-image :src="img" height="150px" :preview="true">
                <template #previewMask>
                  <a-button type="primary" @click.stop="downloadImage(img)">
                    <download-outlined /> 下载
                  </a-button>
                </template>
              </a-image>
            </div>
          </div>
        </div>
      </div>

      <a-empty v-else description="暂无推荐资源">
        <a-button type="primary" @click="generateRecommend">
          <template #icon><bulb-outlined /></template>
          生成推荐资源
        </a-button>
      </a-empty>
    </a-spin>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import { message } from "ant-design-vue";
import {
  generateTeachingRecommendation,
  getRecommendationByDesign,
  type RecommendationData,
} from "@/api/teacher_recommend";
import { DownloadOutlined, BulbOutlined } from "@ant-design/icons-vue";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

// 初始化 Markdown 解析器
const initMarkdownParser = () => {
  return new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
    highlight: function (str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return (
            '<pre class="hljs"><code>' +
            hljs.highlight(str, { language: lang, ignoreIllegals: true })
              .value +
            "</code></pre>"
          );
        } catch (err) {
          console.error("代码高亮错误:", err);
        }
      }
      return (
        '<pre class="hljs"><code>' +
        MarkdownIt().utils.escapeHtml(str) +
        "</code></pre>"
      );
    },
  });
};

export default defineComponent({
  name: "TeacherRecommendations",
  components: {
    DownloadOutlined,
    BulbOutlined,
  },
  props: {
    designId: {
      type: Number,
      required: true,
    },
  },
  setup(props) {
    const md = initMarkdownParser();
    const recommendData = ref<RecommendationData | null>(null);
    const loadingRecommend = ref(false);

    // 计算属性渲染Markdown
    const renderedVideoRecommend = computed(() => {
      if (!recommendData.value?.video_recommendations) return "";

      // 预处理代码块
      const content = recommendData.value.video_recommendations
        .replace(/<pre><code>/g, "```") // 转换旧格式代码块
        .replace(/<\/code><\/pre>/g, "```");

      return md.render(content);
    });

    // 加载推荐资源
    const loadRecommendations = async () => {
      try {
        loadingRecommend.value = true;
        recommendData.value = await getRecommendationByDesign(props.designId);
        console.log("获取的资源：", recommendData.value);
      } catch (error) {
        message.error("获取推荐资源失败");
      } finally {
        loadingRecommend.value = false;
      }
    };

    // 生成推荐资源
    const generateRecommend = async () => {
      try {
        loadingRecommend.value = true;
        await generateTeachingRecommendation(props.designId);
        await loadRecommendations();
        message.success("推荐资源生成成功");
      } catch (error) {
        message.error("推荐资源生成失败");
      } finally {
        loadingRecommend.value = false;
      }
    };

    // 下载图片
    const downloadImage = (url: string) => {
      const link = document.createElement("a");
      link.href = url;
      link.download = url.split("/").pop() || "recommend-image";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    // 新增：解析图片推荐数据
    const imageRecommendations = computed(() => {
      if (!recommendData.value?.image_recommendations) return [];

      try {
        const parsed = JSON.parse(recommendData.value.image_recommendations);
        return parsed.images || [];
      } catch (error) {
        console.error("图片数据解析失败:", error);
        return [];
      }
    });
    // 初始化加载
    onMounted(async () => {
      await loadRecommendations();
    });

    return {
      recommendData,
      loadingRecommend,
      renderedVideoRecommend,
      imageRecommendations,
      generateRecommend,
      downloadImage,
    };
  },
});
</script>

<style scoped>
.teacher-recommendations {
  padding: 16px;
  background: #fbfaef;
  border: 5px solid #fcf9d3;
  border-radius: 8px;
  height: 83vh;
}

/* Markdown 内容样式 */
.markdown-content {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  max-height: 50vh;
  overflow-y: auto;
  line-height: 1.6;
}

.markdown-content :deep() h1,
.markdown-content :deep() h2,
.markdown-content :deep() h3 {
  color: rgba(0, 0, 0, 0.85);
  margin: 1em 0;
}

.markdown-content :deep() pre {
  max-width: 100%;
  overflow-x: auto;
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  margin: 1em 0;
}

.markdown-content :deep() code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.9em;
}

.markdown-content :deep() img {
  max-width: 100%;
  height: auto;
  margin: 1em 0;
  border-radius: 4px;
}

.markdown-content :deep() table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  background: #fff;
}

.markdown-content :deep() th,
.markdown-content :deep() td {
  border: 1px solid #dfe2e5;
  padding: 0.6em 1em;
  text-align: left;
}

.markdown-content :deep() blockquote {
  border-left: 4px solid #1890ff;
  margin: 1em 0;
  padding-left: 1em;
  color: #6a737d;
  background: #f8f8f8;
}

/* 图片网格样式 */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.image-item {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  transition: transform 0.2s;
}

.image-item:hover {
  transform: translateY(-3px);
}

/* 空状态样式 */
.ant-empty {
  margin: 40px 0;
}
</style>
