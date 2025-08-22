<template>
  <div class="learning-path-generator">
    <!-- 生成学习路线表单 -->
    <div v-if="!learningPathData && !loadingExistingPath" class="generate-form">
      <div class="section-title">
        <h3>生成学习路线</h3>
        <p>输入您的学习目标，AI将为您规划个性化学习路径</p>
      </div>
      <a-form :model="formState" layout="vertical">
        <a-form-item label="学习目标" required>
          <a-textarea
            v-model:value="formState.target"
            placeholder="例如：前端开发、Python数据分析、机器学习基础等"
            :rows="3"
            :maxlength="100"
            show-count
          />
        </a-form-item>
        <a-button
          type="primary"
          :loading="generating"
          :disabled="!formState.target.trim()"
          @click="generateLearningPath"
          block
        >
          {{ generating ? "生成中..." : "生成学习路线" }}
        </a-button>
      </a-form>
    </div>

    <!-- 加载状态 -->
    <div v-if="loadingExistingPath" class="loading-container">
      <a-spin size="large" tip="加载学习路线中..." />
    </div>

    <!-- 学习路线展示 -->
    <div
      v-else-if="learningPathData && !showSearchResults"
      class="learning-path-container"
    >
      <div class="path-header">
        <h3>{{ learningPathData.name }} 学习路线</h3>
        <div class="header-actions">
          <a-button type="link" @click="regeneratePath">
            <template #icon><reload-outlined /></template>
            重新生成
          </a-button>
        </div>
      </div>

      <div class="chart-container">
        <div ref="chartRef" style="width: 100%; height: 400px"></div>
      </div>

      <div class="path-tips">
        <info-circle-outlined />
        <span>点击路线节点可推荐相关课程</span>
      </div>
    </div>

    <!-- 课程搜索结果 -->
    <div v-else-if="showSearchResults" class="search-results-container">
      <div class="results-header">
        <a-button
          type="link"
          @click="showSearchResults = false"
          class="back-button"
        >
          <template #icon><arrow-left-outlined /></template>
          返回学习路线
        </a-button>
        <h4>「{{ selectedNodeName }}」相关课程</h4>
      </div>

      <a-list
        :data-source="searchResults"
        :loading="searchLoading"
        class="results-list"
      >
        <template #renderItem="{ item }">
          <a-list-item class="result-item">
            <a-list-item-meta>
              <template #title>
                <router-link :to="`/home/public-courseclass/${item.id}`">
                  {{ item.name }}
                </router-link>
              </template>
              <template #description>
                <div class="course-info">
                  <p class="course-desc">
                    {{ item.description || "暂无描述" }}
                  </p>
                  <div class="course-stats">
                    <span v-if="item.courses && item.courses.length">
                      <book-outlined /> {{ item.courses.length }}门课程
                    </span>
                    <span v-if="item.score !== undefined">
                      <star-outlined /> 匹配度:
                      {{ (item.score * 100).toFixed(1) }}%
                    </span>
                  </div>
                </div>
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>

        <template #loadMore>
          <div v-if="hasMoreResults" class="load-more">
            <a-button @click="loadMoreResults" :loading="searchLoading">
              加载更多
            </a-button>
          </div>
        </template>

        <template #empty>
          <a-empty description="未找到相关课程" />
        </template>
      </a-list>
    </div>

    <!-- 错误提示 -->
    <a-modal
      v-model:visible="showErrorModal"
      title="生成失败"
      :footer="null"
      width="400px"
    >
      <div class="error-content">
        <exclamation-circle-outlined class="error-icon" />
        <p>{{ errorMessage }}</p>
        <a-button type="primary" @click="showErrorModal = false">
          确定
        </a-button>
      </div>
    </a-modal>
  </div>
</template>

<script lang="ts">
import {
  defineComponent,
  ref,
  reactive,
  onMounted,
  onUnmounted,
  nextTick,
  watch,
} from "vue";
import { message } from "ant-design-vue";
import * as echarts from "echarts";
import type { ECharts, ECElementEvent } from "echarts";
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  BookOutlined,
  StarOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons-vue";
