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
import {
  ref,
  onMounted,
  watch,
  defineProps,
  defineEmits,
  defineExpose,
} from "vue";
import mindmapApi from "@/api/mindmap";
import MindMap from "simple-mind-map";
import MiniMap from "simple-mind-map/src/plugins/MiniMap.js";
import Watermark from "simple-mind-map/src/plugins/Watermark.js";
import KeyboardNavigation from "simple-mind-map/src/plugins/KeyboardNavigation.js";
import ExportPDF from "simple-mind-map/src/plugins/ExportPDF.js";
import ExportXMind from "simple-mind-map/src/plugins/ExportXMind.js";
import Export from "simple-mind-map/src/plugins/Export.js";
import Drag from "simple-mind-map/src/plugins/Drag.js";
import Select from "simple-mind-map/src/plugins/Select.js";
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

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  editable: {
    type: Boolean,
    default: true,
  },
});

console.log("传入数据", props.data);
const emit = defineEmits(["update"]);

const mindMapContainerRef = ref(null);
let mindMap = null;
const showContextMenu = ref(false);
const menuPosition = ref({ x: 0, y: 0 });
let currentNode = null;

// 精简数据，只保留必要字段
// 精简数据，只保留必要的字段（如果有id则保留，没有则不添加）
const simplifyData = (data) => {
  if (!data) return null;

  const simplifyNode = (node) => {
    if (!node || !node.data) return null;

    // 创建精简后的数据对象
    const simplifiedData = {
      text: node.data.text || "",
      note: node.data.note || "",
      fillColor: node.data.color || "#ffffff",
    };

    // 只有原数据有id时才保留
    if (node.data.id !== undefined) {
      simplifiedData.id = node.data.id;
    }

    const simplified = {
      data: simplifiedData,
      children: [],
    };

    if (node.children && Array.isArray(node.children)) {
      simplified.children = node.children
        .map((child) => simplifyNode(child))
        .filter(Boolean);
    }

    return simplified;
  };

  return simplifyNode(JSON.parse(JSON.stringify(data)));
};
// 获取精简后的思维导图数据
const getSimplifiedMindMapData = () => {
  if (!mindMap) return null;
  const fullData = mindMap.getData();
  return simplifyData(fullData);
};

