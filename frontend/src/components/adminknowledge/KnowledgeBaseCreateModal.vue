<!-- 管理员 -->
<template>
  <a-modal
    v-model:visible="visible"
    title="创建系统知识库"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
    :width="800"
    :mask-closable="false"
    :ok-button-props="{ disabled: isCreating }"
  >
    <a-alert
      message="系统知识库创建提示"
      description="系统知识库将由管理员维护，可被所有用户使用"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <a-form :model="formState" :rules="rules" layout="vertical">
      <a-form-item label="知识库名称" name="name">
        <a-input
          v-model:value="formState.name"
          placeholder="请输入系统知识库名称"
          :disabled="isCreating"
          allow-clear
        />
      </a-form-item>
      <a-form-item label="知识库描述" name="description">
        <a-textarea
          v-model:value="formState.description"
          placeholder="请输入系统知识库描述"
          :rows="4"
          :disabled="isCreating"
          allow-clear
        />
      </a-form-item>
      <a-form-item label="知识库类型" name="base_type">
        <a-radio-group
          v-model:value="formState.base_type"
          button-style="solid"
          @change="filterCategoriesByType"
        >
          <a-radio-button value="structural">结构化</a-radio-button>
          <a-radio-button value="non_structural">非结构化</a-radio-button>
        </a-radio-group>
        <div class="tip-text">知识库类型创建后不可修改</div>
      </a-form-item>
      <a-form-item label="关联系统类目" name="category_ids">
        <a-select
          v-model:value="formState.category_ids"
          mode="multiple"
          placeholder="请选择关联的系统类目"
          style="width: 100%"
          :options="filteredCategoryOptions"
          :disabled="isCreating"
          :filter-option="filterOption"
          show-search
          option-filter-prop="label"
          :loading="categoriesLoading"
        >
        </a-select>
      </a-form-item>
      <a-form-item label="可见性设置" name="is_public">
        <a-space>
          <a-switch
            v-model:checked="formState.is_public"
            checked-children="公开"
            un-checked-children="私有"
            :disabled="isCreating"
          />
          <span class="tip-text">{{
            formState.is_public ? "所有用户可见" : "仅管理员可见"
          }}</span>
        </a-space>
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
import {
  adminCreateKnowledgeBase,
  adminSearchCategories,
} from "@/api/knowledgebasemanage";
import type { Category } from "@/api/knowledgebase";

const emit = defineEmits(["created"]);

const visible = ref(false);
const confirmLoading = ref(false);
const categoriesLoading = ref(false);
const allCategoryOptions = ref<
  { value: number; label: string; type: string; is_system: boolean }[]
>([]);
const filteredCategoryOptions = ref<
  { value: number; label: string; type: string }[]
>([]);

// 创建状态相关变量
const isCreating = ref(false);
const creationProgress = ref(0);
const creationStatus = ref<"active" | "success" | "exception">("active");
const creationStatusText = ref("系统知识库创建中，请稍候...");
const creationInterval = ref<number | null>(null);

interface FormState {
  name: string;
  description?: string;
  base_type: "structural" | "non_structural";
  category_ids: number[];
  is_public: boolean;
  is_system?: boolean;
}

const formState = reactive<FormState>({
  name: "",
  description: "",
  base_type: "structural",
  category_ids: [],
  is_public: false,
  is_system: true, // 管理员创建的知识库默认为系统知识库
});

// 更严格的验证规则
const rules = {
  name: [
    { required: true, message: "请输入系统知识库名称", trigger: "blur" },
    {
      min: 2,
      max: 50,
      message: "名称长度需在2-50个字符之间",
      trigger: "blur",
    },
    {
      validator: (rule: any, value: string) => {
        if (/[<>]/.test(value)) {
          return Promise.reject("名称不能包含特殊字符");
        }
        return Promise.resolve();
      },
      trigger: "blur",
    },
  ],
  description: [
    { max: 200, message: "描述不能超过200个字符", trigger: "blur" },
  ],
  base_type: [
    { required: true, message: "请选择知识库类型", trigger: "change" },
  ],
  category_ids: [
    { required: true, message: "请至少选择一个系统类目", trigger: "change" },
    {
      validator: () => {
        // 验证所选类目是否为系统类目且类型匹配
        const selectedCategories = allCategoryOptions.value.filter((cat) =>
          formState.category_ids.includes(cat.value)
        );
        return selectedCategories.every(
          (cat) => cat.type === formState.base_type && cat.is_system
        );
      },
      message: "必须选择与知识库类型匹配的系统类目",
      trigger: "change",
    },
  ],
};

const showModal = async () => {
  console.log("showModal");
  visible.value = true;
  resetCreationStatus();
  if (allCategoryOptions.value.length === 0) {
    await fetchSystemCategories();
  }
  filterCategoriesByType();
};

const resetCreationStatus = () => {
  isCreating.value = false;
  creationProgress.value = 0;
  creationStatus.value = "active";
  creationStatusText.value = "系统知识库创建中，请稍候...";
  if (creationInterval.value !== null) {
    window.clearInterval(creationInterval.value);
    creationInterval.value = null;
  }
};

const fetchSystemCategories = async () => {
  categoriesLoading.value = true;
  try {
    const result = await adminSearchCategories({
      is_system: true,
      per_page: 1000, // 获取所有系统类目
    });
    console.log("获取到的系统类目", result);
    allCategoryOptions.value = result.data.map((cat: Category) => ({
      value: cat.id,
      label: `${cat.name} (${
        cat.category_type === "structural" ? "结构化" : "非结构化"
      })${cat.is_system ? " [系统]" : ""}`,
      type: cat.category_type,
      is_system: cat.is_system,
    }));
  } catch (error) {
    message.error("获取系统类目列表失败");
    console.error(error);
  } finally {
    categoriesLoading.value = false;
  }
};

// 根据知识库类型过滤系统类目
const filterCategoriesByType = () => {
  filteredCategoryOptions.value = allCategoryOptions.value
    .filter((cat) => cat.type === formState.base_type && cat.is_system)
    .map(({ value, label, type }) => ({ value, label, type }));

  // 清空已选的类目，避免类型不匹配
  formState.category_ids = formState.category_ids.filter((id) => {
    const cat = allCategoryOptions.value.find((c) => c.value === id);
    return cat?.type === formState.base_type && cat.is_system;
  });
  console.log("过滤后的系统类目:", filteredCategoryOptions.value);
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
      creationStatusText.value = "系统知识库处理中，即将完成...";
    }
  }, 100);

  try {
    // 实际API请求
    const result = await adminCreateKnowledgeBase({
      name: formState.name.trim(),
      description: formState.description?.trim(),
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

    message.success("系统知识库创建成功");
    isCreating.value = false;
    emit("created", result);
    handleCancel();
  } catch (error: any) {
    // 出错处理
    if (creationInterval.value !== null) {
      window.clearInterval(creationInterval.value);
      creationInterval.value = null;
    }

    creationProgress.value = 100;
    creationStatus.value = "exception";
    creationStatusText.value = "创建失败";

    const errorMessage = error.response?.data?.message || "系统知识库创建失败";
    message.error(errorMessage);
    console.error("创建系统知识库错误:", error);
  } finally {
    confirmLoading.value = false;
    isCreating.value = false;
  }
};

const handleCancel = () => {
  if (isCreating.value) {
    message.warning("系统知识库正在创建中，请等待完成");
    return;
  }

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

<style scoped>
.tip-text {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 4px;
}
</style>