import {
  generateLearningPath,
  searchPublicClasses,
  getUserLearningPath,
  type LearningPathResponse,
  type PublicClassSearchResponse,
  type PublicClassResult,
} from "@/api/student_recommend";

interface FormState {
  target: string;
}

export default defineComponent({
  name: "LearningPathGenerator",
  components: {
    ArrowLeftOutlined,
    ReloadOutlined,
    InfoCircleOutlined,
    BookOutlined,
    StarOutlined,
    ExclamationCircleOutlined,
  },
  setup() {
    const formState = reactive<FormState>({
      target: "",
    });

    const generating = ref(false);
    const loadingExistingPath = ref(true); // 新增：加载已有路径的状态
    const learningPathData = ref<LearningPathResponse | null>(null);
    const chartRef = ref<HTMLElement | null>(null);
    const chartInstance = ref<ECharts | null>(null);
    const showSearchResults = ref(false);
    const selectedNodeName = ref("");
    const searchResults = ref<PublicClassResult[]>([]);
    const searchLoading = ref(false);
    const currentPage = ref(1);
    const hasMoreResults = ref(false);
    const showErrorModal = ref(false);
    const errorMessage = ref("");

    // 加载已有学习路径
    const loadExistingLearningPath = async () => {
      try {
        loadingExistingPath.value = true;
        const existingPath = await getUserLearningPath();
        if (existingPath) {
          learningPathData.value = existingPath;
          await nextTick();
          setTimeout(() => {
            initChart();
          }, 100);
        }
      } catch (error: any) {
        console.error("加载已有学习路径失败:", error);
        // 不显示错误，因为用户可能还没有生成过学习路径
      } finally {
        loadingExistingPath.value = false;
      }
    };

    // 初始化图表
    const initChart = () => {
      if (!chartRef.value || !learningPathData.value) return;

      chartInstance.value = echarts.init(chartRef.value);

      const option = {
        tooltip: {
          trigger: "item",
          triggerOn: "mousemove",
          formatter: "{b}",
        },
        series: [
          {
            type: "tree",
            data: [convertToTreeData(learningPathData.value)],
            top: "1%",
            left: "7%",
            bottom: "1%",
            right: "20%",
            symbolSize: 7,
            label: {
              position: "left",
              verticalAlign: "middle",
              align: "right",
              fontSize: 14,
              fontWeight: "bold",
            },
            leaves: {
              label: {
                position: "right",
                verticalAlign: "middle",
                align: "left",
              },
            },
            emphasis: {
              focus: "descendant",
            },
            expandAndCollapse: true,
            animationDuration: 550,
            animationDurationUpdate: 750,
          },
        ],
      };

      chartInstance.value.setOption(option);

      // 添加点击事件监听
      chartInstance.value.on("click", handleChartClick);
    };

    // 将学习路线数据转换为ECharts树形图数据格式
    const convertToTreeData = (data: LearningPathResponse) => {
      const convertNode = (node: any) => {
        const result: any = {
          name: node.name,
          itemStyle: node.itemStyle || { color: "#5470c6" },
        };

        if (node.children && node.children.length > 0) {
          result.children = node.children.map(convertNode);
        }

        return result;
      };

      return convertNode(data);
    };

    // 处理图表点击事件
    const handleChartClick = (params: ECElementEvent) => {
      if (params.data && params.data.name) {
        searchCourses(params.data.name);
      }
    };

    // 搜索课程
    const searchCourses = async (keyword: string) => {
      try {
        searchLoading.value = true;
        selectedNodeName.value = keyword;

        const response = await searchPublicClasses(keyword, 1, 10);
        searchResults.value = response.results;
        currentPage.value = 1;
        hasMoreResults.value = response.total > response.results.length;

        showSearchResults.value = true;
      } catch (error: any) {
        message.error("搜索课程失败: " + (error.message || "未知错误"));
      } finally {
        searchLoading.value = false;
      }
    };

    // 加载更多结果
    const loadMoreResults = async () => {
      try {
        searchLoading.value = true;
        const nextPage = currentPage.value + 1;

        const response = await searchPublicClasses(
          selectedNodeName.value,
          nextPage,
          10
        );
        searchResults.value = [...searchResults.value, ...response.results];
        currentPage.value = nextPage;
        hasMoreResults.value = response.total > searchResults.value.length;
      } catch (error: any) {
        message.error("加载更多失败: " + (error.message || "未知错误"));
      } finally {
        searchLoading.value = false;
      }
    };

    // 生成学习路线
    const generateLearningPathHandler = async () => {
      if (!formState.target.trim()) {
        message.warning("请输入学习目标");
        return;
      }

      try {
        generating.value = true;
        const response = await generateLearningPath(formState.target.trim());
        learningPathData.value = response;

        await nextTick();
        initChart();
      } catch (error: any) {
        errorMessage.value = error.message || "生成学习路线失败，请稍后重试";
        showErrorModal.value = true;
      } finally {
        generating.value = false;
      }
    };

    // 重新生成路线
    const regeneratePath = () => {
      learningPathData.value = null;
      showSearchResults.value = false;
      formState.target = ""; // 清空表单以便重新输入
    };

    // 重置表单
    const resetForm = () => {
      formState.target = "";
      learningPathData.value = null;
      showSearchResults.value = false;
    };

    // 响应式调整图表大小
    const resizeChart = () => {
      if (chartInstance.value) {
        chartInstance.value.resize();
      }
    };

    onMounted(() => {
      window.addEventListener("resize", resizeChart);
      // 组件挂载时加载已有学习路径
      loadExistingLearningPath();
    });

    onUnmounted(() => {
      window.removeEventListener("resize", resizeChart);
      if (chartInstance.value) {
        chartInstance.value.dispose();
      }
    });
    // 在setup函数中添加watch监听
    watch(showSearchResults, (newVal: boolean) => {
      if (!newVal && learningPathData.value) {
        // 当从搜索结果返回学习路线时，重新初始化图表
        setTimeout(() => {
          initChart();
        }, 100);
      }
    });

    return {
      formState,
      generating,
      loadingExistingPath, // 暴露给模板
      learningPathData,
      chartRef,
      showSearchResults,
      selectedNodeName,
      searchResults,
      searchLoading,
      hasMoreResults,
      showErrorModal,
      errorMessage,
      generateLearningPath: generateLearningPathHandler,
      regeneratePath,
      resetForm,
      searchCourses,
      loadMoreResults,
    };
  },
});
</script>

