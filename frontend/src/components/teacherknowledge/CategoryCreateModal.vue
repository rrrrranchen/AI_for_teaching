<template>
  <a-modal
    v-model:visible="visible"
    title="创建新类目"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
  >
    <a-form :model="formState" :rules="rules" layout="vertical">
      <a-form-item label="类目名称" name="name">
        <a-input v-model:value="formState.name" placeholder="请输入类目名称" />
      </a-form-item>
      <a-form-item label="类目描述" name="description">
        <a-textarea
          v-model:value="formState.description"
          placeholder="请输入类目描述"
          :rows="4"
        />
      </a-form-item>
      <a-form-item label="类目类型" name="category_type">
        <a-radio-group v-model:value="formState.category_type">
          <a-radio-button value="structural">结构化</a-radio-button>
          <a-radio-button value="non_structural">非结构化</a-radio-button>
        </a-radio-group>
      </a-form-item>
      <a-form-item label="是否公开" name="is_public">
        <a-switch v-model:checked="formState.is_public" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, reactive, defineExpose, defineEmits } from "vue";
import { message } from "ant-design-vue";
import {
  createCategory,
  type CategoryType,
  type LoadingState,
} from "@/api/knowledgebase";

const emit = defineEmits(["created"]);

const visible = ref(false);
const confirmLoading = ref(false);

interface FormState {
  name: string;
  description: string;
  category_type: CategoryType; // 使用导入的CategoryType类型
  is_public: boolean;
}

const formState = reactive<FormState>({
  name: "",
  description: "",
  category_type: "structural", // 默认值，确保是CategoryType类型
  is_public: false,
});

const rules = {
  name: [
    { required: true, message: "请输入类目名称", trigger: "blur" },
    { max: 100, message: "名称不能超过100个字符", trigger: "blur" },
  ],
  category_type: [
    { required: true, message: "请选择类目类型", trigger: "change" },
  ],
};

const showModal = () => {
  visible.value = true;
};

const handleOk = async () => {
  confirmLoading.value = true;
  try {
    const result = await createCategory({
      name: formState.name,
      description: formState.description,
      category_type: formState.category_type, // 现在类型匹配
      is_public: formState.is_public,
    });
    message.success("类目创建成功");
    emit("created", result);
    handleCancel();
  } catch (error) {
    message.error("类目创建失败");
    console.error(error);
  } finally {
    confirmLoading.value = false;
  }
};

const handleCancel = () => {
  visible.value = false;
  // 重置表单
  formState.name = "";
  formState.description = "";
  formState.category_type = "structural";
  formState.is_public = false;
};

defineExpose({
  showModal,
});
</script>
