<template>
  <div class="mind-map-editor-container">
    <div
      class="editor-main"
      :style="{
        width: showDetail ? '60vh' : '100vh',
        overflow: showDetail ? 'hidden' : 'visible',
      }"
    >
      <div class="toolbar">
        <a-button type="primary" @click="generateMindMap" :loading="generating">
          <template #icon><ReloadOutlined /></template>
          生成思维导图
        </a-button>
        <a-button type="primary" @click="saveMindMap" :loading="saving">
          <template #icon><SaveOutlined /></template>
          保存修改
        </a-button>
      </div>
      <div v-if="loading" class="loading-container">
        <a-spin tip="加载思维导图中..." />
      </div>
      <div v-else-if="mindMapData" class="mind-map-content">
        <MindMapViewer
          ref="mindMapViewer"
          :data="mindMapData"
          :editable="true"
          @node-click="handleNodeClick"
        />
      </div>
      <div v-else class="empty-container">
        <a-empty description="暂无思维导图数据">
          <a-button type="primary" @click="generateMindMap">
            生成思维导图
          </a-button>
        </a-empty>
      </div>
    </div>

    <!-- 右侧详情面板 -->
    <div v-if="showDetail" class="detail-panel">
      <div class="panel-header">
        <h3>{{ currentNodeText }}</h3>
        <a-button type="text" @click="closePanel">
          <template #icon><CloseOutlined /></template>
        </a-button>
      </div>

      <div class="detail-panel-content">
        <a-tabs v-model:activeKey="activeTab">
          <a-tab-pane key="questions" tab="关联题目" class="questions-tab">
            <a-spin :spinning="detailLoading">
              <div style="height: 100%; display: flex; flex-direction: column">
                <div
                  class="content-scrollable"
                  style="flex: 1; overflow-y: auto"
                >
                  <QuestionStats
                    v-if="currentNodeData"
                    :questions="allQuestions"
                  />
                  <a-empty v-else description="暂无关联题目数据" />
                </div>
              </div>
            </a-spin>
          </a-tab-pane>
          <a-tab-pane key="analysis" tab="AI分析">
            <a-spin :spinning="analysisLoading">
              <div style="height: 100%; display: flex; flex-direction: column">
                <div
                  class="content-scrollable"
                  style="flex: 1; overflow-y: auto"
                >
                  <div v-if="aiAnalysis" class="analysis-content">
                    <p class="analysis-text">
                      {{ aiAnalysis.analysis_report }}
                    </p>
                    <p class="analysis-time">
                      生成时间: {{ formatTime(aiAnalysis.timestamp) }}
                    </p>
                  </div>
                  <div
                    v-else-if="analysisChecked && !aiAnalysis"
                    class="analysis-actions"
                  >
                    <a-button
                      type="primary"
                      @click="getAIAnalysis"
                      :loading="analysisLoading"
                    >
                      生成AI分析报告
                    </a-button>
                  </div>
                  <a-empty v-else description="正在检查分析报告..." />
                </div>
              </div>
            </a-spin>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>
  </div>
</template>

<script>
import {
  ReloadOutlined,
  SaveOutlined,
  CloseOutlined,
} from "@ant-design/icons-vue";
import {
  generateMindMap as apiGenerateMindMap,
  updateMindMap as apiUpdateMindMap,
  getMindMap as apiGetMindMap,
} from "@/api/teachingdesign";
import mindmapApi from "@/api/mindmap";
import MindMapViewer from "./MindMapViewer.vue";
import dayjs from "dayjs";
import QuestionStats from "./QuestionStats.vue";

