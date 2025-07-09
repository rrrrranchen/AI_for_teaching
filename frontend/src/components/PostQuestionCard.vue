<template>
  <a-col :span="8">
    <a-card hoverable>
      <template #cover>
        <img alt="example" src="@/assets/postquestion.png" />
      </template>
      <a-card-meta
        title="课后习题生成"
        description="根据教学设计版本生成课后题目"
      />
      <template #actions>
        <a-button type="primary" @click="handleCardAction"> 开始生成 </a-button>
      </template>
    </a-card>

    <!-- 分步骤模态框 -->
    <a-modal
      v-model:visible="showStepModal"
      title="生成课后习题"
      :width="800"
      :ok-text="currentStep === 1 ? '下一步' : '提交'"
      :cancel-text="currentStep === 2 ? '上一步' : '取消'"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="submitting"
    >
      <a-steps :current="currentStep - 1" class="steps">
        <a-step title="选择课程和章节" />
        <a-step title="选择设计版本" />
      </a-steps>

      <div class="step-content">
        <!-- 第一步：选择课程 -->
        <div v-show="currentStep === 1" class="step-1">
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

        <!-- 第二步：选择教学设计版本 -->
        <div v-show="currentStep === 2" class="step-2">
          <a-form layout="vertical">
            <a-form-item
              label="教学设计"
              required
              :validate-status="designError ? 'error' : ''"
              :help="designError"
            >
              <a-select
                v-model:value="selectedDesign"
                @change="handleDesignChange"
                placeholder="请选择教学设计"
                :loading="loadingDesigns"
              >
                <a-select-option
                  v-for="design in designs"
                  :key="design.design_id"
                  :value="design.design_id"
                >
                  {{ design.title }}
                </a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item
              label="版本"
              required
              :validate-status="versionError ? 'error' : ''"
              :help="versionError"
            >
              <a-select
                v-model:value="selectedVersion"
                placeholder="请选择版本"
                :loading="loadingVersions"
              >
                <a-select-option
                  v-for="version in versions"
                  :key="version.id"
                  :value="version.id"
                >
                  {{ version.version }} (推荐度:
                  {{ version.recommendation_score }})
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>
      </div>
    </a-modal>
  </a-col>
</template>

<script lang="ts">
import { defineComponent, reactive, ref } from "vue";
import { message } from "ant-design-vue";
import { getAllCourseclasses, type Courseclass } from "@/api/courseclass";
import { getCoursesByCourseclass, type Course } from "@/api/course";
import {
  getCourseDesigns,
  getDesignVersions,
  type TeachingDesign,
  type TeachingDesignVersion,
} from "@/api/teachingdesign";
import { questionApi } from "@/api/questions";

export default defineComponent({
  name: "PostQuestionCard",
  setup() {
    // 模态框状态
    const showStepModal = ref(false);
    const currentStep = ref(1);
    const submitting = ref(false);

    // 课程数据
    const courseclasses = ref<Courseclass[]>([]);
    const courses = ref<Course[]>([]);
    const selectedCourseclass = ref<number>();
    const selectedCourse = ref<number>();

    // 教学设计数据
    const designs = ref<TeachingDesign[]>([]);
    const versions = ref<TeachingDesignVersion[]>([]);
    const selectedDesign = ref<number>();
    const selectedVersion = ref<number>();
    const loadingDesigns = ref(false);
    const loadingVersions = ref(false);

    // 错误提示
    const courseclassError = ref("");
    const courseError = ref("");
    const designError = ref("");
    const versionError = ref("");

    // 处理卡片点击
    const handleCardAction = () => {
      showStepModal.value = true;
      currentStep.value = 1;
      loadCourseclasses();
    };

    // 加载课程班
    const loadCourseclasses = async () => {
      try {
        courseclasses.value = await getAllCourseclasses();
      } catch (error) {
        message.error("课程班加载失败");
      }
    };

    // 课程班变更处理
    const handleCourseclassChange = async (value: number) => {
      try {
        courses.value = await getCoursesByCourseclass(value);
        selectedCourse.value = undefined;
      } catch (error) {
        message.error("课程加载失败");
      }
    };

    // 处理模态确认
    const handleModalOk = async () => {
      if (currentStep.value === 1) {
        // 第一步验证
        courseclassError.value = selectedCourseclass.value
          ? ""
          : "请选择课程班";
        courseError.value = selectedCourse.value ? "" : "请选择课程";

        if (!selectedCourseclass.value || !selectedCourse.value) return;

        // 加载教学设计
        try {
          loadingDesigns.value = true;
          designs.value = await getCourseDesigns(selectedCourse.value);
          console.log(designs.value);
          currentStep.value = 2;
        } catch (error) {
          message.error("教学设计加载失败");
        } finally {
          loadingDesigns.value = false;
        }
      } else {
        // 第二步验证
        designError.value = selectedDesign.value ? "" : "请选择教学设计";
        versionError.value = selectedVersion.value ? "" : "请选择版本";

        if (!selectedDesign.value || !selectedVersion.value) return;

        try {
          submitting.value = true;
          await handleGenerateQuestions();
          showStepModal.value = false;
          resetForm();
        } catch (error) {
          console.error("生成失败", error);
        } finally {
          submitting.value = false;
        }
      }
    };

    // 在handleDesignChange方法中添加校验
    const handleDesignChange = async (value: number) => {
      try {
        if (!value) throw new Error("未选择教学设计");
        console.log(value);
        loadingVersions.value = true;
        const data = await getDesignVersions(value);
        versions.value = data.versions;
        selectedVersion.value = undefined;
      } catch (error) {
        message.error("版本加载失败: " + (error as Error).message);
      } finally {
        loadingVersions.value = false;
      }
    };

    // 生成课后习题
    const handleGenerateQuestions = async () => {
      const hide = message.loading("正在生成课后习题...", 0);
      try {
        const params = {
          design_id: selectedDesign.value!,
          version_id: selectedVersion.value!,
        };

        const questions = await questionApi.generatePostQuestions(params);
        message.success(`成功生成 ${questions.length} 道课后习题`);
      } catch (error) {
        message.error("生成失败，请稍后重试");
        throw error;
      } finally {
        hide();
      }
    };

    // 重置表单
    const resetForm = () => {
      currentStep.value = 1;
      selectedCourseclass.value = undefined;
      selectedCourse.value = undefined;
      selectedDesign.value = undefined;
      selectedVersion.value = undefined;
      designs.value = [];
      versions.value = [];
    };

    return {
      showStepModal,
      currentStep,
      submitting,
      courseclasses,
      courses,
      designs,
      versions,
      selectedCourseclass,
      selectedCourse,
      selectedDesign,
      selectedVersion,
      loadingDesigns,
      loadingVersions,
      courseclassError,
      courseError,
      designError,
      versionError,
      handleCardAction,
      handleCourseclassChange,
      handleDesignChange,
      handleModalOk,
      handleModalCancel: () => {
        showStepModal.value = false;
        resetForm();
      },
    };
  },
});
</script>

<style scoped>
/* 保持与其他卡片一致的样式 */
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

.ant-form-item {
  margin-bottom: 16px;
}
</style>
