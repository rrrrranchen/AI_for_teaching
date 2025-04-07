<template>
  <div class="course-container">
    <!-- 面包屑导航 -->
    <div class="breadcrumb-section">
      <a-breadcrumb separator=">">
        <a-breadcrumb-item>
          <router-link to="/home/my-class">我的班级</router-link>
        </a-breadcrumb-item>
        <a-breadcrumb-item>
          <router-link
            :to="{
              path: `/home/courseclass/${courseclassId}`,
            }"
            >{{ courseclassName }}</router-link
          >
        </a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <!-- 题目列表 -->
    <a-card
      :title="`课前预习题目 (${preQuestions.length})`"
      style="margin-bottom: 20px"
    >
      <template #extra>
        <a-button type="link" @click="toggleCollapse" size="small">
          <template #icon>
            <UpOutlined v-if="!isCollapsed" />
            <DownOutlined v-else />
          </template>
          {{ isCollapsed ? "展开" : "收起" }}
        </a-button>
      </template>

      <a-table
        v-show="!isCollapsed"
        :columns="questionColumns"
        :dataSource="preQuestions"
        :loading="loading"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <!-- 新增选择题内容解析 -->
          <template v-if="column.key === 'content'">
            <div v-if="record.type === 'choice'">
              <div class="question-text">
                {{ parsedContent(record.content).question }}
              </div>
              <div
                v-for="(option, index) in parsedContent(record.content).options"
                :key="index"
                class="option-item"
              >
                {{ option }}
              </div>
            </div>
            <template v-else>
              {{ record.content }}
            </template>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" @click="showEditModal(record)">
                <template #icon><EditOutlined /></template>
              </a-button>
              <a-button size="small" danger @click="confirmDelete(record.id)">
                <template #icon><DeleteOutlined /></template>
              </a-button>
              <a-switch
                checked-children="已发布"
                un-checked-children="未发布"
                :checked="record.is_public"
                @change="(checked: any) => togglePublic(record.id, checked)"
              />
            </a-space>
          </template>
          <template v-else-if="column.key === 'difficulty'">
            <a-rate :value="Number(record.difficulty)" disabled />
          </template>
        </template>
      </a-table>
    </a-card>

    <a-card :title="`教学设计`" style="margin-bottom: 20px"></a-card>

    <a-card
      :title="`课后练习题目 (${postQuestions.length})`"
      style="margin-bottom: 20px"
    >
      <template #extra>
        <a-button type="link" @click="toggleCollapsePost" size="small">
          <template #icon>
            <UpOutlined v-if="!isCollapsedPost" />
            <DownOutlined v-else />
          </template>
          {{ isCollapsedPost ? "展开" : "收起" }}
        </a-button>
      </template>

      <a-table
        v-show="!isCollapsedPost"
        :columns="questionColumns"
        :dataSource="postQuestions"
        :loading="loading"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <!-- 复用相同的内容解析逻辑 -->
          <template v-if="column.key === 'content'">
            <div v-if="record.type === 'choice'">
              <div class="question-text">
                {{ parsedContent(record.content).question }}
              </div>
              <div
                v-for="(option, index) in parsedContent(record.content).options"
                :key="index"
                class="option-item"
              >
                {{ option }}
              </div>
            </div>
            <template v-else>
              {{ record.content }}
            </template>
          </template>

          <template v-if="column.key === 'actions'">
            <a-space>
              <!-- 复用相同的操作按钮 -->
              <a-button size="small" @click="showEditModal(record)">
                <template #icon><EditOutlined /></template>
              </a-button>
              <a-button size="small" danger @click="confirmDelete(record.id)">
                <template #icon><DeleteOutlined /></template>
              </a-button>
              <a-switch
                checked-children="已发布"
                un-checked-children="未发布"
                :checked="record.is_public"
                @change="(checked: any) => togglePublic(record.id, checked)"
              />
            </a-space>
          </template>

          <template v-else-if="column.key === 'difficulty'">
            <a-rate :value="Number(record.difficulty)" disabled />
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 编辑题目模态框 -->
    <a-modal
      v-model:visible="editModalVisible"
      :title="`编辑题目 (ID: ${currentQuestion?.id})`"
      @ok="handleUpdateQuestion"
      @cancel="resetEditForm"
    >
      <a-form :model="editFormState" layout="vertical">
        <a-form-item label="题目类型">
          <a-select v-model:value="editFormState.type">
            <a-select-option value="choice">选择题</a-select-option>
            <a-select-option value="fill">填空题</a-select-option>
            <a-select-option value="short_answer">简答题</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="题目内容" required>
          <a-textarea v-model:value="editFormState.content" rows="4" />
        </a-form-item>
        <a-form-item label="正确答案" required>
          <a-textarea v-model:value="editFormState.correct_answer" rows="4" />
        </a-form-item>
        <a-form-item label="难度">
          <a-rate v-model:value="editFormState.difficulty" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted } from "vue";