export default {
  name: "MindMapEditor",
  components: {
    ReloadOutlined,
    SaveOutlined,
    CloseOutlined,
    MindMapViewer,
    QuestionStats,
  },
  computed: {
    allQuestions() {
      if (!this.currentNodeData) return [];
      return this.currentNodeData.flatMap((leaf) =>
        leaf.questions.map((q) => ({
          ...q,
          knowledge_point_name: leaf.knowledge_point_name,
        }))
      );
    },
  },
  props: {
    designId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      mindMapData: null,
      loading: false,
      generating: false,
      saving: false,

      // 右侧面板相关状态
      showDetail: false,
      activeTab: "questions",
      currentNodeId: null,
      currentNodeText: "",
      currentNodeData: null,
      aiAnalysis: null,
      detailLoading: false,
      analysisLoading: false,
      analysisChecked: false, // 新增，表示是否已检查过分析报告

      // 表格列配置
      questionColumns: [
        {
          title: "题目类型",
          dataIndex: "type",
          key: "type",
          filters: [
            { text: "选择题", value: "choice" },
            { text: "填空题", value: "fill" },
            { text: "简答题", value: "short_answer" },
          ],
          onFilter: (value, record) => record.type === value,
          render: (type) => {
            const typeMap = {
              choice: "选择题",
              fill: "填空题",
              short_answer: "简答题",
            };
            return typeMap[type] || type;
          },
        },
        {
          title: "题目内容",
          dataIndex: "content",
          key: "content",
          ellipsis: true,
        },
        {
          title: "难度",
          dataIndex: "difficulty",
          key: "difficulty",
        },
      ],
    };
  },
  methods: {
    async fetchMindMap() {
      try {
        this.loading = true;
        const response = await apiGetMindMap(this.designId);
        this.mindMapData = response.mindmap;
      } catch (error) {
        this.$message.error("获取思维导图失败");
        console.error("获取思维导图错误:", error);
      } finally {
        this.loading = false;
      }
    },
    async generateMindMap() {
      try {
        this.generating = true;
        const response = await apiGenerateMindMap(this.designId);
        this.mindMapData = response.data.mind_map;
        this.$message.success("思维导图生成成功");
        this.$emit("update");
      } catch (error) {
        this.$message.error("生成思维导图失败");
        console.error("生成思维导图错误:", error);
      } finally {
        this.generating = false;
      }
    },
    async saveMindMap() {
      try {
        this.saving = true;
        const data = this.$refs.mindMapViewer.getMindMapData();
        await apiUpdateMindMap(this.designId, data);
        this.$message.success("思维导图保存成功");
        this.$emit("update");
      } catch (error) {
        this.$message.error("保存思维导图失败");
        console.error("保存思维导图错误:", error);
      } finally {
        this.saving = false;
      }
    },

    // 节点点击处理
    async handleNodeClick({ nodeId, nodeText }) {
      this.currentNodeId = nodeId;
      this.currentNodeText = nodeText;
      this.showDetail = true;
      this.activeTab = "questions";
      this.detailLoading = true;
      this.analysisChecked = false; // 重置检查状态
      this.aiAnalysis = null; // 重置分析数据

      try {
        // 并行获取题目和AI分析
        const [questionsRes, analysisRes] = await Promise.all([
          mindmapApi.getKnowledgeQuestions(nodeId),
          this.tryGetAIAnalysis(nodeId), // 尝试获取分析报告
        ]);

        this.currentNodeData = questionsRes.leaf_questions;
        this.aiAnalysis = analysisRes; // 如果有分析报告则赋值
      } catch (error) {
        this.$message.error("获取数据失败");
        console.error("获取数据错误:", error);
      } finally {
        this.detailLoading = false;
        this.analysisChecked = true; // 标记已检查
      }
    },

    async tryGetAIAnalysis(knowledgePointId) {
      try {
        this.analysisLoading = true;
        const response = await mindmapApi.getAIAnalysis(knowledgePointId);
        return response;
      } catch (error) {
        // 404表示没有分析报告，忽略这个错误
        if (error.response?.status !== 404) {
          console.error("获取AI分析错误:", error);
        }
        return null;
      } finally {
        this.analysisLoading = false;
      }
    },

    // 获取AI分析
    async getAIAnalysis() {
      if (!this.currentNodeId) return;

      this.analysisLoading = true;
      try {
        const response = await mindmapApi.generateAIAnalysis(
          this.currentNodeId
        );
        this.aiAnalysis = response;
        this.$message.success("AI分析生成成功");
      } catch (error) {
        this.$message.error("生成AI分析失败");
        console.error("AI分析错误:", error);
      } finally {
        this.analysisLoading = false;
      }
    },
    // 关闭面板
    closePanel() {
      this.showDetail = false;
      this.currentNodeId = null;
      this.currentNodeText = "";
      this.currentNodeData = null;
      this.aiAnalysis = null;
    },

    // 格式化时间
    formatTime(timestamp) {
      return dayjs(timestamp).format("YYYY-MM-DD HH:mm:ss");
    },
  },
  mounted() {
    this.fetchMindMap();
  },
  watch: {
    designId(newVal) {
      if (newVal) {
        this.fetchMindMap();
      }
    },
  },
};
</script>

<style scoped>
.mind-map-editor-container {
  display: flex;
  height: 83vh;
  border-radius: 10px;
  overflow: hidden;
  border: 5px solid #c8e5fb;
}

.editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 防止flex布局溢出 */
  border-radius: 8px;
}

.toolbar {
  padding: 10px;
  border-bottom: 2px solid #cfe7f9;
  display: flex;
  gap: 10px;
}

.loading-container,
.empty-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.mind-map-content {
  flex: 1;
  position: relative;
  background: #fff;
  min-height: 500px;
  transition: width 0.3s ease;
}

/* 右侧详情面板样式 */
.detail-panel {
  width: 40%;
  border-left: 2px solid #e3e3e3;
  display: flex;
  flex-direction: column;
  background: #fbfced;
  min-height: 0; /* 防止flex布局溢出 */
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-scrollable {
  height: 100%;
  overflow-y: auto;
  padding-right: 8px;
  box-sizing: border-box;
}

.leaf-question {
  margin-bottom: 20px;
}

.leaf-question:last-child {
  margin-bottom: 0;
}

.knowledge-content {
  color: #666;
  margin-bottom: 12px;
}

.analysis-content {
  padding: 16px;
}

.analysis-text {
  white-space: pre-wrap;
  line-height: 1.6;
}

.analysis-time {
  color: #999;
  text-align: right;
  margin-top: 16px;
}

.analysis-actions {
  padding: 16px;
  text-align: center;
}

/* 调整标签位置 */
.detail-panel ::v-deep .ant-tabs-nav {
  margin-left: 16px; /* 向右移动16px */
}
</style>
