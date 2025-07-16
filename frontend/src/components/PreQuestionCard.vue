<template>
  <a-col :span="8">
    <a-card hoverable>
      <template #cover>
        <img alt="example" :src="cardData.image" />
      </template>
      <a-card-meta :title="cardData.title" :description="cardData.description">
      </a-card-meta>
      <template #actions>
        <a-button type="primary" @click="handleCardAction">
          {{ cardData.buttonText }}
        </a-button>
      </template>
    </a-card>

    <!-- 分步骤模态框 -->
    <a-modal
      v-model:visible="showStepModal"
      :title="modalTitle"
      :width="800"
      :ok-text="currentStep === 1 ? '下一步' : '提交'"
      :cancel-text="currentStep === 2 ? '上一步' : '取消'"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="submitting"
    >
      <a-steps :current="currentStep - 1" class="steps">
        <a-step title="选择课程和章节" />
        <a-step title="填写信息" />
      </a-steps>

      <div class="step-content">
        <!-- 第一步：选择课程 -->
        <a-form layout="vertical">
          <a-form-item
            label="课程"
            required
            :validate-status="courseclassError ? 'error' : ''"
            :help="courseclassError"
          >
            <a-select
              v-model:value="selectedCourseclass"
              @change="handleCourseclassChange"
              placeholder="请选择课程"
            >
              <a-select-option
                v-for="courseclass in courseclasses"
                :key="courseclass.id"
                :value="courseclass.id"
              >
                {{ courseclass.name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item
            label="课程章节"
            required
            :validate-status="courseError ? 'error' : ''"
            :help="courseError"
          >
            <a-select
              v-model:value="selectedCourse"
              placeholder="请选择课程章节"
            >
              <a-select-option
                v-for="course in courses"
                :key="course.id"
                :value="course.id"
              >
                {{ course.name }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </div>
    </a-modal>
  </a-col>
</template>

<script lang="ts">
import { defineComponent, reactive, ref } from "vue";
import { message } from "ant-design-vue";
import { getAllCourseclasses } from "@/api/courseclass";
import type { Courseclass } from "@/api/courseclass";
import { getCoursesByCourseclass } from "@/api/course";
import type { Course } from "@/api/course";
import { questionApi } from "@/api/questions";
import type { FormInstance } from "ant-design-vue";

interface FormState {
  title: string;
  content: string;
  objective: string;
}

export default defineComponent({
  name: "PreQuestionCard",
  setup() {
    const cardData = reactive({
      title: "课前水平检测习题生成",
      description: "根据课程内容自动生成课前水平检测题目",
      image: require("@/assets/prequestion.png"),
      buttonText: "开始生成",
    });

    // 模态框状态
    const showStepModal = ref(false);
    const currentStep = ref(1);
    const modalTitle = ref("创建课前习题");
    const submitting = ref(false);
    const formRef = ref<FormInstance>();

    // 课程数据
    const courseclasses = ref<Courseclass[]>([]);
    const courses = ref<Course[]>([]);
    const selectedCourseclass = ref<number>();
    const selectedCourse = ref<number>();

    // 表单数据
    const formState = reactive<FormState>({
      title: "",
      content: "",
      objective: "",
    });

    // 错误提示
    const courseclassError = ref("");
    const courseError = ref("");

    // 处理卡片按钮点击
    const handleCardAction = () => {
      showStepModal.value = true;
      currentStep.value = 1;
      loadCourseclasses();
    };

    // 加载课程班数据
    const loadCourseclasses = async () => {
      try {
        courseclasses.value = await getAllCourseclasses();
      } catch (error) {
        message.error("课程班加载失败");
      }
    };

    // 课程班选择变化时加载课程
    const handleCourseclassChange = async (value: number) => {
      try {
        courses.value = await getCoursesByCourseclass(value);
        selectedCourse.value = undefined; // 重置课程选择
      } catch (error) {
        message.error("课程加载失败");
      }
    };

    // 处理模态框确认
    const handleModalOk = async () => {
      if (currentStep.value === 1) {
        // 第一步验证
        courseclassError.value = selectedCourseclass.value
          ? ""
          : "请选择课程班";
        courseError.value = selectedCourse.value ? "" : "请选择课程";

        if (!selectedCourseclass.value || !selectedCourse.value) {
          return;
        }
        currentStep.value = 2;
      } else {
        // 第二步表单验证
        try {
          await formRef.value?.validate();
          submitting.value = true;
          await handleCreatePreQuestions();
          showStepModal.value = false;
          resetForm();
        } catch (error) {
          console.log("表单验证失败", error);
        } finally {
          submitting.value = false;
        }
      }
    };

    // 处理模态框取消/上一步
    const handleModalCancel = () => {
      if (currentStep.value === 2) {
        currentStep.value = 1;
      } else {
        showStepModal.value = false;
        resetForm();
      }
    };

    // 提交创建请求
    const handleCreatePreQuestions = async () => {
      const hide = message.loading("正在生成课前习题，请稍候...", 0);

      try {
        await questionApi.createPreQuestions(selectedCourse.value!);
        message.success("课前习题生成成功！");
      } catch (error) {
        message.error("请求发送失败");
        throw error;
      } finally {
        hide();
      }
    };

    // 重置表单
    const resetForm = () => {
      currentStep.value = 1;
      Object.assign(formState, {
        title: "",
        content: "",
        objective: "",
      });
      selectedCourseclass.value = undefined;
      selectedCourse.value = undefined;
      courseclassError.value = "";
      courseError.value = "";
    };

    return {
      cardData,
      showStepModal,
      currentStep,
      modalTitle,
      submitting,
      formRef,
      courseclasses,
      courses,
      selectedCourseclass,
      selectedCourse,
      formState,
      courseclassError,
      courseError,
      handleCardAction,
      handleCourseclassChange,
      handleModalOk,
      handleModalCancel,
    };
  },
});
</script>

<style scoped>
.ant-card-cover img {
  height: 200px;
  object-fit: cover;
}

.steps {
  margin-bottom: 24px;
}

.step-content {
  margin-top: 24px;
  min-height: 300px;
  padding: 0 24px;
}

.step-2 .ant-form-item {
  margin-bottom: 16px;
}
</style>
