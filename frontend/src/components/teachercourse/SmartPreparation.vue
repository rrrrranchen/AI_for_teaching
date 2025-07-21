<template>
  <div class="smart-preparation-container">
    <div class="content-section">
      <div class="content-card" :bordered="false">
        <div style="display: flex; margin-bottom: 16px">
          <div class="card-title">
            <book-outlined class="title-icon" />
            <span style="font-size: large">教学内容</span>
          </div>
          <a-button
            type="primary"
            @click="handleSaveContent"
            :loading="saving"
            class="save-btn"
          >
            <template #icon><save-outlined /></template>
            保存内容
          </a-button>
        </div>

        <a-textarea
          v-model:value="content"
          placeholder="在这里输入详细的教学内容..."
          :auto-size="{ minRows: 9, maxRows: 9 }"
          class="content-textarea"
          allow-clear
        />
        <a-divider class="divider" />

        <div class="card-title" style="margin-bottom: 16px">
          <flag-outlined class="title-icon" />
          <span style="font-size: large">教学目标</span>
        </div>
        <a-textarea
          v-model:value="objectives"
          placeholder="在这里输入明确的教学目标..."
          class="content-textarea"
          allow-clear
          :auto-size="{ minRows: 9, maxRows: 9 }"
        />

        <!-- New AI Generation Cards Section -->
        <a-divider class="divider" />
        <div class="card-title" style="margin-bottom: 16px">
          <rocket-outlined class="title-icon" />
          <span style="font-size: large">AI 智能生成</span>
        </div>

        <div class="cards-container">
          <a-card
            hoverable
            class="generation-card"
            @click="showGeneratePreQuestionsConfirm"
            ><template #cover
              ><img
                src="@/assets/prequestion.png"
                alt="Generate Pre-class Questions"
                class="card-image"
            /></template>
            <div class="card-content">
              <!-- <img
                src="@/assets/aiforedu.png"
                alt="Generate Pre-class Questions"
                class="card-image"
              /> -->
              <h3>生成课前习题</h3>
              <p>基于教学内容自动生成课前预习题目</p>
            </div>
          </a-card>

          <a-card
            a-card
            hoverable
            class="generation-card"
            @click="showGenerateTeachingDesignModal"
          >
            <template #cover
              ><img
                src="@/assets/aiforedu.png"
                alt="Generate Teaching Design"
                class="card-image"
            /></template>
            <div class="card-content">
              <h3>生成教学设计</h3>
              <p>基于教学内容自动生成完整教学设计方案</p>
            </div>
          </a-card>
        </div>
      </div>
    </div>

    <div class="preview-section">
      <a-card class="preview-card" :bordered="false">
        <template #title>
          <div class="card-title">
            <eye-outlined class="title-icon" />
            <span>教学设计列表</span>
          </div>
        </template>

        <div class="teaching-design-container">
          <a-empty
            v-if="teachingDesigns.length === 0"
            description="暂无教学设计"
            image-style="height: 120px"
            class="empty-preview"
          >
            <template #image>
              <file-search-outlined style="font-size: 48px; color: #1890ff" />
            </template>
          </a-empty>

          <div class="teaching-design-cards" v-else>
            <TeachingDesignItem
              :key="teachingDesigns[0].design_id"
              :design="teachingDesigns[0]"
              class="teaching-design-item"
              @click="handleDesignClick(teachingDesigns[0])"
            />
            <!-- 添加思维导图生成题目组件 -->
            <a-card
              v-if="teachingDesigns.length > 0"
              class="mind-map-card"
              title="思维导图课后习题生成"
              :bordered="false"
            >
              <MindMapGerQuestions :design-id="teachingDesigns[0].design_id" />
            </a-card>
          </div>
        </div>
      </a-card>
    </div>
  </div>
  <!-- 新增生成中模态框 -->
  <a-modal
    v-model:visible="generatingTeachingDesignModal"
    title="生成教学设计"
    :footer="null"
    :closable="false"
    :maskClosable="false"
    width="400px"
  >
    <div class="generating-modal-content">
      <img src="@/assets/loading.gif" alt="生成中" class="generating-gif" />
      <div class="generating-text">
        <loading-outlined :style="{ fontSize: '24px', color: '#1890ff' }" />
        <span style="margin-top: 16px; margin-left: 12px"
          >多智能体团队正在努力生成...</span
        >
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from "vue";
import { message, Modal } from "ant-design-vue";
import {
  BookOutlined,
  FlagOutlined,
  EyeOutlined,
  SaveOutlined,
  FileSearchOutlined,
  RocketOutlined,
} from "@ant-design/icons-vue";
import { getCourseContent, updateCourseContent } from "@/api/course";
import { useRoute } from "vue-router";
import { questionApi } from "@/api/questions";
import {
  createTeachingDesign,
  getCourseDesigns,
  type TeachingDesign,
} from "@/api/teachingdesign";
import TeachingDesignItem from "@/components/TeachingDesignItem.vue";
import MindMapGerQuestions from "@/components/mindmap/MindMapGerQuestions.vue";

