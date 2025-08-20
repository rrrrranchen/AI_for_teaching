<template>
  <a-modal
    :visible="internalVisible"
    :width="1350"
    :footer="null"
    :bodyStyle="{ padding: '0' }"
    :style="{ top: '20px' }"
    @cancel="handleClose"
    @ok="handleClose"
    :confirmLoading="loading"
  >
    <div class="container">
      <div class="header">
        <h2>{{ kbName }} - 知识图谱</h2>
      </div>

      <div class="action-bar">
        <span class="kb-name">{{ kbName }}</span>
        <a-spin :spinning="loading" tip="加载知识图谱中...">
          <button @click="toggleLayout">
            {{ layoutType === "force" ? "切换环形布局" : "切换力导向布局" }}
          </button>
        </a-spin>
      </div>
      <div v-if="!loading" class="graph-container" ref="chartDom"></div>
      <div v-else class="loading-container">
        <a-spin tip="正在加载知识图谱数据..." size="large" />
      </div>
    </div>
  </a-modal>
</template>

<script setup>
/* ========= 依赖 ========= */
import * as echarts from "echarts";
import {
  ref,
  reactive,
  onMounted,
  onBeforeUnmount,
  nextTick,
  defineProps,
  watch,
  defineEmits,
} from "vue";
import { message } from "ant-design-vue";
import { getKnowledgeBaseGraph } from "@/api/knowledgebase";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  kbId: {
    type: Number,
    required: true,
  },
  kbName: {
    type: String,
    required: true,
  },
});
const emit = defineEmits(["update:visible", "loading"]);

/* ========= 响应式数据 ========= */
const internalVisible = ref(props.visible);
const chart = ref(null); // echarts 实例
const chartDom = ref(null); // 容器 DOM
const layoutType = ref("force"); // 布局模式：force | circular

const loading = ref(false);
const graphData = reactive({
  nodes: [],
  links: [],
  categories: [],
});
// 新增获取图谱数据方法
const fetchGraphData = async () => {
  if (!props.kbId) return;

  emit("loading", { kbId: props.kbId, loading: true });
  loading.value = true;

  try {
    const { success, data, error } = await getKnowledgeBaseGraph(props.kbId);
    if (success) {
      Object.assign(graphData, data);
      // 关键：等 DOM 渲染完再初始化
      setTimeout(() => {
        initChart();
      }, 150);
    } else {
      message.error(`获取知识图谱失败: ${error}`);
    }
  } catch (error) {
    console.error("获取知识图谱出错:", error);
    message.error("获取知识图谱数据出错");
  } finally {
    loading.value = false;
    emit("loading", { kbId: props.kbId, loading: false });
  }
};

/* ========= 方法 ========= */
// 修改initChart方法，使用响应式graphData
const initChart = () => {
  if (!chartDom.value) return;

  try {
    if (chart.value) {
      chart.value.dispose();
    }

    chart.value = echarts.init(chartDom.value);
    chart.value.setOption(getChartOption());
    chart.value.on("click", handleNodeClick);
  } catch (error) {
    console.error("图表初始化失败:", error);
  }
};

const getChartOption = () => {
  return {
    backgroundColor: "#ffffff",
    title: {
      top: "top",
      left: "center",
      textStyle: { color: "#333", fontSize: 20 },
    },
    tooltip: {
      backgroundColor: "rgba(255,255,255,0.95)",
      borderColor: "#ddd",
      borderWidth: 1,
      textStyle: { color: "#333" },
      formatter: formatTooltip,
    },
    legend: {
      data: graphData.categories.map((c) => c.name),
      top: "bottom",
      textStyle: { color: "#666" },
    },

    animationDuration: 1500,
    animationEasingUpdate: "quinticInOut",
    series: [
      {
        name: "知识图谱",
        type: "graph",
        layout: layoutType.value,
        data: graphData.nodes,
        links: graphData.links,
        categories: graphData.categories,
        roam: true,
        label: {
          show: true,
          position: "right",
          formatter: "{b}",
          color: "#333",
          fontSize: 12,
        },
        edgeLabel: {
          show: true,
          formatter: "{c}",
          color: "#666",
          fontSize: 10,
        },
        lineStyle: {
          opacity: 0.8,
          width: 1.5,
          curveness: 0.2,
          color: "source",
        },
        emphasis: {
          focus: "adjacency",
          lineStyle: { width: 3 },
          label: { show: true, fontWeight: "bold" },
        },
        ...(layoutType.value === "force"
          ? { force: { repulsion: 300, edgeLength: 100, gravity: 0.1 } }
          : { circular: { rotateLabel: true } }),
      },
    ],
  };
};

