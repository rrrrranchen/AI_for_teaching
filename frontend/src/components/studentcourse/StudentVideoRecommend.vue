<!-- src/components/studentcourse/StudentVideoRecommend.vue -->
<template>
  <div class="video-recommend-container">
    <a-spin :spinning="loading">
      <div v-if="videoList.length > 0" class="video-content">
        <!-- 左侧视频播放器 -->
        <div class="video-player">
          <iframe
            :src="`https://player.bilibili.com/player.html?bvid=${currentVideo.bvid}&high_quality=1&danmaku=0`"
            width="100%"
            height="700"
            scrolling="no"
            frameborder="no"
            sandbox="allow-top-navigation allow-same-origin allow-forms allow-scripts allow-popups"
          ></iframe>
          <div class="video-info">
            <h3>{{ currentVideo.title }}</h3>
            <p>{{ currentVideo.description }}</p>
          </div>
        </div>

        <!-- 右侧推荐列表 -->
        <div class="video-list">
          <h3>课后推荐视频 ({{ videoList.length }})</h3>
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

      <a-empty v-else description="暂无课后推荐视频">
        <a-button type="primary" @click="generateRecommendations">
          <template #icon><bulb-outlined /></template>
          生成推荐视频
        </a-button>
      </a-empty>
    </a-spin>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import { message } from "ant-design-vue";
import { BulbOutlined } from "@ant-design/icons-vue";
import {
  generatePostClassRecommendations,
  getPostClassRecommendations,
} from "@/api/student_recommend";

interface VideoItem {
  title: string;
  description: string;
  link: string;
  bvid: string;
}

export default defineComponent({
  name: "StudentVideoRecommend",
  components: {
    BulbOutlined,
  },
  props: {
    courseId: {
      type: Number,
      required: true,
    },
  },
  setup(props) {
    const loading = ref(false);
    const generating = ref(false);
    const currentVideoIndex = ref(0);
    const videoList = ref<VideoItem[]>([]);

    // 从链接中提取BV号
    const extractBvid = (link: string) => {
      const match = link.match(/video\/(BV\w+)/);
      return match ? match[1] : "";
    };

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
    };

    // 加载推荐视频
    const loadRecommendations = async () => {
      try {
        loading.value = true;
        const response = await getPostClassRecommendations(props.courseId);
        if (response && response.video_recommendations === null) {
          message.info("暂未生成视频资源");
          loading.value = false;
          return;
        } else if (response && response.video_recommendations) {
          try {
            const parsedData = JSON.parse(response.video_recommendations);
            if (parsedData.videos && Array.isArray(parsedData.videos)) {
              videoList.value = parsedData.videos.map((video: any) => ({
                ...video,
                bvid: extractBvid(video.link),
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
        message.error("获取推荐视频失败");
        console.error("获取推荐视频错误:", error);
      } finally {
        loading.value = false;
      }
    };

    // 生成推荐视频
    const generateRecommendations = async () => {
      try {
        generating.value = true;
        await generatePostClassRecommendations(props.courseId);
        await loadRecommendations();
        message.success("课后推荐视频生成成功");
      } catch (error) {
        message.error("生成课后推荐视频失败");
        console.error("生成推荐视频错误:", error);
      } finally {
        generating.value = false;
      }
    };

    // 初始化加载
    onMounted(async () => {
      await loadRecommendations();
    });

    return {
      loading,
      generating,
      videoList,
      currentVideo,
      currentVideoIndex,
      generateRecommendations,
      changeVideo,
    };
  },
});
</script>

<style scoped>
.video-recommend-container {
  padding: 16px;
  border-radius: 8px;
  height: calc(100vh - 64px - 32px);
}

.video-content {
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
  .video-content {
    flex-direction: column;
  }

  .video-player,
  .video-list {
    flex: none;
    width: 100%;
  }
}
</style>
