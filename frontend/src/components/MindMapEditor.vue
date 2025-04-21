<template>
  <div class="mind-map-container">
    <div ref="mindMapContainerRef" class="mind-map"></div>
    <div
      v-if="showContextMenu"
      class="context-menu"
      :style="{ top: menuPosition.y + 'px', left: menuPosition.x + 'px' }"
    >
      <ul>
        <li @click="addChildNode">添加子节点</li>
        <li @click="addSameNode">添加同级节点</li>
        <li @click="removeNode">删除节点</li>
        <li @click="copyNode">复制节点</li>
        <li @click="pasteNode">粘贴节点</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import MindMap from "simple-mind-map";
import MiniMap from "simple-mind-map/src/plugins/MiniMap.js";
import Watermark from "simple-mind-map/src/plugins/Watermark.js";
import KeyboardNavigation from "simple-mind-map/src/plugins/KeyboardNavigation.js";
import ExportPDF from "simple-mind-map/src/plugins/ExportPDF.js";
import ExportXMind from "simple-mind-map/src/plugins/ExportXMind.js";
import Export from "simple-mind-map/src/plugins/Export.js";
import Drag from "simple-mind-map/src/plugins/Drag.js";
import Select from "simple-mind-map/src/plugins/Select.js";
import RichText from "simple-mind-map/src/plugins/RichText.js";
import AssociativeLine from "simple-mind-map/src/plugins/AssociativeLine.js";
import TouchEvent from "simple-mind-map/src/plugins/TouchEvent.js";
import NodeImgAdjust from "simple-mind-map/src/plugins/NodeImgAdjust.js";
import SearchPlugin from "simple-mind-map/src/plugins/Search.js";
import Painter from "simple-mind-map/src/plugins/Painter.js";
import Formula from "simple-mind-map/src/plugins/Formula.js";

// 注册插件
MindMap.usePlugin(MiniMap)
  .usePlugin(Watermark)
  .usePlugin(Drag)
  .usePlugin(KeyboardNavigation)
  .usePlugin(ExportPDF)
  .usePlugin(ExportXMind)
  .usePlugin(Export)
  .usePlugin(Select)
  .usePlugin(AssociativeLine)
  .usePlugin(NodeImgAdjust)
  .usePlugin(TouchEvent)
  .usePlugin(SearchPlugin)
  .usePlugin(Painter)
  .usePlugin(Formula);

const mindMapContainerRef = ref(null);
let mindMap = null;
const showContextMenu = ref(false);
const menuPosition = ref({ x: 0, y: 0 });
let currentNode = null;