const formatTooltip = (param) => {
  if (param.dataType === "node") {
    return `<div style="font-weight:bold;color:#333">${param.name}</div>
            <div>${param.data.category || "TensorFlow组件"}</div>`;
  }
  return `<div>${param.source} → ${param.target}</div>
          <div><b>关系:</b> ${param.data.label}</div>`;
};

const handleNodeClick = (params) => {
  if (params.dataType === "node") {
    showNodeInfo(params.name);
  }
};

const showNodeInfo = (nodeName) => {
  const infoMap = {
    // TensorFlow: "谷歌开源的深度学习框架，支持从研究到生产的全流程",
    // "TensorFlow Lite": "轻量级解决方案，用于在移动和嵌入式设备上部署模型",
    // ...其他节点信息
  };
  const info = infoMap[nodeName] || `关于${nodeName}的详细信息。`;
  alert(`节点信息: ${nodeName}\n\n${info}`);
};

const toggleLayout = () => {
  layoutType.value = layoutType.value === "force" ? "circular" : "force";
  initChart();
};

const handleResize = () => {
  chart.value?.resize();
};

const handleClose = () => {
  if (chart.value) {
    chart.value.dispose();
    chart.value = null;
  }
  internalVisible.value = false;
  emit("update:visible", false);
};

/* ========= 生命周期和监听 ========= */
onMounted(() => {
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  chart.value?.dispose();
});

// 修改watch监听
watch(
  () => props.visible,
  (newVal) => {
    internalVisible.value = newVal;
    if (newVal && props.kbId) {
      nextTick(() => {
        fetchGraphData();
      });
    }
  }
);
watch(internalVisible, (newVal) => {
  if (!newVal && chart.value) {
    chart.value.dispose();
    chart.value = null;
  }
});
</script>

<style scoped>
body {
  margin: 0;
  padding: 0;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(to bottom, #f7f9fc, #eef2f7);
  color: #333;
  min-height: 100vh;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
/* header {
  text-align: center;
  padding: 20px 0;
  margin-bottom: 30px;
  border-bottom: 2px solid rgba(0, 0, 0, 0.05);
}
h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  color: #2c3e50;
} */
/* 新增头部样式 */
.header {
  text-align: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

/* 修改操作栏样式 */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 16px;
}

.kb-name {
  font-weight: bold;
  font-size: 16px;
  color: #1890ff;
  margin-right: 16px;
}

.action-bar button {
  margin-left: auto; /* 让按钮靠右 */
}

.subtitle {
  font-size: 1.2rem;
  color: #555;
  max-width: 800px;
  margin: 0 auto;
  line-height: 1.6;
}
.graph-container {
  background: #fff;
  border-radius: 15px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  height: 700px;
  margin-bottom: 30px;
  border: 1px solid #eee;
}

.controls {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 25px;
}
button {
  background: linear-gradient(to right, #9ce3ff, #3ac1ff);
  color: white;
  border: none;
  padding: 12px 25px;
  border-radius: 30px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}
button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}
.info-panel {
  background: #fff;
  border-radius: 15px;
  padding: 25px;
  margin-top: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #eee;
}
.info-panel h2 {
  margin-top: 0;
  color: #4a00e0;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}
.info-content {
  line-height: 1.7;
  color: #555;
}
.node-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 10px;
  margin-top: 15px;
  border-left: 4px solid #4a00e0;
}
.node-info h3 {
  margin-top: 0;
  color: #2c3e50;
}
footer {
  text-align: center;
  padding: 30px 0;
  margin-top: 40px;
  border-top: 1px solid #eee;
  font-size: 0.9rem;
  color: #777;
}
@media (max-width: 768px) {
  .graph-container {
    height: 500px;
  }
  .controls {
    flex-direction: column;
    align-items: center;
  }
  button {
    width: 100%;
    max-width: 300px;
  }
  h1 {
    font-size: 2rem;
  }
}
/* 新增加载容器样式 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 700px;
  background: #fff;
  border-radius: 15px;
}
</style>
