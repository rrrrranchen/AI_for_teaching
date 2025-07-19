<template>
  <a-modal
    :visible="internalVisible"
    :width="1350"
    :footer="null"
    :bodyStyle="{ padding: '0' }"
    :style="{ top: '20px' }"
    @cancel="handleClose"
    @ok="handleClose"
  >
    <div class="container">
      <div class="legend">
        <div class="legend-item">
          <div class="legend-color" style="background-color: #4f19c7"></div>
          <span>核心语言</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #c71969"></div>
          <span>标准库</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #19c7a9"></div>
          <span>流行框架</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #ff6b6b"></div>
          <span>应用领域</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #f9c74f"></div>
          <span>开发工具</span>
        </div>
        <button @click="toggleLayout">
          {{ layoutType === "force" ? "切换环形布局" : "切换力导向布局" }}
        </button>
      </div>

      <div class="graph-container" ref="chartDom"></div>
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

const emit = defineEmits(["update:visible"]);

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
});

/* ========= 响应式数据 ========= */
const internalVisible = ref(props.visible);
const chart = ref(null); // echarts 实例
const chartDom = ref(null); // 容器 DOM
const layoutType = ref("force"); // 布局模式：force | circular

const graphData = reactive({
  nodes: [
    // 核心语言
    {
      id: "Python",
      name: "Python",
      symbolSize: 70,
      itemStyle: { color: "#4f19c7" },
    },
    {
      id: "Syntax",
      name: "语法特性",
      symbolSize: 50,
      itemStyle: { color: "#4f19c7" },
    },
    {
      id: "OOP",
      name: "面向对象",
      symbolSize: 50,
      itemStyle: { color: "#4f19c7" },
    },
    {
      id: "FP",
      name: "函数式编程",
      symbolSize: 45,
      itemStyle: { color: "#4f19c7" },
    },

    // 标准库
    {
      id: "os",
      name: "os模块",
      symbolSize: 40,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "sys",
      name: "sys模块",
      symbolSize: 40,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "re",
      name: "re模块",
      symbolSize: 40,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "collections",
      name: "collections",
      symbolSize: 40,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "itertools",
      name: "itertools",
      symbolSize: 40,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "datetime",
      name: "datetime",
      symbolSize: 40,
      itemStyle: { color: "#c71969" },
    },

    // 流行框架
    {
      id: "Django",
      name: "Django",
      symbolSize: 55,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "Flask",
      name: "Flask",
      symbolSize: 50,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "NumPy",
      name: "NumPy",
      symbolSize: 50,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "Pandas",
      name: "Pandas",
      symbolSize: 50,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "Matplotlib",
      name: "Matplotlib",
      symbolSize: 45,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "TensorFlow",
      name: "TensorFlow",
      symbolSize: 45,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "PyTorch",
      name: "PyTorch",
      symbolSize: 45,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "FastAPI",
      name: "FastAPI",
      symbolSize: 45,
      itemStyle: { color: "#19c7a9" },
    },

    // 应用领域
    {
      id: "WebDev",
      name: "Web开发",
      symbolSize: 50,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "DataScience",
      name: "数据科学",
      symbolSize: 50,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "AI",
      name: "人工智能",
      symbolSize: 50,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "Automation",
      name: "自动化脚本",
      symbolSize: 45,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "GameDev",
      name: "游戏开发",
      symbolSize: 45,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "DevOps",
      name: "DevOps",
      symbolSize: 45,
      itemStyle: { color: "#ff6b6b" },
    },

    // 开发工具
    {
      id: "PyCharm",
      name: "PyCharm",
      symbolSize: 45,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "VSCode",
      name: "VS Code",
      symbolSize: 45,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "Jupyter",
      name: "Jupyter",
      symbolSize: 45,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "pip",
      name: "pip",
      symbolSize: 40,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "conda",
      name: "conda",
      symbolSize: 40,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "virtualenv",
      name: "virtualenv",
      symbolSize: 40,
      itemStyle: { color: "#f9c74f" },
    },
  ],
  links: [
    // Python核心连接
    { source: "Python", target: "Syntax", label: "包含" },
    { source: "Python", target: "OOP", label: "支持" },
    { source: "Python", target: "FP", label: "支持" },
    { source: "Python", target: "os", label: "标准库" },
    { source: "Python", target: "sys", label: "标准库" },

    // 标准库连接
    { source: "os", target: "sys", label: "协同工作" },
    { source: "re", target: "collections", label: "数据处理" },
    { source: "itertools", target: "FP", label: "支持" },
    { source: "datetime", target: "os", label: "文件时间" },

    // 框架连接
    { source: "Django", target: "WebDev", label: "用于" },
    { source: "Flask", target: "WebDev", label: "用于" },
    { source: "FastAPI", target: "WebDev", label: "用于" },
    { source: "NumPy", target: "DataScience", label: "用于" },
    { source: "Pandas", target: "DataScience", label: "用于" },
    { source: "Matplotlib", target: "DataScience", label: "用于" },
    { source: "TensorFlow", target: "AI", label: "用于" },
    { source: "PyTorch", target: "AI", label: "用于" },
    { source: "NumPy", target: "Pandas", label: "基础" },
    { source: "NumPy", target: "TensorFlow", label: "基础" },

    // 应用领域连接
    { source: "WebDev", target: "Automation", label: "相关" },
    { source: "DataScience", target: "AI", label: "相关" },
    { source: "GameDev", target: "PyGame", label: "使用" },
    { source: "DevOps", target: "Automation", label: "使用" },

    // 开发工具连接
    { source: "PyCharm", target: "Python", label: "支持" },
    { source: "VSCode", target: "Python", label: "支持" },
    { source: "Jupyter", target: "DataScience", label: "用于" },
    { source: "pip", target: "Python", label: "包管理" },
    { source: "conda", target: "DataScience", label: "环境管理" },
    { source: "virtualenv", target: "WebDev", label: "环境隔离" },
  ],
  categories: [],
});

/* ========= 方法 ========= */
const initChart = () => {
  if (!chartDom.value) return;

  try {
    // 销毁旧实例
    if (chart.value) {
      chart.value.dispose();
    }

    chart.value = echarts.init(chartDom.value);

    const option = getChartOption();
    chart.value.setOption(option);

    // 添加事件监听
    chart.value.on("click", handleNodeClick);
  } catch (error) {
    console.error("图表初始化失败:", error);
  }
};

const getChartOption = () => {
  return {
    backgroundColor: "#ffffff",
    title: {
      text: "Python 知识图谱",
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
            <div>${param.data.category || "Python组件"}</div>`;
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
    Python: "高级编程语言，以简洁易读著称，支持多种编程范式",
    Django: "高级Python Web框架，鼓励快速开发和干净、实用的设计",
    Flask: "轻量级Web应用框架，易于扩展",
    NumPy: "Python科学计算的基础包，提供高性能多维数组对象",
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
  nextTick(initChart);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  chart.value?.dispose();
});

watch(
  () => props.visible,
  (newVal) => {
    internalVisible.value = newVal;
    if (newVal) {
      nextTick(initChart);
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
header {
  text-align: center;
  padding: 20px 0;
  margin-bottom: 30px;
  border-bottom: 2px solid rgba(0, 0, 0, 0.05);
}
h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  color: #2c3e50;
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
.legend {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 15px;
  margin: 20px 0;
}
.legend-item {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  background: #f8f9fa;
  border-radius: 20px;
  font-size: 14px;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}
.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  margin-right: 8px;
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
</style>