import { useRoute } from "vue-router";
import { message, Modal } from "ant-design-vue";
import {
  DeleteOutlined,
  EditOutlined,
  UpOutlined,
  DownOutlined,
} from "@ant-design/icons-vue";
import {
  questionApi,
  type Question,
  type QuestionType,
  type QuestionDifficulty,
} from "@/api/questions";

export default defineComponent({
  name: "TeacherCourseDetail",
  components: { DeleteOutlined, EditOutlined, UpOutlined, DownOutlined },
  setup() {
    const route = useRoute();
    const courseclassName = ref<string>("");
    const courseclassId = ref<number>(0);
    const courseId = ref<number>(0);
    const loading = ref(false);
    const preQuestions = ref<Question[]>([]);
    const currentQuestion = ref<Question | null>(null);
    const postQuestions = ref<Question[]>([]);
    const isCollapsedPost = ref(true);

    // 新增折叠方法
    const toggleCollapsePost = () => {
      isCollapsedPost.value = !isCollapsedPost.value;
    };

    // 新增获取课后习题方法
    const fetchPostQuestions = async () => {
      try {
        loading.value = true;
        const response = await questionApi.getPostQuestions(courseId.value);
        postQuestions.value = response;
      } catch (error) {
        message.error("获取课后题目失败");
        console.error("获取课后题目错误:", error);
      } finally {
        loading.value = false;
      }
    };

    const isCollapsed = ref(false);
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value;
    };

    // 模态框状态
    const addModalVisible = ref(false);
    const editModalVisible = ref(false);

    // 表单状态
    const addFormState = reactive({
      content: "",
    });

    const editFormState = reactive({
      type: "choice" as QuestionType,
      content: "",
      correct_answer: "",
      difficulty: "3" as QuestionDifficulty,
    });

    // 表格列定义
    const questionColumns = [
      {
        title: "题目内容",
        dataIndex: "content",
        key: "content",
        ellipsis: true,
      },
      {
        title: "答案",
        dataIndex: "correct_answer",
        key: "correct_answer",
        ellipsis: true,
      },
      {
        title: "难度",
        key: "difficulty",
        width: 180,
      },
      {
        title: "操作",
        key: "actions",
        width: 180,
      },
    ];

    // 初始化
    onMounted(async () => {
      try {
        const id = Number(route.params.courseId);
        if (isNaN(id)) throw new Error("无效的课程ID");
        courseId.value = id;
        courseclassId.value = Number(route.query.courseclassId);
        courseclassName.value = route.query.courseclassName as string;
        console.log("课程班信息：", courseclassId.value, courseclassName.value);
        await Promise.all([fetchPreQuestions(), fetchPostQuestions()]); // 并行请求
      } catch (err) {
        message.error("初始化失败");
        console.error("初始化错误:", err);
      }
    });

    // 获取预习题目列表
    const fetchPreQuestions = async () => {
      try {
        loading.value = true;
        const response = await questionApi.getPreQuestions(courseId.value);
        console.log("获取到的题目数据:", response); // 添加这行

        preQuestions.value = response;
        console.log("赋值后的preQuestions:", preQuestions.value); // 3. 检查赋值结果
      } catch (error) {
        message.error("获取题目列表失败");
        console.error("获取题目列表错误:", error);
      } finally {
        loading.value = false;
      }
    };

    // 添加预习题目
    const handleAddPreQuestion = async () => {
      try {
        if (!addFormState.content.trim()) {
          message.warning("请输入题目内容");
          return;
        }

        await questionApi.createPreQuestions(courseId.value, {
          content: addFormState.content,
        });

        message.success("添加成功");
        resetAddForm();
        await fetchPreQuestions();
      } catch (error) {
        message.error("添加题目失败");
        console.error("添加题目错误:", error);
      }
    };

    // 重置添加表单
    const resetAddForm = () => {
      addFormState.content = "";
      addModalVisible.value = false;
    };

    // 显示编辑模态框
    const showEditModal = (question: Question) => {
      currentQuestion.value = question;
      editFormState.type = question.type;
      editFormState.content = question.content;
      editFormState.correct_answer = question.correct_answer;
      editFormState.difficulty = question.difficulty;
      editModalVisible.value = true;
    };

    // 更新题目
    const handleUpdateQuestion = async () => {
      try {
        if (!currentQuestion.value) return;

        await questionApi.updateQuestion(currentQuestion.value.id, {
          ...editFormState,
          difficulty: editFormState.difficulty.toString() as QuestionDifficulty,
        });

        message.success("更新成功");
        resetEditForm();
        await fetchPreQuestions();
      } catch (error) {
        message.error("更新题目失败");
        console.error("更新题目错误:", error);
      }
    };

    // 重置编辑表单
    const resetEditForm = () => {
      currentQuestion.value = null;
      editModalVisible.value = false;
    };

    // 删除题目确认
    const confirmDelete = (questionId: number) => {
      Modal.confirm({
        title: "确认删除",
        content: "确定要删除这个题目吗？此操作不可撤销。",
        okText: "确认",
        okType: "danger",
        cancelText: "取消",
        onOk: async () => {
          try {
            await questionApi.deleteQuestion(questionId);
            message.success("删除成功");
            await fetchPreQuestions();
          } catch (error) {
            message.error("删除题目失败");
            console.error("删除题目错误:", error);
          }
        },
      });
    };

    // 切换题目公开状态
    const togglePublic = async (questionId: number, isPublic: boolean) => {
      try {
        await questionApi.toggleQuestionPublic(questionId, isPublic);
        message.success("状态更新成功");
        await fetchPreQuestions();
      } catch (error) {
        message.error("状态更新失败");
        console.error("状态更新错误:", error);
      }
    };

    const parsedContent = (content: string) => {
      try {
        return JSON.parse(content);
      } catch (e) {
        return {
          question: "内容格式错误",
          options: ["无效的题目数据"],
        };
      }
    };
    return {
      courseclassId,
      courseclassName,
      courseId,
      loading,
      preQuestions,
      postQuestions,
      currentQuestion,
      questionColumns,
      addModalVisible,
      editModalVisible,
      addFormState,
      editFormState,
      isCollapsed,
      isCollapsedPost,
      toggleCollapse,
      toggleCollapsePost,
      handleAddPreQuestion,
      resetAddForm,
      showEditModal,
      handleUpdateQuestion,
      resetEditForm,
      confirmDelete,
      togglePublic,
      parsedContent,
    };
  },
});
</script>

<style scoped>
/* 外层滚动容器样式 */
.course-container {
  height: 100vh; /* 根据实际布局调整 */
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.breadcrumb-section {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
}

/* 卡片包裹层 */
.card-wrapper {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

/* 卡片样式 */
.course-card {
  border-radius: 8px;
}

/* 滚动条美化 */
.course-container::-webkit-scrollbar {
  width: 6px;
}

.course-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.course-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.course-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 新增样式优化显示 */
.question-text {
  font-weight: 500;
  margin-bottom: 8px;
}
.option-item {
  margin: 4px 0;
  padding-left: 12px;
  position: relative;
}
.option-item::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #666;
}
/* 优化折叠按钮样式 */
:deep(.ant-card-head-title) {
  font-weight: 500;
  font-size: 16px;
}

:deep(.ant-card-extra) {
  padding: 12px 0;
}
</style>
