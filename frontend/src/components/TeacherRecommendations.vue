<!-- src/components/TeacherRecommendations.vue -->
<template>
  <div class="teacher-recommendations">
    <a-spin :spinning="loadingRecommend">
      <div v-if="videoList.length > 0" class="video-container">
        <!-- 左侧视频播放器 -->
        <div class="video-player">
          <iframe
            :src="`//player.bilibili.com/player.html?bvid=${currentVideo.bvid}&page=1`"
            width="100%"
            height="800"
            scrolling="no"
            frameborder="0"
          ></iframe>
          <div class="video-info">
            <h3>{{ currentVideo.title }}</h3>
            <p>{{ currentVideo.description }}</p>
          </div>
        </div>

        <!-- 右侧推荐列表 -->
        <div class="video-list">
          <h3>推荐视频列表 ({{ videoList.length }})</h3>
          <a-list
            :data-source="videoList"
            item-layout="horizontal"
            :split="false"
          >
            <template #renderItem="{ item, index }">
              <a-list-item
                :class="['video-item', { active: currentVideoIndex === index }]"
                @click="changeVideo(index)"
              >
                <a-list-item-meta :description="item.description">
                  <template #title>
                    <a>{{ index + 1 }}. {{ item.title }}</a>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
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
} from "@/api/teacher_recommend";
import { BulbOutlined } from "@ant-design/icons-vue";

interface VideoItem {
  title: string;
  description: string;
  link: string;
  bvid: string;
}

export default defineComponent({
  name: "TeacherRecommendations",
  components: {
    BulbOutlined,
  },
  props: {
    designId: {
      type: Number,
      required: true,
    },
  },
  setup(props) {
    const loadingRecommend = ref(false);
    const currentVideoIndex = ref(0);
    const videoList = ref<VideoItem[]>([]);

    // 当前播放的视频
    const currentVideo = computed(() => {
      return (
        videoList.value[currentVideoIndex.value] || {
          title: "",
          description: "",
          link: "",
          bvid: "",
        }
      );
    });

    // 切换视频
    const changeVideo = (index: number) => {
      currentVideoIndex.value = index;
      // 滚动到选中的视频项
      const element = document.querySelector(`.video-item.active`);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    };
    const parseVideoLink = (link: string) => {
      // 支持两种B站链接格式：
      // 1. https://www.bilibili.com/video/BV1La411e7NC/
      // 2. https://b23.tv/BV1La411e7NC
      const match = link.match(/(?:video\/|tv\/)(BV\w+)/);
      return match ? match[1] : null;
    };
    // 加载推荐资源
    const loadRecommendations = async () => {
      try {
        loadingRecommend.value = true;
        const response = await getRecommendationByDesign(props.designId);
        console.log("Response:", response!.video_recommendations);
        // 直接解析返回的JSON数据
        if (response && response.video_recommendations) {
          try {
            const parsedData = JSON.parse(response.video_recommendations);
            if (parsedData.videos && Array.isArray(parsedData.videos)) {
              // 在loadRecommendations中处理数据时
              videoList.value = parsedData.videos.map((video: any) => ({
                ...video,
                bvid: parseVideoLink(video.link),
              }));
              if (videoList.value.length > 0) {
                currentVideoIndex.value = 0;
              }
            }
          } catch (e) {
            console.error("JSON解析错误:", e);
            message.error("视频数据格式不正确");
          }
        }
      } catch (error) {
        message.error("获取推荐资源失败");
        console.error("获取推荐资源错误:", error);
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
        console.error("生成推荐资源错误:", error);
      } finally {
        loadingRecommend.value = false;
      }
    };

    // 初始化加载
    onMounted(async () => {
      await loadRecommendations();
    });

    return {
      loadingRecommend,
      videoList,
      currentVideo,
      currentVideoIndex,
      generateRecommend,
      changeVideo,
    };
  },
});
</script>

<style scoped>
.teacher-recommendations {
  padding: 16px;
  border-radius: 8px;
  height: calc(100vh - 64px - 32px);
}

.video-container {
  display: flex;
  gap: 24px;
  height: 100%;
}

.video-player {
  flex: 3;
  min-width: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-info h3 {
  margin: 0;
  font-size: 18px;
  color: rgba(0, 0, 0, 0.85);
}

.video-info p {
  margin: 8px 0 0;
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
  line-height: 1.6;
}

.video-list {
  flex: 1;
  min-width: 300px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  padding: 16px;
  overflow-y: auto;
  max-height: 600px;
}

.video-item {
  padding: 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 8px;
}

.video-item:hover {
  background-color: #f5f5f5;
}

.video-item.active {
  background-color: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.video-item :deep(.ant-list-item-meta-title) {
  margin-bottom: 4px;
  font-weight: 500;
  font-size: 14px;
}

.video-item :deep(.ant-list-item-meta-description) {
  color: rgba(0, 0, 0, 0.65);
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 空状态样式 */
.ant-empty {
  margin: 40px 0;
}

@media (max-width: 768px) {
  .video-container {
    flex-direction: column;
  }

  .video-player,
  .video-list {
    flex: none;
    width: 100%;
  }
}
</style>
