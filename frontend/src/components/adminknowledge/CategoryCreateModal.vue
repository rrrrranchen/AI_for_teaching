<template>
  <a-modal
    v-model:visible="visible"
    title="创建系统类目"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="confirmLoading"
    width="600px"
  >
    <a-form :model="formState" :rules="rules" layout="vertical">
      <a-form-item label="类目名称" name="name">
        <a-input
          v-model:value="formState.name"
          placeholder="请输入系统类目名称"
          allow-clear
        />
      </a-form-item>
      <a-form-item label="类目描述" name="description">
        <a-textarea
          v-model:value="formState.description"
          placeholder="请输入系统类目描述"
          :rows="4"
          allow-clear
        />
      </a-form-item>
      <a-form-item label="类目类型" name="category_type">
        <a-radio-group v-model:value="formState.category_type">
          <a-radio-button value="structural">结构化</a-radio-button>
          <a-radio-button value="non_structural">非结构化</a-radio-button>
        </a-radio-group>
        <div class="tip-text">系统类目类型创建后不可修改</div>
      </a-form-item>
      <a-form-item label="可见性设置" name="is_public">
        <a-space>
          <a-switch
            v-model:checked="formState.is_public"
            checked-children="公开"
            un-checked-children="私有"
          />
          <span class="tip-text">{{
            formState.is_public ? "所有用户可见" : "仅管理员可见"
          }}</span>
        </a-space>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, reactive, defineExpose, defineEmits } from "vue";
import { message } from "ant-design-vue";
import { adminCreateCategory } from "@/api/knowledgebasemanage";
import { type CategoryType } from "@/api/knowledgebase";

const emit = defineEmits(["created"]);

const visible = ref(false);
const confirmLoading = ref(false);

interface FormState {
  name: string;
  description: string;
  category_type: CategoryType;
  is_public: boolean;
}

const formState = reactive<FormState>({
  name: "",
  description: "",
  category_type: "structural",
  is_public: false,
});

// 更严格的验证规则
const rules = {
  name: [
    { required: true, message: "请输入系统类目名称", trigger: "blur" },
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
    const result = await adminCreateCategory({
      name: formState.name.trim(),
      description: formState.description.trim(),
      category_type: formState.category_type,
      is_public: formState.is_public,
    });

    message.success("系统类目创建成功");
    emit("created", result);
    handleCancel();
  } catch (error: any) {
    message.error(error.response?.data?.message || "系统类目创建失败");
    console.error("创建系统类目错误:", error);
  } finally {
    confirmLoading.value = false;
  }
};

const handleCancel = () => {
  visible.value = false;
  // 重置表单
  Object.assign(formState, {
    name: "",
    description: "",
    category_type: "structural",
    is_public: false,
  });
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