// 示例数据
const mindData = {
  data: {
    id: 92,
    text: "TCP技术知识点",
    note: "",
  },
  children: [
    {
      data: {
        id: 93,
        text: "TCP协议基础",
        note: "",
      },
      children: [
        {
          data: {
            id: 94,
            text: "TCP定义与特性",
            note: "- **面向连接的传输层协议**\n- **可靠性传输机制**\n- **流量控制功能**\n- **拥塞控制功能**",
          },
          children: [],
        },
        {
          data: {
            id: 95,
            text: "TCP与UDP对比",
            note: "- **可靠性（TCP） vs 高效率（UDP）**\n- **面向连接（TCP） vs 无连接（UDP）**\n- **数据有序性（TCP） vs 无序性（UDP）**",
          },
          children: [],
        },
        {
          data: {
            id: 96,
            text: "协议栈位置",
            note: "- **传输层协议**\n- **基于IP协议工作**",
          },
          children: [],
        },
      ],
    },
    {
      data: {
        id: 97,
        text: "TCP连接管理",
        note: "",
      },
      children: [
        {
          data: {
            id: 98,
            text: "三次握手建立连接",
            note: "- **报文交换序列：SYN → SYN-ACK → ACK**\n- **序列号（Sequence Number）作用：标识数据字节流**\n- **确认号（Acknowledgment Number）作用：确认接收到的数据**\n- **连接状态：**\n  - 半连接状态（SYN_RECEIVED）\n  - 全连接状态（ESTABLISHED）",
          },
          children: [],
        },
        {
          data: {
            id: 99,
            text: "四次挥手断开连接",
            note: "- **报文交换序列：FIN → ACK → FIN → ACK**\n- **TIME_WAIT状态：**\n  - 持续时间：2MSL（Maximum Segment Lifetime）\n  - 作用：确保最后一个ACK到达对端\n- **异常断开处理机制**",
          },
          children: [],
        },
      ],
    },
    {
      data: {
        id: 100,
        text: "TCP数据传输机制",
        note: "",
      },
      children: [
        {
          data: {
            id: 101,
            text: "可靠性保证机制",
            note: "- **确认应答（ACK）机制**\n- **超时重传机制**\n- **数据排序功能**",
          },
          children: [],
        },
        {
          data: {
            id: 102,
            text: "流量控制",
            note: "- **滑动窗口协议原理**\n- **窗口类型：**\n  - 接收窗口（rwnd）\n  - 发送窗口（cwnd）",
          },
          children: [],
        },
        {
          data: {
            id: 103,
            text: "拥塞控制",
            note: "- **慢启动算法（Slow Start）**\n- **拥塞避免算法（Congestion Avoidance）**\n- **快速重传（Fast Retransmit）**\n- **快速恢复（Fast Recovery）**",
          },
          children: [],
        },
      ],
    },
    {
      data: {
        id: 104,
        text: "TCP报文关键字段",
        note: "- **序列号（32位）**\n- **确认号（32位）**\n- **窗口大小字段（16位）**\n- **控制标志位：**\n  - SYN\n  - ACK\n  - FIN\n  - RST",
      },
      children: [],
    },
    {
      data: {
        id: 105,
        text: "性能优化相关",
        note: "",
      },
      children: [
        {
          data: {
            id: 106,
            text: "窗口大小调整策略",
            note: "",
          },
          children: [],
        },
        {
          data: {
            id: 107,
            text: "拥塞控制算法选择",
            note: "- **TCP Tahoe**\n- **TCP Reno**",
          },
          children: [],
        },
        {
          data: {
            id: 108,
            text: "MSL（Maximum Segment Lifetime）参数配置",
            note: "",
          },
          children: [],
        },
      ],
    },
    {
      data: {
        id: 109,
        text: "诊断工具与技术",
        note: "",
      },
      children: [
        {
          data: {
            id: 110,
            text: "Wireshark抓包分析",
            note: "- **报文类型识别**\n- **状态转换跟踪**",
          },
          children: [],
        },
        {
          data: {
            id: 111,
            text: "常见问题诊断",
            note: "- **连接超时分析**\n- **传输速率下降分析**",
          },
          children: [],
        },
      ],
    },
  ],
};

// 初始化思维导图
onMounted(() => {
  mindMap = new MindMap({
    el: mindMapContainerRef.value,
    data: mindData,
    editable: true, // 启用编辑模式
  });

  // 节点右键事件
  mindMap.on("node_contextmenu", (e, node) => {
    if (e.which === 3) {
      menuPosition.value.x = e.clientX + 10;
      menuPosition.value.y = e.clientY + 10;
      showContextMenu.value = true;
      currentNode = node;
    }
  });

  // 点击空白处关闭菜单
  mindMap.on("draw_click", () => {
    showContextMenu.value = false;
  });
});

// 添加子节点
const addChildNode = () => {
  if (mindMap && currentNode) {
    mindMap.execCommand("INSERT_CHILD_NODE");
    showContextMenu.value = false;
  }
};

// 添加同级节点
const addSameNode = () => {
  if (mindMap && currentNode) {
    mindMap.execCommand("INSERT_NODE");
    showContextMenu.value = false;
  }
};

// 删除节点
const removeNode = () => {
  if (mindMap && currentNode) {
    mindMap.execCommand("REMOVE_NODE");
    showContextMenu.value = false;
  }
};

// 复制节点
const copyNode = () => {
  if (mindMap && currentNode) {
    mindMap.renderer.copy();
    showContextMenu.value = false;
  }
};

// 粘贴节点
const pasteNode = () => {
  if (mindMap && currentNode) {
    mindMap.renderer.paste();
    showContextMenu.value = false;
  }
};
</script>

<style scoped>
.mind-map-container {
  position: relative;
}

.mind-map {
  width: 100%;
  height: calc(100vh - 190px);
}

.context-menu {
  position: fixed;
  background-color: white;
  border: 1px solid #ccc;
  box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  padding: 10px;
  border-radius: 4px;
}

.context-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.context-menu li {
  padding: 8px 12px;
  cursor: pointer;
}

.context-menu li:hover {
  background-color: #f0f0f0;
}
</style>