<style scoped lang="less">
// 添加加载状态的样式
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}
.learning-path-generator {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  height: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.generate-form {
  .section-title {
    margin-bottom: 20px;

    h3 {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 4px;
      color: #1a1a1a;
    }

    p {
      font-size: 14px;
      color: #8c8c8c;
      margin: 0;
    }
  }
}

.learning-path-container {
  .path-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1a1a1a;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .chart-container {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
    background: #fafafa;
  }

  .path-tips {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    padding: 8px 12px;
    background: #e6f7ff;
    border: 1px solid #91d5ff;
    border-radius: 6px;
    font-size: 12px;
    color: #1890ff;
  }
}

.search-results-container {
  .results-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;

    h4 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #1a1a1a;
    }

    .back-button {
      padding: 0;
    }
  }

  .results-list {
    max-height: 400px;
    overflow-y: auto;

    .result-item {
      padding: 12px 0;
      border-bottom: 1px solid #f0f0f0;

      &:hover {
        background: #fafafa;
      }

      .course-info {
        .course-desc {
          margin: 0 0 8px 0;
          font-size: 12px;
          color: #8c8c8c;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .course-stats {
          display: flex;
          gap: 16px;
          font-size: 11px;
          color: #bfbfbf;

          span {
            display: flex;
            align-items: center;
            gap: 4px;
          }
        }
      }
    }
  }

  .load-more {
    text-align: center;
    padding: 16px;
  }
}

.error-content {
  text-align: center;
  padding: 20px;

  .error-icon {
    font-size: 48px;
    color: #ff4d4f;
    margin-bottom: 16px;
  }

  p {
    margin: 0 0 20px 0;
    color: #8c8c8c;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .learning-path-generator {
    padding: 16px;
  }

  .path-header {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 12px;
  }

  .chart-container {
    padding: 12px;
  }
}
</style>
