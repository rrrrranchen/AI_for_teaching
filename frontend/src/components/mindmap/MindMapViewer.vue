<template>
  <div class="mind-map-container">
    <!-- 添加导出按钮 -->
    <button v-if="editable" class="export-btn" @click="exportToXMind">
      导出XMind
    </button>
    <div ref="mindMapContainerRef" class="mind-map"></div>

    <!-- 添加小地图容器 -->
    <div
      class="mini-map-container"
      @mousedown="onMiniMapMousedown"
      @mousemove="onMiniMapMousemove"
    >
      <div
        class="mini-map-svg-container"
        ref="miniMapContainer"
        :style="{
          transform: `scale(${miniMapBoxScale})`,
          left: miniMapBoxLeft + 'px',
          top: miniMapBoxTop + 'px',
        }"
      ></div>
      <div
        class="mini-map-view-box"
        :style="viewBoxStyle"
        :class="{ 'with-transition': withTransition }"
        @mousedown.stop="onViewBoxMousedown"
        @mousemove="onViewBoxMousemove"
      ></div>
    </div>

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
const miniMapContainer = ref(null); // 小地图容器引用
let mindMap = null;
const showContextMenu = ref(false);
const menuPosition = ref({ x: 0, y: 0 });
let currentNode = null;

// 小地图相关状态
const containerWidth = 200; // 小地图宽度
const containerHeight = 120; // 小地图高度
const viewBoxStyle = ref({});
const withTransition = ref(true);
const miniMapBoxScale = ref(1);
const miniMapBoxLeft = ref(0);
const miniMapBoxTop = ref(0);

// 更新小地图
const updateMiniMap = () => {
  if (!mindMap || !mindMap.miniMap || !miniMapContainer.value) return;

  // 计算小地图数据
  let data = mindMap.miniMap.calculationMiniMap(
    containerWidth,
    containerHeight
  );
  // 渲染到小地图
  miniMapContainer.value.innerHTML = data.svgHTML;
  viewBoxStyle.value = data.viewBoxStyle;
  miniMapBoxScale.value = data.miniMapBoxScale;
  miniMapBoxLeft.value = data.miniMapBoxLeft;
  miniMapBoxTop.value = data.miniMapBoxTop;
};

// 小地图鼠标事件
const onMiniMapMousedown = (e) => {
  if (mindMap && mindMap.miniMap) {
    withTransition.value = false;
    mindMap.miniMap.onMousedown(e);
  }
};

const onMiniMapMousemove = (e) => {
  if (mindMap && mindMap.miniMap) {
    mindMap.miniMap.onMousemove(e);
  }
};

const onMiniMapMouseup = (e) => {
  if (mindMap && mindMap.miniMap) {
    withTransition.value = true;
    mindMap.miniMap.onMouseup(e);
  }
};

// 视口框的鼠标事件
const onViewBoxMousedown = (e) => {
  if (mindMap && mindMap.miniMap) {
    mindMap.miniMap.onViewBoxMousedown(e);
  }
};

const onViewBoxMousemove = (e) => {
  if (mindMap && mindMap.miniMap) {
    mindMap.miniMap.onViewBoxMousemove(e);
  }
};

// 视口框的位置大小改变事件
const onViewBoxPositionChange = ({ left, right, top, bottom }) => {
  withTransition.value = false;
  viewBoxStyle.value.left = left;
  viewBoxStyle.value.right = right;
  viewBoxStyle.value.top = top;
  viewBoxStyle.value.bottom = bottom;
};

// 精简数据，只保留必要字段
const simplifyData = (data) => {
  if (!data) return null;

  const simplifyNode = (node) => {
    if (!node || !node.data) return null;

    const simplifiedData = {
      text: node.data.text || "",
      note: node.data.note || "",
      fillColor: node.data.color || "#ffffff",
    };

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
        type: "mindMap",
        options: {
          hgap: 60,
          vgap: 20,
          getLayoutRootNode: () => {
            return {
              x: 0,
              y: 0,
            };
          },
        },
      },
      themeConfig: {
        backgroundColor: "#edf6fbcc",
      },
    });

    // 添加事件监听
    mindMap.on("node_click", async (node) => {
      console.log("节点被点击，节点数据:", node.nodeData);
      if (node.nodeData.data?.id) {
        try {
          emit("node-click", {
            nodeId: node.nodeData.data.id,
            nodeText: node.nodeData.data.text,
            loading: true,
          });

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

    mindMap.on("node_contextmenu", (e, node) => {
      if (e.which === 3 && props.editable) {
        menuPosition.value.x = e.clientX + 10;
        menuPosition.value.y = e.clientY + 10;
        showContextMenu.value = true;
        currentNode = node;
      }
    });

    mindMap.on("draw_click", () => {
      showContextMenu.value = false;
    });

    // 监听数据变化
    mindMap.on("data_change", () => {
      const simplifiedData = getSimplifiedMindMapData();
      emit("update", simplifiedData);
      updateMiniMap(); // 数据变化时更新小地图
    });

    // 添加小地图相关事件监听
    mindMap.on("view_data_change", updateMiniMap);
    mindMap.on("node_tree_render_end", updateMiniMap);
    mindMap.on("mini_map_view_box_position_change", onViewBoxPositionChange);
    window.addEventListener("mouseup", onMiniMapMouseup);

    // 初始化小地图
    updateMiniMap();
  } catch (error) {
    console.error("初始化思维导图失败:", error);
  }
};

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

// 添加导出方法
const exportToXMind = () => {
  if (mindMap) {
    try {
      const rootText = mindMap.getData()?.data?.text || "思维导图";
      const fileName = `${rootText}`;
      mindMap.export("xmind", true, fileName);
    } catch (error) {
      console.error("导出XMind失败:", error);
      alert("导出失败，请确保已安装所需插件");
    }
  }
};
</script>

<style scoped>
.mind-map-container {
  position: relative;
  width: 100%;
  height: 100%;
}

/* 导出按钮样式 */
.export-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: background-color 0.3s;
}

.export-btn:hover {
  background-color: #359c6c;
}

.mind-map {
  width: 100%;
  height: 100vh;
}

/* 小地图容器样式 */
.mini-map-container {
  position: absolute;
  left: 20px;
  top: 20px;
  width: 200px;
  height: 120px;
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #ccc;
  border-radius: 4px;
  z-index: 50;
  overflow: hidden;
}

.mini-map-svg-container {
  position: absolute;
  transform-origin: left top;
}

.mini-map-view-box {
  position: absolute;
  border: 2px solid rgb(238, 69, 69);
  transition: all 0.3s;
}

.mini-map-view-box.with-transition {
  transition: all 0.3s;
}

.context-menu {
  position: fixed;
  border: 1px solid #ccc;
  box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  padding: 10px;
  border-radius: 4px;
  background-color: #f0f0f0;
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