export default defineComponent({
  name: "SmartPreparation",
  components: {
    BookOutlined,
    FlagOutlined,
    EyeOutlined,
    SaveOutlined,
    FileSearchOutlined,
    RocketOutlined,
    TeachingDesignItem,
    MindMapGerQuestions,
  },
  setup() {
    const route = useRoute();
    const courseId = ref<number>(Number(route.params.courseId));
    const content = ref<string>("");
    const objectives = ref<string>("");
    const saving = ref<boolean>(false);
    const generating = ref<boolean>(false);

    const fetchCourseContent = async () => {
      try {
        const data = await getCourseContent(courseId.value);
        content.value = data.content || "";
        objectives.value = data.objectives || "";
      } catch (error) {
        message.error("获取课程内容失败");
        console.error("获取课程内容错误:", error);
      }
    };

    const handleSaveContent = async () => {
      try {
        saving.value = true;
        await updateCourseContent(courseId.value, {
          content: content.value,
          objectives: objectives.value,
        });
        message.success("内容保存成功");
      } catch (error) {
        message.error("保存失败，请稍后重试");
        console.error("保存课程内容错误:", error);
      } finally {
        saving.value = false;
      }
    };

    const handleGeneratePreQuestions = async () => {
      try {
        generating.value = true;
        const response = await questionApi.createPreQuestions(courseId.value);
        message.success(`成功生成 ${response.question_ids.length} 道课前习题`);
      } catch (error) {
        message.error("生成课前习题失败");
        console.error("生成课前习题错误:", error);
      } finally {
        generating.value = false;
      }
    };

    // 原有的生成函数保持不变
    const handleGenerateTeachingDesign = async () => {
      try {
        generating.value = true;
        await createTeachingDesign({ course_id: courseId.value });
        message.success("教学设计生成成功");
        // 刷新教学设计列表
        await fetchTeachingDesigns();
      } catch (error) {
        message.error("生成教学设计失败");
        console.error("生成教学设计错误:", error);
      } finally {
        generating.value = false;
      }
    };

    const showGeneratePreQuestionsConfirm = () => {
      Modal.confirm({
        title: "确认生成",
        content: "确定要根据当前教学内容和目标生成课前习题吗？",
        okText: "确定",
        cancelText: "取消",
        onOk() {
          return handleGeneratePreQuestions();
        },
        onCancel() {
          console.log("取消生成课前习题");
        },
      });
    };

    // 新增状态控制模态框
    const generatingTeachingDesignModal = ref(false);

    // 修改后的生成教学设计函数
    const showGenerateTeachingDesignModal = () => {
      // 先显示生成中模态框
      generatingTeachingDesignModal.value = true;

      // 然后执行生成任务
      handleGenerateTeachingDesign().finally(() => {
        // 完成后关闭模态框
        generatingTeachingDesignModal.value = false;
      });
    };

    const teachingDesigns = ref<TeachingDesign[]>([]);

    const fetchTeachingDesigns = async () => {
      try {
        const designs = await getCourseDesigns(courseId.value);
        teachingDesigns.value = designs;
      } catch (error) {
        message.error("获取教学设计失败");
        console.error("获取教学设计错误:", error);
      }
    };

    const handleDesignClick = (design: any) => {
      // Handle design click (e.g., open detail view)
      console.log("Design clicked:", design);
    };

    onMounted(() => {
      fetchCourseContent();
      fetchTeachingDesigns();
    });

    return {
      generatingTeachingDesignModal,
      content,
      objectives,
      saving,
      generating,
      teachingDesigns,
      handleSaveContent,
      handleGeneratePreQuestions,
      handleGenerateTeachingDesign,
      showGeneratePreQuestionsConfirm,
      showGenerateTeachingDesignModal,
      handleDesignClick,
    };
  },
});
</script>

<style scoped>
.smart-preparation-container {
  display: flex;
  gap: 24px;
  height: calc(100vh - 165px);
}

.content-section {
  flex: 1;
  min-width: 0;
}

.preview-section {
  width: 50%;
}

.content-card {
  height: 100%;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  background-color: #f9fbff;
}
.preview-card {
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;

  background-color: #f9fbff;
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 500;

  .title-icon {
    margin-right: 8px;
    font-size: 18px;
  }
}

.content-textarea {
  width: 100%;
  flex: 1;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.save-btn {
  border-radius: 6px;
  padding: 0 16px;
  height: 36px;
  margin-left: auto;
}

.preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: #fafafa;
  border-radius: 8px;
  border: 1px dashed #d9d9d9;
}

.empty-preview {
  padding: 40px 0;

  .preview-hint {
    color: #8c8c8c;
    margin-top: 8px;
  }
}

/* New styles for generation cards */
.generation-cards {
  margin-top: 24px;
}

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.generation-card {
  border-radius: 8px;
  transition: all 0.3s;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);

  :deep(.ant-card-body) {
    padding: 16px;
  }

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  }
}
.ant-card-cover img {
  height: 80px;
  object-fit: cover;
}
.card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;

  h3 {
    margin: 12px 0 8px;
    font-size: 16px;
    color: #333;
  }

  p {
    margin: 0;
    color: #666;
    font-size: 14px;
  }
}

/* .card-image {
  width: 80px;
  height: 80px;
  object-fit: contain;
  margin-bottom: 12px;
} */

@media (max-width: 992px) {
  .smart-preparation-container {
    flex-direction: column;
    height: auto;
  }

  .preview-section {
    width: 100%;
    min-width: auto;
    margin-top: 24px;
  }

  .cards-container {
    grid-template-columns: 1fr;
  }
}

.mind-map-card {
  margin-top: 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* 新增生成中模态框样式 */
.generating-modal-content {
  text-align: center;
  padding: 20px;
}

.generating-text {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 500;
}

.generating-gif {
  width: 150px;
  height: 150px;
  display: block;
  margin: 0 auto;
}

.generating-tip {
  margin-top: 20px;
  color: #8c8c8c;
  font-size: 14px;
}
</style>
