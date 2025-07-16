<template>
  <div class="mind-map-questions-container">
    <!-- 思维导图展示区域 -->
    <div class="mind-map-wrapper">
      <MindMapMiniViewer
        v-if="mindMapData"
        ref="mindMapViewer"
        :data="mindMapData"
        :editable="false"
        @node-click="handleNodeClick"
      />
      <a-empty v-else description="暂无思维导图数据" />
    </div>

    <!-- 生成题目参数模态框 -->
    <a-modal
      v-model:visible="showGenerateModal"
      title="生成课后习题"
      width="600px"
      :confirm-loading="generating"
      @ok="handleGenerateQuestions"
      @cancel="closeModal"
    >
      <a-form :model="generateForm" layout="vertical">
        <a-form-item label="知识点名称">
          <a-input v-model:value="currentNodeText" disabled />
        </a-form-item>

        <a-form-item label="题目规格配置">
          <div class="specs-container">
            <div
              v-for="(spec, index) in generateForm.specs"
              :key="index"
              class="spec-item"
            >
              <a-space>
                <a-select
                  v-model:value="spec.type"
                  style="width: 120px"
                  placeholder="题目类型"
                >
                  <a-select-option value="choice">选择题</a-select-option>
                  <a-select-option value="fill">填空题</a-select-option>
                  <a-select-option value="short_answer">简答题</a-select-option>
                  <a-select-option value="practice">实践题</a-select-option>
                </a-select>

                <a-input-number
                  v-model:value="spec.count"
                  :min="1"
                  :max="10"
                  placeholder="数量"
                />

                <a-select
                  v-model:value="spec.difficulty"
                  style="width: 120px"
                  placeholder="难度(可选)"
                  allow-clear
                >
                  <a-select-option :value="1">1 - 简单</a-select-option>
                  <a-select-option :value="2">2 - 较易</a-select-option>
                  <a-select-option :value="3">3 - 中等</a-select-option>
                  <a-select-option :value="4">4 - 较难</a-select-option>
                  <a-select-option :value="5">5 - 困难</a-select-option>
                </a-select>

                <a-button
                  type="text"
                  danger
                  @click="removeSpec(index)"
                  :disabled="generateForm.specs.length <= 1"
                >
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-space>
            </div>

            <a-button type="dashed" @click="addSpec" class="add-spec-btn">
              <template #icon><PlusOutlined /></template>
              添加规格
            </a-button>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 生成结果展示模态框 -->
    <a-modal
      v-model:visible="showResultModal"
      title="生成结果"
      width="800px"
      :footer="null"
    >
      <div v-if="generatedQuestions">
        <a-alert
          :message="`已为知识点【${
            generatedQuestions?.data.knowledge_point?.name || '未知知识点'
          }】生成 ${generatedQuestions?.data.questions?.length} 道题目`"
          type="success"
          show-icon
          class="mb-4"
        />

        <a-tabs>
          <a-tab-pane key="questions" tab="题目列表">
            <a-list
              :data-source="generatedQuestions.data.questions"
              :grid="{ gutter: 16, column: 1 }"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-card
                    :title="`${getQuestionTypeName(item.type)} (难度: ${
                      item.difficulty
                    })`"
                  >
                    <div class="question-content">
                      <p><strong>题目:</strong> {{ item.content }}</p>
                      <p><strong>答案:</strong> {{ item.correct_answer }}</p>
                    </div>
                  </a-card>
                </a-list-item>
              </template>
            </a-list>
          </a-tab-pane>
          <a-tab-pane key="specs" tab="使用规格">
            <a-descriptions bordered :column="1">
              <a-descriptions-item
                v-for="(spec, index) in generatedQuestions.data.specs_used"
                :key="index"
                :label="`规格 ${index + 1}`"
              >
                <p>类型: {{ getQuestionTypeName(spec.type) }}</p>
                <p>数量: {{ spec.count }}</p>
                <p v-if="spec.difficulty">难度: {{ spec.difficulty }}</p>
              </a-descriptions-item>
            </a-descriptions>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineProps } from "vue";
import { message } from "ant-design-vue";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons-vue";
import MindMapMiniViewer from "./MindMapMiniViewer.vue";
import { questionApi } from "@/api/questions";
import type {
  QuestionSpec,
  GenerateNodeQuestionsResponse,
} from "@/api/questions";

import { getMindMap as apiGetMindMap } from "@/api/teachingdesign";

const props = defineProps({
  designId: {
    type: Number,
    required: true,
  },
});

// 思维导图数据
const mindMapData = ref<any>(null);
const mindMapViewer = ref<any>(null);

// 当前选中节点信息
const currentNodeId = ref<number | null>(null);
const currentNodeText = ref<string>("");

// 模态框状态
const showGenerateModal = ref(false);
const showResultModal = ref(false);
const generating = ref(false);

// 生成表单
const generateForm = ref({
  specs: [
    {
      type: "choice" as const,
      count: 1,
      difficulty: null as number | null,
    },
  ],
});

// 生成结果
const generatedQuestions = ref<GenerateNodeQuestionsResponse | null>(null);

// 获取思维导图数据
const fetchMindMap = async () => {
  try {
    // 这里假设有一个API可以获取教学设计对应的思维导图
    const response = await apiGetMindMap(props.designId);
    mindMapData.value = response.mindmap;
    console.log("mindMapData", mindMapData.value);

    // 模拟数据
    // mindMapData.value = {
    //   data: {
    //     text: "因特网和组成技术知识点",
    //     id: 1,
    //   },
    //   children: [
    //     {
    //       data: {
    //         text: "网络基本概念",
    //         id: 2,
    //       },
    //       children: [
    //         {
    //           data: {
    //             text: "因特网的定义与特点",
    //             id: 3,
    //           },
    //         },
    //       ],
    //     },
    //   ],
    // };
  } catch (error) {
    message.error("获取思维导图失败");
    console.error(error);
  }
};

// 节点点击处理
const handleNodeClick = (node: { nodeId: number; nodeText: string }) => {
  if (!node.nodeId) return;

  currentNodeId.value = node.nodeId;
  currentNodeText.value = node.nodeText;
  showGenerateModal.value = true;
};

// 添加题目规格
const addSpec = () => {
  generateForm.value.specs.push({
    type: "choice",
    count: 1,
    difficulty: null,
  });
};

// 移除题目规格
const removeSpec = (index: number) => {
  generateForm.value.specs.splice(index, 1);
};

// 生成题目
const handleGenerateQuestions = async () => {
  if (!currentNodeId.value) return;

  try {
    generating.value = true;

    const response = await questionApi.generateQuestionsForMindMapNode(
      currentNodeId.value,
      generateForm.value.specs
    );
    console.log("返回：", response);
    // 确保响应数据格式正确
    if (!response.data.knowledge_point) {
      response.data.knowledge_point = {
        id: currentNodeId.value,
        name: currentNodeText.value || "未知知识点",
      };
    }

    generatedQuestions.value = response;
    console.log("generatedQuestions", generatedQuestions.value);
    showGenerateModal.value = false;
    showResultModal.value = true;
    message.success("题目生成成功");
  } catch (error) {
    message.error("题目生成失败");
    console.error(error);

    showResultModal.value = true;
  } finally {
    generating.value = false;
  }
};

// 关闭模态框
const closeModal = () => {
  showGenerateModal.value = false;
  generateForm.value.specs = [
    {
      type: "choice",
      count: 1,
      difficulty: null,
    },
  ];
};

// 获取题目类型名称
const getQuestionTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    choice: "选择题",
    fill: "填空题",
    short_answer: "简答题",
  };
  return typeMap[type] || type;
};

onMounted(() => {
  fetchMindMap();
});
</script>

<style scoped>
.mind-map-questions-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mind-map-wrapper {
  flex: 1;
  min-height: 500px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.specs-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.spec-item {
  display: flex;
  align-items: center;
}

.add-spec-btn {
  width: 100%;
  margin-top: 8px;
}

.question-content {
  white-space: pre-wrap;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
