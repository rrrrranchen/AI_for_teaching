<template>
  <a-col :span="8">
    <a-card hoverable>
      <template #cover>
        <img alt="example" src="@/assets/aiforedu.png" />
      </template>
      <a-card-meta
        title="教学设计生成"
        description="根据课程内容自动生成教学设计"
      />
      <template #actions>
        <a-button type="primary" @click="handleCardAction"> 开始生成 </a-button>
      </template>
    </a-card>

    <!-- 分步骤模态框 -->
    <a-modal
      v-model:visible="showStepModal"
      title="创建教学设计"
      :width="800"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="submitting"
    >
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
import { createTeachingDesign } from "@/api/teachingdesign";
import type { CreateTeachingDesignParams } from "@/api/teachingdesign";
import type { FormInstance } from "ant-design-vue";

export default defineComponent({
  name: "TeachingDesignCard",
  setup() {
    // 模态框状态
    const showStepModal = ref(false);
    const currentStep = ref(1);
    const submitting = ref(false);
    const formRef = ref<FormInstance>();

    // 课程数据
    const courseclasses = ref<Courseclass[]>([]);
    const courses = ref<Course[]>([]);
    const selectedCourseclass = ref<number>();
    const selectedCourse = ref<number>();

    // 错误提示
    const courseclassError = ref("");
    const courseError = ref("");

    // 处理卡片按钮点击
    const handleCardAction = () => {
      showStepModal.value = true;
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
        selectedCourse.value = undefined;
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

        if (!selectedCourseclass.value || !selectedCourse.value) return;
        currentStep.value = 2;
      } else {
        try {
          await formRef.value?.validate();
          submitting.value = true;
          await handleCreateTeachingDesign();
          showStepModal.value = false;
        } catch (error) {
          console.log("表单验证失败", error);
        } finally {
          submitting.value = false;
        }
      }
    };

    // 处理模态框取消
    const handleModalCancel = () => {
      if (currentStep.value === 2) {
        currentStep.value = 1;
      } else {
        showStepModal.value = false;
      }
    };

    // 创建教学设计
    const handleCreateTeachingDesign = async () => {
      const hide = message.loading("正在生成教学设计，请稍候...", 0);
      try {
        const params: CreateTeachingDesignParams = {
          course_id: selectedCourse.value!,
        };

        const response = await createTeachingDesign(params);
        message.success(
          `成功创建教学设计，包含 ${response.versions.length} 个版本`
        );
      } catch (error) {
        message.error("教学设计生成失败");
        throw error;
      } finally {
        hide();
      }
    };

    return {
      showStepModal,
      currentStep,
      submitting,
      formRef,
      courseclasses,
      courses,
      selectedCourseclass,
      selectedCourse,
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
