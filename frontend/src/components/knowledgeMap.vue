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
          <span>核心框架</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #c71969"></div>
          <span>模型组件</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #19c7a9"></div>
          <span>开发工具</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #ff6b6b"></div>
          <span>应用场景</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #f9c74f"></div>
          <span>数据处理</span>
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
    // 核心框架
    {
      id: "TensorFlow",
      name: "TensorFlow",
      symbolSize: 60,
      itemStyle: { color: "#4f19c7" },
    },
    {
      id: "TFLite",
      name: "TensorFlow Lite",
      symbolSize: 50,
      itemStyle: { color: "#4f19c7" },
    },
    {
      id: "TFjs",
      name: "TensorFlow.js",
      symbolSize: 50,
      itemStyle: { color: "#4f19c7" },
    },

    // 模型组件
    {
      id: "MobileNet",
      name: "MobileNet",
      symbolSize: 40,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "CNN",
      name: "卷积神经网络",
      symbolSize: 35,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "RNN",
      name: "循环神经网络",
      symbolSize: 35,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "PoseNet",
      name: "PoseNet",
      symbolSize: 35,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "Sequential",
      name: "Sequential模型",
      symbolSize: 35,
      itemStyle: { color: "#c71969" },
    },
    {
      id: "Functional",
      name: "Functional模型",
      symbolSize: 35,
      itemStyle: { color: "#c71969" },
    },

    // 开发工具
    {
      id: "AndroidStudio",
      name: "Android Studio",
      symbolSize: 45,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "Nodejs",
      name: "Node.js",
      symbolSize: 40,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "TensorBoard",
      name: "TensorBoard",
      symbolSize: 35,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "FlatBuffers",
      name: "FlatBuffers",
      symbolSize: 35,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "Converter",
      name: "模型转换器",
      symbolSize: 35,
      itemStyle: { color: "#19c7a9" },
    },
    {
      id: "Interpreter",
      name: "解释器",
      symbolSize: 35,
      itemStyle: { color: "#19c7a9" },
    },

    // 应用场景
    {
      id: "ImageRecognition",
      name: "图像识别",
      symbolSize: 45,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "ObjectDetection",
      name: "物体检测",
      symbolSize: 40,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "PoseEstimation",
      name: "姿态估计",
      symbolSize: 40,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "AutoML",
      name: "AutoML",
      symbolSize: 35,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "Embedded",
      name: "嵌入式设备",
      symbolSize: 40,
      itemStyle: { color: "#ff6b6b" },
    },
    {
      id: "BrowserML",
      name: "浏览器机器学习",
      symbolSize: 40,
      itemStyle: { color: "#ff6b6b" },
    },

    // 数据处理
    {
      id: "TFHub",
      name: "TensorFlow Hub",
      symbolSize: 40,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "Dataset",
      name: "数据集",
      symbolSize: 35,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "Preprocessing",
      name: "数据预处理",
      symbolSize: 35,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "Augmentation",
      name: "数据增强",
      symbolSize: 35,
      itemStyle: { color: "#f9c74f" },
    },
    {
      id: "Quantization",
      name: "量化",
      symbolSize: 35,
      itemStyle: { color: "#f9c74f" },
    },
  ],
  links: [
    // TensorFlow核心连接
    { source: "TensorFlow", target: "TFLite", label: "移动端部署" },
    { source: "TensorFlow", target: "TFjs", label: "Web部署" },
    { source: "TensorFlow", target: "TFHub", label: "模型仓库" },

    // TFLite相关
    { source: "TFLite", target: "MobileNet", label: "支持模型" },
    { source: "TFLite", target: "Converter", label: "包含" },
    { source: "TFLite", target: "Interpreter", label: "包含" },
    { source: "TFLite", target: "FlatBuffers", label: "格式" },
    { source: "TFLite", target: "ImageRecognition", label: "应用" },
    { source: "TFLite", target: "Embedded", label: "运行环境" },
    { source: "TFLite", target: "AndroidStudio", label: "开发工具" },
    { source: "TFLite", target: "Quantization", label: "优化技术" },

    // TF.js相关
    { source: "TFjs", target: "BrowserML", label: "运行环境" },
    { source: "TFjs", target: "Nodejs", label: "运行环境" },
    { source: "TFjs", target: "Sequential", label: "支持模型" },
    { source: "TFjs", target: "Functional", label: "支持模型" },
    { source: "TFjs", target: "PoseEstimation", label: "应用" },
    { source: "TFjs", target: "ObjectDetection", label: "应用" },
    { source: "TFjs", target: "Preprocessing", label: "数据处理" },
    { source: "TFjs", target: "Dataset", label: "使用" },

    // 模型相关
    { source: "MobileNet", target: "CNN", label: "基于" },
    { source: "PoseNet", target: "CNN", label: "基于" },
    { source: "Sequential", target: "LayersAPI", label: "使用" },
    { source: "Functional", target: "LayersAPI", label: "使用" },

    // 应用场景
    {
      source: "ImageRecognition",
      target: "FlowerRecognition",
      label: "案例",
    },
    {
      source: "ObjectDetection",
      target: "PoseEstimation",
      label: "相关",
    },
    { source: "Embedded", target: "RaspberryPi", label: "平台" },
    { source: "BrowserML", target: "WebApp", label: "实现" },

    // 数据处理
    { source: "Dataset", target: "MNIST", label: "示例" },
    { source: "Dataset", target: "CIFAR", label: "示例" },
    { source: "Preprocessing", target: "Augmentation", label: "包含" },
    {
      source: "Quantization",
      target: "ModelOptimization",
      label: "优化",
    },
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
    TensorFlow: "谷歌开源的深度学习框架，支持从研究到生产的全流程",
    "TensorFlow Lite": "轻量级解决方案，用于在移动和嵌入式设备上部署模型",
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
