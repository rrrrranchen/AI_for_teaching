<template>
  <a-modal
    v-model:visible="visible"
    title="创建知识库"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
    :width="800"
    :ok-button-props="{ disabled: isCreating }"
  >
    <a-form :model="formState" :rules="rules" layout="vertical">
      <a-form-item label="知识库名称" name="name">
        <a-input
          v-model:value="formState.name"
          placeholder="请输入知识库名称"
          :disabled="isCreating"
        />
      </a-form-item>
      <a-form-item label="知识库描述" name="description">
        <a-textarea
          v-model:value="formState.description"
          placeholder="请输入知识库描述"
          :rows="4"
          :disabled="isCreating"
        />
      </a-form-item>
      <a-form-item label="知识库类型" name="base_type">
        <a-radio-group
          v-model:value="formState.base_type"
          @change="filterCategoriesByType"
        >
          <a-radio-button value="structural">结构化</a-radio-button>
          <a-radio-button value="non_structural">非结构化</a-radio-button>
        </a-radio-group>
      </a-form-item>
      <a-form-item label="关联类目" name="category_ids">
        <a-select
          v-model:value="formState.category_ids"
          mode="multiple"
          placeholder="请选择关联类目"
          style="width: 100%"
          :options="filteredCategoryOptions"
          :disabled="isCreating"
          :filter-option="filterOption"
          show-search
          option-filter-prop="label"
        ></a-select>
      </a-form-item>
      <a-form-item label="是否公开" name="is_public">
        <a-switch
          v-model:checked="formState.is_public"
          :disabled="isCreating"
        />
      </a-form-item>

      <div v-if="isCreating" style="margin-top: 16px">
        <a-progress
          :percent="creationProgress"
          :status="creationStatus"
          :stroke-color="{
            '0%': '#108ee9',
            '100%': '#87d068',
          }"
        />
        <p style="text-align: center; margin-top: 8px">
          {{ creationStatusText }}
        </p>
      </div>
    </a-form>
  </a-modal>
</template>
<script lang="ts" setup>
import { ref, reactive, defineEmits, defineExpose } from "vue";
import { message } from "ant-design-vue";
import { createKnowledgeBase, getCategories } from "@/api/knowledgebase";
import type { Category } from "@/api/knowledgebase";

const emit = defineEmits(["created"]);

const visible = ref(false);
const confirmLoading = ref(false);
const allCategoryOptions = ref<
  { value: number; label: string; type: string }[]
>([]);
const filteredCategoryOptions = ref<
  { value: number; label: string; type: string }[]
>([]);

// 新增创建状态相关变量
const isCreating = ref(false);
const creationProgress = ref(0);
const creationStatus = ref<"active" | "success" | "exception">("active");
const creationStatusText = ref("知识库创建中，请稍候...");
const creationInterval = ref<number | null>(null);

interface FormState {
  name: string;
  description?: string;
  base_type: "structural" | "non_structural";
  category_ids: number[];
  is_public: boolean;
}

const formState = reactive<FormState>({
  name: "",
  description: "",
  base_type: "structural",
  category_ids: [],
  is_public: false,
});

const rules = {
  name: [
    { required: true, message: "请输入知识库名称", trigger: "blur" },
    { max: 100, message: "名称不能超过100个字符", trigger: "blur" },
  ],
  base_type: [
    { required: true, message: "请选择知识库类型", trigger: "change" },
  ],
  category_ids: [
    { required: true, message: "请至少选择一个类目", trigger: "change" },
    {
      validator: () => {
        // 验证所选类目类型是否与知识库类型匹配
        const selectedCategories = allCategoryOptions.value.filter((cat) =>
          formState.category_ids.includes(cat.value)
        );
        return selectedCategories.every(
          (cat) => cat.type === formState.base_type
        );
      },
      message: "所选类目类型必须与知识库类型匹配",
      trigger: "change",
    },
  ],
};

const showModal = async () => {
  visible.value = true;
  resetCreationStatus();
  if (allCategoryOptions.value.length === 0) {
    await fetchCategories();
  }
  filterCategoriesByType();
};

const resetCreationStatus = () => {
  isCreating.value = false;
  creationProgress.value = 0;
  creationStatus.value = "active";
  creationStatusText.value = "知识库创建中，请稍候...";
  if (creationInterval.value !== null) {
    window.clearInterval(creationInterval.value);
    creationInterval.value = null;
  }
};

const fetchCategories = async () => {
  try {
    const result = await getCategories();
    allCategoryOptions.value = [
      ...result.structured_categories.map((cat) => ({
        value: cat.id,
        label: `${cat.name} (${
          cat.category_type === "structural" ? "结构化" : "非结构化"
        })`,
        type: cat.category_type,
      })),
      ...result.non_structured_categories.map((cat) => ({
        value: cat.id,
        label: `${cat.name} (${
          cat.category_type === "structural" ? "结构化" : "非结构化"
        })`,
        type: cat.category_type,
      })),
    ];
  } catch (error) {
    message.error("获取类目列表失败");
    console.error(error);
  }
};

// 根据知识库类型过滤类目
const filterCategoriesByType = () => {
  filteredCategoryOptions.value = allCategoryOptions.value.filter(
    (cat) => cat.type === formState.base_type
  );
  // 清空已选的类目，避免类型不匹配
  formState.category_ids = formState.category_ids.filter((id) => {
    const cat = allCategoryOptions.value.find((c) => c.value === id);
    return cat?.type === formState.base_type;
  });
};

const filterOption = (input: string, option: any) => {
  return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};

const handleOk = async () => {
  confirmLoading.value = true;
  isCreating.value = true;

  const startTime = Date.now();
  const duration = 20000; // 最大模拟时长20秒

  // 启动创建进度模拟
  creationInterval.value = window.setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(99, Math.floor((elapsed / duration) * 100));
    creationProgress.value = progress;

    if (progress >= 99 && creationInterval.value !== null) {
      window.clearInterval(creationInterval.value);
      creationInterval.value = null;
      creationStatusText.value = "知识库处理中，即将完成...";
    }
  }, 100);

  try {
    // 实际API请求
    const result = await createKnowledgeBase({
      name: formState.name,
      description: formState.description,
      base_type: formState.base_type,
      category_ids: formState.category_ids,
      is_public: formState.is_public,
    });

    // API完成后清除定时器
    if (creationInterval.value !== null) {
      window.clearInterval(creationInterval.value);
      creationInterval.value = null;
    }

    // 立即完成进度显示
    creationProgress.value = 100;
    creationStatus.value = "success";
    creationStatusText.value = "创建成功！";

    message.success("知识库创建成功");
    isCreating.value = false;
    emit("created", result);
    handleCancel();
  } catch (error) {
    // 出错处理
    if (creationInterval.value !== null) {
      window.clearInterval(creationInterval.value);
      creationInterval.value = null;
    }

    creationProgress.value = 100;
    creationStatus.value = "exception";
    creationStatusText.value = "创建失败";

    message.error("知识库创建失败");
    console.error(error);
  } finally {
    confirmLoading.value = false;
    isCreating.value = false;
  }
};

const handleCancel = () => {
  // 取消时清除定时器
  if (creationInterval.value !== null) {
    window.clearInterval(creationInterval.value);
    creationInterval.value = null;
  }
  visible.value = false;
  formState.name = "";
  formState.description = "";
  formState.base_type = "structural";
  formState.category_ids = [];
  formState.is_public = false;
  resetCreationStatus();
};

defineExpose({
  showModal,
});
</script>
