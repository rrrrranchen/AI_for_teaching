<template>
  <div class="smart-preparation">
    <!-- 上下分栏布局 -->
    <a-row :gutter="16" class="full-height">
      <a-col :span="24" class="top-section">
        <!-- 三个卡片布局 -->
        <a-row :gutter="16">
          <a-col :span="8" v-for="(card, index) in cards" :key="index">
            <a-card hoverable>
              <template #cover>
                <img alt="example" :src="card.image" />
              </template>
              <a-card-meta :title="card.title" :description="card.description">
              </a-card-meta>
              <template #actions>
                <a-button type="primary" @click="handleCardAction(index)">
                  {{ card.buttonText }}
                </a-button>
              </template>
            </a-card>
          </a-col>
        </a-row>

        <!-- 第一步：选择课程班和课程的模态框 -->
        <a-modal
          v-model:visible="showCourseSelect"
          title="选择课程"
          @ok="handleCourseSelected"
        >
          <a-form layout="vertical">
            <a-form-item label="课程班">
              <a-select
                v-model:value="selectedCourseclass"
                @change="handleCourseclassChange"
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

            <a-form-item label="课程">
              <a-select v-model:value="selectedCourse">
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
        </a-modal>

        <!-- 第二步：输入课程信息的模态框 -->
        <a-modal
          v-model:visible="showCourseInfoInput"
          title="创建课前习题"
          @ok="handleCreatePreQuestions"
        >
          <a-form layout="vertical" :model="formState">
            <a-form-item
              label="课程标题"
              name="title"
              :rules="[{ required: true, message: '请输入课程标题' }]"
            >
              <a-input v-model:value="formState.title" />
            </a-form-item>

            <a-form-item
              label="教学内容"
              name="content"
              :rules="[{ required: true, message: '请输入教学内容' }]"
            >
              <a-textarea v-model:value="formState.content" :rows="4" />
            </a-form-item>

            <a-form-item
              label="教学目标"
              name="objective"
              :rules="[{ required: true, message: '请输入教学目标' }]"
            >
              <a-textarea v-model:value="formState.objective" :rows="4" />
            </a-form-item>
          </a-form>
        </a-modal>
      </a-col>
      <a-col :span="24" class="bottom-section">
        <!-- 下半部分留空 -->
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, ref } from "vue";
import { message } from "ant-design-vue";
import { getAllCourseclasses } from "@/api/courseclass";
import type { Courseclass } from "@/api/courseclass";
import { getCoursesByCourseclass } from "@/api/course";
import type { Course } from "@/api/course";
import { questionApi } from "@/api/questions";
import type { CreatePreQuestionsParams } from "@/api/questions";

interface CardItem {
  title: string;
  description: string;
  image: string;
  buttonText: string;
}

interface FormState {
  title: string;
  content: string;
  objective: string;
}

export default defineComponent({
  name: "SmartPreparationView",
  setup() {
    // 卡片配置
    const cards = reactive<CardItem[]>([
      {
        title: "课前习题生成",
        description: "根据课程内容自动生成预习题目",
        image: "https://example.com/pre-class.png",
        buttonText: "开始生成",
      },
      {
        title: "功能待开发",
        description: "敬请期待",
        image: "https://example.com/coming-soon.png",
        buttonText: "暂不可用",
      },
      {
        title: "功能待开发",
        description: "敬请期待",
        image: "https://example.com/coming-soon.png",
        buttonText: "暂不可用",
      },
    ]);

    // 模态框状态
    const showCourseSelect = ref(false);
    const showCourseInfoInput = ref(false);

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

    // 处理卡片按钮点击
    const handleCardAction = (index: number) => {
      if (index === 0) {
        showCourseSelect.value = true;
        loadCourseclasses();
      }
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
      } catch (error) {
        message.error("课程加载失败");
      }
    };

    // 确认课程选择
    const handleCourseSelected = () => {
      if (!selectedCourse.value) {
        message.warning("请选择课程");
        return;
      }
      showCourseSelect.value = false;
      showCourseInfoInput.value = true;
    };
    //提交创建请求
    const handleCreatePreQuestions = async () => {
      const hide = message.loading("正在生成课前习题，请稍候...", 0);

      try {
        const params: CreatePreQuestionsParams = {
          content: `课程标题：${formState.title}\n教学内容：${formState.content}\n教学目标：${formState.objective}`,
        };

        await questionApi.createPreQuestions(selectedCourse.value!, params);
        message.success("课前习题生成请求已发送");
        showCourseInfoInput.value = false;
        resetForm();
      } catch (error) {
        message.error("请求发送失败");
      } finally {
        hide();
      }
    };

    // 重置表单
    const resetForm = () => {
      Object.assign(formState, {
        title: "",
        content: "",
        objective: "",
      });
      selectedCourseclass.value = undefined;
      selectedCourse.value = undefined;
    };

    return {
      cards,
      showCourseSelect,
      showCourseInfoInput,
      courseclasses,
      courses,
      selectedCourseclass,
      selectedCourse,
      formState,
      handleCardAction,
      handleCourseclassChange,
      handleCourseSelected,
      handleCreatePreQuestions,
    };
  },
});
</script>

<style scoped>
.full-height {
  height: 100vh;
}

.top-section {
  height: 50vh;
  padding: 20px;
  overflow-y: auto;
}

.bottom-section {
  height: 50vh;
  border-top: 1px solid #f0f0f0;
  padding: 20px;
}

.ant-card {
  margin-bottom: 16px;
}

.ant-card-cover img {
  height: 200px;
  object-fit: cover;
}
</style>
