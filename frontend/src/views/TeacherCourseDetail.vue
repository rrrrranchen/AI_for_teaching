<template>
  <!-- 面包屑导航 -->
  <div class="breadcrumb-section">
    <a-breadcrumb separator=">">
      <a-breadcrumb-item>
        <router-link to="/home/my-class">我的课程</router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item>
        <router-link
          :to="{
            path: `/home/courseclass/${courseclassId}`,
          }"
          >{{ courseclassName }}</router-link
        >
      </a-breadcrumb-item>
      <a-breadcrumb-item>
        {{ courseName }}
      </a-breadcrumb-item>
    </a-breadcrumb>
  </div>

  <div class="course-container">
    <!-- 新增报告标签页 -->
    <a-tabs v-model:activeKey="activeTab" class="custom-tabs">
      <a-tab-pane key="smartpreparation" tab="智能备课">
        <SmartPreparation />
      </a-tab-pane>
      <!-- 原有标签页保持不变 -->
      <a-tab-pane key="questions" tab="题目管理">
        <!-- 题目列表 -->
        <a-card
          :title="`课前预习题目 (${preQuestions.length})`"
          style="margin-bottom: 20px"
        >
          <template #extra>
            <a-space>
              <a-button>添加题目</a-button>
              <a-button
                type="link"
                @click="showDeadlineModal('preview')"
                size="small"
              >
                <template #icon><CalendarOutlined /></template>
                设置截止时间
              </a-button>
              <a-button type="link" @click="toggleCollapse" size="small">
                <template #icon>
                  <UpOutlined v-if="!isCollapsed" />
                  <DownOutlined v-else />
                </template>
                {{ isCollapsed ? "展开" : "收起" }}
              </a-button>
            </a-space>
          </template>

          <a-table
            v-show="!isCollapsed"
            :columns="questionColumns"
            :dataSource="preQuestions"
            :loading="loading"
            rowKey="id"
            :pagination="{ pageSize: 5 }"
          >
            >
            <template #bodyCell="{ column, record }">
              <!-- 新增选择题内容解析 -->
              <template v-if="column.key === 'content'">
                <div v-if="record.type === 'choice'">
                  <div class="question-text">
                    {{ parsedContent(record.content).question }}
                  </div>
                  <div
                    v-for="(option, index) in parsedContent(record.content)
                      .options"
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
                  <a-button
                    size="small"
                    danger
                    @click="confirmDelete(record.id)"
                  >
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

        <!-- 课后练习题目 -->
        <a-card
          :title="`课后练习题目 (${postQuestions.length})`"
          style="margin-bottom: 20px"
        >
          <template #extra>
            <a-space>
              <a-button>添加题目</a-button>
              <a-button
                type="link"
                @click="showDeadlineModal('post')"
                size="small"
              >
                <template #icon><CalendarOutlined /></template>
                设置截止时间
              </a-button>
              <a-button type="link" @click="toggleCollapsePost" size="small">
                <template #icon>
                  <UpOutlined v-if="!isCollapsedPost" />
                  <DownOutlined v-else />
                </template>
                {{ isCollapsedPost ? "展开" : "收起" }}
              </a-button>
            </a-space>
          </template>

          <a-table
            v-show="!isCollapsedPost"
            :columns="postquestionColumns"
            :dataSource="postQuestions"
            :loading="loading"
            rowKey="id"
            :pagination="{ pageSize: 5 }"
          >
            <template #bodyCell="{ column, record }">
              <!-- 复用相同的内容解析逻辑 -->
              <template v-if="column.key === 'content'">
                <div v-if="record.type === 'choice'">
                  <p>{{ parsedContent(record.content).question }}</p>

                  <div
                    v-for="(option, index) in parsedContent(record.content)
                      .options"
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
                  <a-button
                    size="small"
                    danger
                    @click="confirmDelete(record.id)"
                  >
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
      </a-tab-pane>

      <a-tab-pane key="report" tab="课程分析报告">
        <div class="report-container">
          <div class="report-header">
            <a-button
              type="primary"
              @click="handleUpdateCourseReport"
              :loading="updatingReport"
            >
              <sync-outlined />
              {{ courseReport ? "更新报告" : "生成报告" }}
            </a-button>
          </div>

          <div v-if="!courseReport" class="empty-report">
            <a-empty description="暂无分析报告">
              <a-button type="primary" @click="handleUpdateCourseReport">
                立即生成
              </a-button>
            </a-empty>
          </div>

          <!-- 使用markdown渲染容器 -->
          <div v-else class="markdown-content" v-html="renderedReport"></div>
        </div>
      </a-tab-pane>
    </a-tabs>
    <!-- 添加截止时间设置模态框 -->
    <a-modal
      v-model:visible="deadlineModal.visible"
      :title="`设置${
        deadlineModal.type === 'preview' ? '课前' : '课后'
      }截止时间`"
      @ok="handleSetDeadline"
      @cancel="resetDeadlineModal"
    >
      <a-form layout="vertical">
        <a-form-item label="截止时间">
          <a-date-picker
            v-model:value="deadlineModal.datetime"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>
    <!-- 编辑题目模态框 -->
    <a-modal
      v-model:visible="editModalVisible"
      :title="`编辑题目 (ID: ${currentQuestion?.id})`"
      width="60%"
      @ok="handleUpdateQuestion"
      @cancel="resetEditForm"
    >
      <a-form :model="editFormState" layout="vertical">
        <a-form-item label="题目类型">
          <a-select v-model:value="editFormState.type">
            <a-select-option value="choice">选择题</a-select-option>
            <a-select-option value="fill">填空题</a-select-option>
            <a-select-option value="short_answer">简答题</a-select-option>
            <a-select-option value="programming">编程题</a-select-option>
            <a-select-option value="practice">实践题</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="题目内容" required>
          <div id="vditor-content-editor"></div>
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
import {
  defineComponent,
  ref,
  reactive,
  onMounted,
  onBeforeUnmount,
  nextTick,
} from "vue";
import { useRoute } from "vue-router";
import { message, Modal } from "ant-design-vue";
import {
  DeleteOutlined,
  EditOutlined,
  UpOutlined,
  DownOutlined,
  SyncOutlined,
  CalendarOutlined,
} from "@ant-design/icons-vue";
import {
  setPreviewDeadline,
  setPostClassDeadline,
  getCourseDetail,
} from "@/api/course";
import {
  questionApi,
  type Question,
  type QuestionType,
  type QuestionDifficulty,
} from "@/api/questions";
import {
  getCourseAnalysisReport,
  updateCourseReport,
} from "@/api/studentanswer";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import SmartPreparation from "@/components/teachercourse/SmartPreparation.vue";
import Vditor from "vditor";
import "vditor/dist/index.css";

dayjs.extend(utc);

export default defineComponent({
  name: "TeacherCourseDetail",
  components: {
    DeleteOutlined,
    EditOutlined,
    UpOutlined,
    DownOutlined,
    SyncOutlined,
    CalendarOutlined,
    SmartPreparation,
  },
  setup() {
    // 在setup函数中添加
    const vditorInstance = ref<Vditor | null>(null);

    const route = useRoute();
    const courseclassName = ref<string>("");
    const courseclassId = ref<number>(0);
    const courseId = ref<number>(0);
    const courseName = ref<string>("");
    const loading = ref(false);
    const preQuestions = ref<Question[]>([]);
    const postQuestions = ref<Question[]>([]);
    const currentQuestion = ref<Question | null>(null);
    const isCollapsed = ref(true);
    const isCollapsedPost = ref(true);
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value;
    };
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

    // 表格列定义
    const postquestionColumns = [
      {
        title: "知识点",
        dataIndex: "knowledge_point_name",
        key: "knowledge_point_name",
        ellipsis: true,
      },
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
        courseName.value = route.query.courseName as string;
        console.log("课程班信息：", courseclassId.value, courseclassName.value);
        await Promise.all([
          fetchPreQuestions(),
          fetchPostQuestions(),
          fetchDeadlines(),
        ]);
        await loadCourseReport();
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
        preQuestions.value = response;
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

        await questionApi.createPreQuestions(courseId.value);

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

    // 修改showEditModal函数
    const showEditModal = (question: Question) => {
      currentQuestion.value = question;
      editFormState.type = question.type;
      editFormState.correct_answer = question.correct_answer;
      editFormState.difficulty = question.difficulty;

      editModalVisible.value = true;

      nextTick(() => {
        if (vditorInstance.value) {
          vditorInstance.value.destroy();
        }

        vditorInstance.value = new Vditor("vditor-content-editor", {
          value: question.content,
          placeholder: "请输入题目内容（支持Markdown格式）",
          height: 500,
          mode: "sv",
          toolbar: [
            "emoji",
            "headings",
            "bold",
            "italic",
            "strike",
            "link",
            "|",
            "list",
            "ordered-list",
            "check",
            "outdent",
            "indent",
            "|",
            "table",
            "|",
            "undo",
            "redo",
            "|",
            "edit-mode",
            "preview",
            "both",
          ],
          after: () => {
            if (question.content) {
              vditorInstance.value?.setValue(question.content);
            }
          },
        });
      });
    };

    // 修改handleUpdateQuestion函数
    const handleUpdateQuestion = async () => {
      try {
        if (!currentQuestion.value || !vditorInstance.value) return;

        const content = vditorInstance.value.getValue();
        if (!content.trim()) {
          message.warning("请输入题目内容");
          return;
        }

        await questionApi.updateQuestion(currentQuestion.value.id, {
          ...editFormState,
          content: content, // 使用Vditor获取的内容
          difficulty: editFormState.difficulty.toString() as QuestionDifficulty,
        });

        message.success("更新成功");
        resetEditForm();
        await fetchPreQuestions();
        await fetchPostQuestions();
      } catch (error) {
        message.error("更新题目失败");
        console.error("更新题目错误:", error);
      }
    };

    // 修改resetEditForm函数
    const resetEditForm = () => {
      if (vditorInstance.value) {
        vditorInstance.value.destroy();
        vditorInstance.value = null;
      }
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
        // 或者直接重新获取数据
        await fetchPostQuestions();
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
          question: content,
        };
      }
    };

    // 新增报告相关状态
    const activeTab = ref("smartpreparation");
    const courseReport = ref<string | null>(null);
    const updatingReport = ref(false);

    const md: any = new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
      highlight: function (str, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return (
              '<pre class="hljs"><code>' +
              hljs.highlight(str, { language: lang, ignoreIllegals: true })
                .value +
              "</code></pre>"
            );
          } catch (err) {
            console.error(err);
          }
        }
        return (
          '<pre class="hljs"><code>' +
          md.utils.escapeHtml(str) +
          "</code></pre>"
        );
      },
    });

    // 添加渲染后的报告内容
    const renderedReport = ref<string>("");
    // 加载课程报告
    const loadCourseReport = async () => {
      try {
        const { data } = await getCourseAnalysisReport(courseId.value);
        courseReport.value = data.markdown_report;
        renderedReport.value = md.render(courseReport.value || "");
      } catch (error) {
        message.error("获取报告失败");
      }
    };

    // 更新课程报告
    const handleUpdateCourseReport = async () => {
      try {
        updatingReport.value = true;
        const { data } = await updateCourseReport(courseId.value);
        courseReport.value = data.markdown_report;
        message.success("报告更新成功");
        renderedReport.value = md.render(courseReport.value);
      } catch (error) {
        message.error("报告更新失败");
      } finally {
        updatingReport.value = false;
      }
    };

    const previewDeadline = ref<string | null>(null);
    const postClassDeadline = ref<string | null>(null);
    const deadlineModal = reactive({
      visible: false,
      type: "preview" as "preview" | "post",
      datetime: null as string | null,
    });

    // 日期格式化方法（显示 UTC 时间）
    const formatDateTime = (datetime: string | null) => {
      return dayjs.utc(datetime).local().format("YYYY-MM-DD HH:mm:ss");
    };

    // 显示设置模态框
    const showDeadlineModal = (type: "preview" | "post") => {
      deadlineModal.type = type;
      console.log("课前时间", previewDeadline.value);
      deadlineModal.datetime =
        type === "preview"
          ? formatDateTime(previewDeadline.value)
          : formatDateTime(postClassDeadline.value);
      deadlineModal.visible = true;
    };

    // 处理设置截止时间
    const handleSetDeadline = async () => {
      if (!deadlineModal.datetime) {
        message.warning("请选择截止时间");
        return;
      }

      try {
        // 将本地时间转换为 UTC 时间
        const localTime = dayjs(deadlineModal.datetime);
        const utcTime = localTime.utc().format("YYYY-MM-DD HH:mm:ss");

        const apiMethod =
          deadlineModal.type === "preview"
            ? setPreviewDeadline
            : setPostClassDeadline;

        const { deadline } = await apiMethod(courseId.value, utcTime);

        if (deadlineModal.type === "preview") {
          previewDeadline.value = deadline;
        } else {
          postClassDeadline.value = deadline;
        }

        message.success("截止时间设置成功");
        deadlineModal.visible = false;
      } catch (error) {
        message.error("设置失败");
        console.error("设置截止时间错误:", error);
      }
    };

    // 初始化时获取截止时间
    const fetchDeadlines = async () => {
      try {
        const previewRes = await getCourseDetail(courseId.value);

        if (previewRes.preview_deadline !== undefined)
          previewDeadline.value = previewRes.preview_deadline.$date;
        if (previewRes.post_class_deadline !== undefined)
          postClassDeadline.value = previewRes.post_class_deadline.$date;
      } catch (error) {
        console.error("获取截止时间失败:", error);
      }
    };
    onBeforeUnmount(() => {
      if (vditorInstance.value) {
        vditorInstance.value.destroy();
      }
    });
    return {
      courseclassId,
      courseclassName,
      courseId,
      courseName,
      loading,
      preQuestions,
      postQuestions,
      currentQuestion,
      questionColumns,
      postquestionColumns,
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
      activeTab,
      courseReport,
      handleUpdateCourseReport,
      updatingReport,
      renderedReport,
      handleSetDeadline,
      showDeadlineModal,
      formatDateTime,
      // formatDate,
      previewDeadline,
      postClassDeadline,
      deadlineModal,
      resetDeadlineModal() {
        deadlineModal.datetime = null; // 清空已选择的时间
        deadlineModal.visible = false;
      },
    };
  },
});
</script>

<style scoped>
.course-container {
  height: 90vh;
  overflow-y: auto;
  padding-left: 20px;
  padding-right: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.custom-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}

.custom-tabs :deep(.ant-tabs-tab) {
  padding: 12px 24px;
  font-weight: 500;
}

.custom-tabs :deep(.ant-tabs-tab-active) {
  color: #1677ff;
}

/* 面包屑导航样式 */
.ant-breadcrumb {
  padding: 16px 24px; /* 上下间距和左间距 */
  font-size: 16px; /* 字体大小 */
  line-height: 1.5;
  margin-bottom: 10px; /* 下间距 */
}

.ant-breadcrumb a {
  transition: color 0.3s;
  color: #1890ff; /* 链接颜色 */
}

.ant-breadcrumb a:hover {
  color: #40a9ff !important; /* 鼠标悬停时的颜色 */
}

.ant-breadcrumb > span:last-child {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85); /* 当前页面颜色 */
}

/* 教学设计卡片样式 */
.teaching-design-cards {
  display: flex;
  overflow-x: auto;
  gap: 16px;
  padding: 10px 0;
}

.teaching-design-item {
  flex: 0 0 auto;
  width: 280px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
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

/* 新增报告样式 */
.report-container {
  padding: 16px;
  background: #edf6fbcc;
  border: 5px solid #c8e5fb;
  border-radius: 8px;
  min-height: 500px;
}

.report-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.empty-report {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

/* 解决方案2：弹性布局滚动（推荐） */

.markdown-content {
  flex: 1;
  overflow-y: auto;
  max-height: 70vh; /* 根据视口高度自动调整 */
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

/* 通用代码块滚动处理 */
.markdown-content :deep() pre {
  max-width: 100%;
  overflow-x: auto;
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
}
</style>
