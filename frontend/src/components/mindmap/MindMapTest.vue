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
  .usePlugin(Formula)
  .usePlugin(RichText);

const mindMapContainerRef = ref(null);
let mindMap = null;
const showContextMenu = ref(false);
const menuPosition = ref({ x: 0, y: 0 });
let currentNode = null;

// 示例数据
const mindData = {
  data: {
    id: 24,
    text: "TCP协议技术知识点",
    note: "",
    backgroundColor: "#ffffff",
  },
  children: [
    {
      data: {
        id: 25,
        text: "基本概念",
        note: "",
        backgroundColor: "#ffffff",
      },
      children: [
        {
          data: {
            id: 26,
            text: "OSI模型位置",
            note: "传输层",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
        {
          data: {
            id: 27,
            text: "全称",
            note: "传输控制协议(Transmission Control Protocol)",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
      ],
    },
    {
      data: {
        id: 28,
        text: "核心机制",
        note: "",
        backgroundColor: "#ffffff",
      },
      children: [
        {
          data: {
            id: 29,
            text: "连接管理",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [
            {
              data: {
                id: 30,
                text: "三次握手过程",
                note: "- `SYN` → `SYN+ACK` → `ACK`\n- 序列号随机生成\n- 窗口大小字段作用",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
            {
              data: {
                id: 31,
                text: "四次挥手过程",
                note: "",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
          ],
        },
        {
          data: {
            id: 32,
            text: "可靠传输",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [
            {
              data: {
                id: 33,
                text: "确认应答机制(ACK)",
                note: "",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
            {
              data: {
                id: 34,
                text: "超时重传机制",
                note: "",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
            {
              data: {
                id: 35,
                text: "滑动窗口机制",
                note: "- 窗口滑动过程\n- 窗口大小对传输速率的影响",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
          ],
        },
        {
          data: {
            id: 36,
            text: "流量控制",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [
            {
              data: {
                id: 37,
                text: "水龙头调节水流类比",
                note: "",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
            {
              data: {
                id: 38,
                text: "窗口大小字段调节",
                note: "",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
          ],
        },
      ],
    },
    {
      data: {
        id: 39,
        text: "协议特点",
        note: "",
        backgroundColor: "#ffffff",
      },
      children: [
        {
          data: {
            id: 40,
            text: "面向连接",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
        {
          data: {
            id: 41,
            text: "可靠交付",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
        {
          data: {
            id: 42,
            text: "全双工通信",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
        {
          data: {
            id: 43,
            text: "字节流服务",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
      ],
    },
    {
      data: {
        id: 44,
        text: "TCP与UDP对比",
        note: "",
        backgroundColor: "#ffffff",
      },
      children: [
        {
          data: {
            id: 45,
            text: "特性",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [
            {
              data: {
                id: 46,
                text: "连接性",
                note: "| TCP | UDP |\n|---|---|\n| 面向连接 | 无连接 |",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
            {
              data: {
                id: 47,
                text: "可靠性",
                note: "| TCP | UDP |\n|---|---|\n| 可靠传输 | 不可靠传输 |",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
            {
              data: {
                id: 48,
                text: "传输方式",
                note: "| TCP | UDP |\n|---|---|\n| 字节流 | 数据报 |",
                backgroundColor: "#ffffff",
              },
              children: [],
            },
          ],
        },
      ],
    },
    {
      data: {
        id: 49,
        text: "关键技术参数",
        note: "",
        backgroundColor: "#ffffff",
      },
      children: [
        {
          data: {
            id: 50,
            text: "序列号(seq)",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
        {
          data: {
            id: 51,
            text: "确认号(ack)",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
        {
          data: {
            id: 52,
            text: "窗口大小(window size)",
            note: "",
            backgroundColor: "#ffffff",
          },
          children: [],
        },
        {
          data: {
            id: 53,
            text: "控制标志位(SYN/ACK等)",
            note: "",
            backgroundColor: "#ffffff",
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
