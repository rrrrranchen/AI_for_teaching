<template>
  <div class="recommended-designs">
    <h3 class="section-title">推荐教学设计</h3>
    <a-spin :spinning="loading">
      <div class="carousel-container" :style="containerStyle">
        <a-empty v-if="designs.length === 0" description="暂无推荐教学设计" />
        <div v-else class="carousel-wrapper">
          <div class="carousel-track" :style="trackStyle">
            <div
              v-for="(design, index) in designs"
              :key="design.design_id"
              class="design-card"
              :class="{ active: currentIndex === index }"
            >
              <a-card hoverable @click="handleDesignClick(design)">
                <template #cover>
                  <div class="card-cover">
                    <img
                      v-if="design.author_avatar"
                      :src="design.author_avatar"
                      alt="作者头像"
                      class="author-avatar"
                    />
                    <div v-else class="avatar-placeholder">
                      {{ design.author_name.charAt(0) }}
                    </div>
                  </div>
                </template>
                <a-card-meta :title="design.title">
                  <template #description>
                    <div class="design-meta">
                      <div class="author-info">
                        <span>{{ design.author_name }}</span>
                      </div>
                      <div class="content-preview">
                        {{ design.version_content }}
                      </div>
                      <div class="recommend-time" v-if="design.recommend_time">
                        推荐于 {{ formatDate(design.recommend_time) }}
                      </div>
                    </div>
                  </template>
                </a-card-meta>
              </a-card>
            </div>
          </div>
          <div class="carousel-controls" v-if="designs.length > 3">
            <button class="control-btn prev" @click="prevSlide">
              <LeftOutlined />
            </button>
            <button class="control-btn next" @click="nextSlide">
              <RightOutlined />
            </button>
          </div>
        </div>
      </div>
    </a-spin>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from "vue";
import { message } from "ant-design-vue";
import { LeftOutlined, RightOutlined } from "@ant-design/icons-vue";
import { forumApi } from "@/api/forum";
import type { RecommendedTeachingDesign } from "@/api/forum";

const designs = ref<RecommendedTeachingDesign[]>([]);
const loading = ref(false);
const currentIndex = ref(0);

const fetchRecommendedDesigns = async () => {
  try {
    loading.value = true;
    const result = await forumApi.getRecommendedDesigns();
    designs.value = result;
  } catch (error) {
    message.error("获取推荐教学设计失败");
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return `${date.getMonth() + 1}月${date.getDate()}日`;
};

const handleDesignClick = (design: RecommendedTeachingDesign) => {
  // 这里可以添加跳转到教学设计详情的逻辑
  console.log("点击教学设计:", design);
};

// 在脚本部分添加响应式卡片宽度控制
const cardWidth = ref(290); // 默认宽度，可以通过props传入或动态修改
const cardGap = ref(16);
const visibleCards = ref(3);

// 计算容器宽度
const containerStyle = computed(() => ({
  width: `${
    visibleCards.value * (cardWidth.value + cardGap.value) + cardGap.value
  }px`,
  maxWidth: "100%", // 确保不超过父容器
}));

// 计算轨道宽度
const trackStyle = computed(() => ({
  transform: `translateX(${
    -currentIndex.value * (cardWidth.value + cardGap.value)
  }px)`,
  width: `${
    designs.value.length * (cardWidth.value + cardGap.value) - cardGap.value
  }px`,
  display: "flex",
  gap: `${cardGap.value}px`,
}));

const prevSlide = () => {
  currentIndex.value = Math.max(0, currentIndex.value - 1);
};

const nextSlide = () => {
  currentIndex.value = Math.min(
    designs.value.length - 3,
    currentIndex.value + 1
  );
};

onMounted(() => {
  fetchRecommendedDesigns();
});
</script>

<style scoped>
.recommended-designs {
  margin-bottom: 24px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
}

.section-title::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 16px;
  background-color: #1890ff;
  margin-right: 8px;
  border-radius: 2px;
}

.carousel-container {
  width: 100%;
  overflow: hidden;
  position: relative;
}

.carousel-wrapper {
  position: relative;
  width: 100%;
  margin: center;
}

.carousel-track {
  display: flex;
  gap: 16px;
  transition: transform 0.5s ease;
  padding: 8px 0;
  will-change: transform; /* 提升动画性能 */
  backface-visibility: hidden; /* 防止渲染问题 */
  padding: 18px;
}

.design-card {
  flex: 0 0 auto; /* 修改这里 */
  width: v-bind('cardWidth + "px"'); /* 使用v-bind绑定响应式宽度 */
  min-width: 0; /* 防止内容溢出 */
}

/* 确保卡片内容不会撑开宽度 */
.design-card .ant-card {
  width: 100%;
  height: 100%;
  box-sizing: border-box; /* 重要 */
}

.card-cover {
  height: 120px;
  background-color: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.author-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #1890ff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.design-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.author-info {
  font-size: 14px;
  color: #666;
}

.content-preview {
  font-size: 13px;
  color: #888;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recommend-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.carousel-controls {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  transform: translateY(-50%);
  pointer-events: none;
  padding: 20px;
}

.control-btn {
  pointer-events: all;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s;
  z-index: 1;
}

.control-btn:hover {
  background: #fff;
  transform: scale(1.1);
}

.control-btn.prev {
  margin-left: -18px;
}

.control-btn.next {
  margin-right: -18px;
}
</style>