// 初始化思维导图
const initMindMap = () => {
  if (!mindMapContainerRef.value) return;

  if (mindMap) {
    mindMap.destroy();
    mindMap = null;
  }

  try {
    mindMap = new MindMap({
      el: mindMapContainerRef.value,
      data: props.data[0],
      editable: props.editable,
      layout: {
        // 树形布局，让整体更居中
        type: "mindMap",
        options: {
          // 节点水平间距
          hgap: 60,
          // 节点垂直间距
          vgap: 20,
          // 控制整体位置
          getLayoutRootNode: () => {
            return {
              x: 0, // 初始x位置设为0，让整体居中
              y: 0, // 初始y位置设为0
            };
          },
        },
      },
      themeConfig: {
        backgroundColor: "#edf6fbcc",
      },
    });
    // 添加节点点击事件
    mindMap.on("node_click", async (node) => {
      console.log("节点被点击，节点数据:", node.nodeData); // 调试输出
      if (node.nodeData.data?.id) {
        try {
          emit("node-click", {
            nodeId: node.nodeData.data.id,
            nodeText: node.nodeData.data.text,
            loading: true,
          });

          // 调用第一个接口获取知识点问题
          const response = await mindmapApi.getKnowledgeQuestions(
            node.nodeData.data.id
          );

          emit("node-click", {
            nodeId: node.nodeData.data.id,
            nodeText: node.nodeData.data.text,
            data: response.leaf_questions,
            loading: false,
          });
        } catch (error) {
          emit("node-click", {
            nodeId: node.nodeData.data.id,
            error: true,
            message: "获取数据失败",
            loading: false,
          });
        }
      }
    });

    // 节点右键事件
    mindMap.on("node_contextmenu", (e, node) => {
      if (e.which === 3 && props.editable) {
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

    // 监听数据变化
    mindMap.on("data_change", () => {
      const simplifiedData = getSimplifiedMindMapData();
      emit("update", simplifiedData);
    });
  } catch (error) {
    console.error("初始化思维导图失败:", error);
  }
};

// // 获取当前思维导图数据
// const getMindMapData = () => {
//   return mindMap ? mindMap.getData() : null;
// };

// 添加子节点
const addChildNode = () => {
  if (mindMap && currentNode && props.editable) {
    mindMap.execCommand("INSERT_CHILD_NODE");
    showContextMenu.value = false;
  }
};

// 添加同级节点
const addSameNode = () => {
  if (mindMap && currentNode && props.editable) {
    mindMap.execCommand("INSERT_NODE");
    showContextMenu.value = false;
  }
};

// 删除节点
const removeNode = () => {
  if (mindMap && currentNode && props.editable) {
    mindMap.execCommand("REMOVE_NODE");
    showContextMenu.value = false;
  }
};

// 复制节点
const copyNode = () => {
  if (mindMap && currentNode && props.editable) {
    mindMap.renderer.copy();
    showContextMenu.value = false;
  }
};

// 粘贴节点
const pasteNode = () => {
  if (mindMap && currentNode && props.editable) {
    mindMap.renderer.paste();
    showContextMenu.value = false;
  }
};

onMounted(() => {
  initMindMap();
});

watch(
  () => props.data,
  (newData) => {
    if (mindMap) {
      try {
        mindMap.setData(newData);
      } catch (error) {
        console.error("更新思维导图数据失败:", error);
      }
    }
  },
  { deep: true }
);

// 暴露精简数据获取方法
defineExpose({
  getMindMapData: getSimplifiedMindMapData,
});

// const mindmaptest = {
//   data: {
//     id: 1,
//     text: "因特网和组成技术知识点",
//     note: "",
//     backgroundColor: "#ffffff",
//   },
//   children: [
//     {
//       data: {
//         id: 2,
//         text: "网络基本概念",
//         note: "",
//         backgroundColor: "#ffffff",
//       },
//       children: [
//         {
//           data: {
//             id: 3,
//             text: "因特网的定义与特点",
//             note: "因特网是全球性的、开放的计算机网络互联系统，基于TCP/IP协议族实现数据通信。",
//             fillColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 4,
//             text: "主机的作用",
//             note: "主机是网络中的终端设备，负责数据的生成、发送和接收。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 5,
//             text: "交换设备的作用",
//             note: "交换设备负责在网络中转发数据，实现不同主机之间的通信。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 6,
//             text: "链路的作用",
//             note: "链路是连接网络设备的物理或逻辑通道，负责数据的传输。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//       ],
//     },
//     {
//       data: {
//         id: 7,
//         text: "网络边缘",
//         note: "",
//         backgroundColor: "#ffffff",
//       },
//       children: [
//         {
//           data: {
//             id: 8,
//             text: "端系统的功能",
//             note: "端系统是网络的终端设备，负责数据的生成、处理和接收。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 9,
//             text: "端系统的类型",
//             note: "包括个人计算机、服务器、移动设备等。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 10,
//             text: "接入网的技术分类",
//             note: "包括DSL、光纤、无线接入等。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 11,
//             text: "物理媒体的种类",
//             note: "包括双绞线、同轴电缆、光纤、无线电波等。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 12,
//             text: "物理媒体的特性",
//             note: "包括传输速率、传输距离、抗干扰能力等。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//       ],
//     },
//     {
//       data: {
//         id: 13,
//         text: "网络核心",
//         note: "",
//         backgroundColor: "#39ffff",
//       },
//       children: [
//         {
//           data: {
//             id: 14,
//             text: "电路交换原理",
//             note: "",
//             backgroundColor: "#48ffff",
//           },
//           children: [
//             {
//               data: {
//                 id: 15,
//                 text: "FDM(频分复用)",
//                 note: "**FDM**是将频带分割为多个子频带，每个子频带独立传输一路信号。",
//                 backgroundColor: "#7fffff",
//               },
//               children: [],
//             },
//             {
//               data: {
//                 id: 16,
//                 text: "TDM(时分复用)",
//                 note: "**TDM**是将时间分割为多个时隙，每个时隙传输一路信号。",
//                 backgroundColor: "#10ffff",
//               },
//               children: [],
//             },
//           ],
//         },
//         {
//           data: {
//             id: 17,
//             text: "分组交换原理",
//             note: "",
//             backgroundColor: "#00ffff",
//           },
//           children: [
//             {
//               data: {
//                 id: 18,
//                 text: "数据报网络",
//                 note: "数据报网络中，每个分组独立路由，不保证顺序到达。",
//                 backgroundColor: "#00ffff",
//               },
//               children: [],
//             },
//             {
//               data: {
//                 id: 19,
//                 text: "虚电路",
//                 note: "虚电路网络中，通信前建立逻辑连接，分组按顺序传输。",
//                 backgroundColor: "#ffffff",
//               },
//               children: [],
//             },
//           ],
//         },
//         {
//           data: {
//             id: 20,
//             text: "交换技术比较",
//             note: "电路交换建立专用路径，适合实时通信；分组交换共享路径，适合突发数据。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//       ],
//     },
//     {
//       data: {
//         id: 21,
//         text: "网络的网络",
//         note: "",
//         backgroundColor: "#ffffff",
//       },
//       children: [
//         {
//           data: {
//             id: 22,
//             text: "层级结构设计",
//             note: "网络采用分层设计，每层负责特定功能，简化网络管理和协议设计。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//         {
//           data: {
//             id: 23,
//             text: "接入层级关系",
//             note: "接入网连接端系统和核心网，核心网连接不同接入网，形成网络的网络。",
//             backgroundColor: "#ffffff",
//           },
//           children: [],
//         },
//       ],
//     },
//   ],
// };
</script>

<style scoped>
.mind-map-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.mind-map {
  width: 100%;
  height: 80vh;
}

.context-menu {
  position: fixed;
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
