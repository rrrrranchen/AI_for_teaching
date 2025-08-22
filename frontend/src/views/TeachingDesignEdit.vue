<template>
  <div class="header-container">
    <a-breadcrumb>
      <template #separator>
        <right-outlined class="breadcrumb-sep-icon" />
      </template>
      <a-breadcrumb-item class="breadcrumb-item">
        <router-link to="/home/my-class" class="breadcrumb-link">
          <home-outlined class="breadcrumb-home-icon" />
          <span class="breadcrumb-text">我的课程</span>
        </router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item
        class="breadcrumb-item"
        v-if="courseclassId && courseclassName"
      >
        <router-link
          :to="{ path: `/home/courseclass/${courseclassId}` }"
          class="breadcrumb-link"
        >
          <span class="breadcrumb-text">{{ courseclassName }}</span>
        </router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item class="breadcrumb-item" v-if="courseId && courseName">
        <router-link
          :to="{
            path: `/home/t-course/${courseId}`,
            query: { courseclassId, courseclassName, courseName },
          }"
          class="breadcrumb-link"
        >
          <span class="breadcrumb-text">{{ courseName }}</span>
        </router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item class="breadcrumb-item">
        <span class="breadcrumb-current">{{ design?.title }}</span>
      </a-breadcrumb-item>
    </a-breadcrumb>
    <div class="header-right">
      <!-- <div class="preparation-timer">
        <clock-circle-outlined />
        <span class="timer-text">备课时长: {{ formattedTime }}</span>
      </div> -->
      <a-switch
        checked-children="已公开"
        un-checked-children="未公开"
        :checked="isPublic"
        :loading="togglingVisibility"
        @change="toggleVisibility"
        class="visibility-switch"
      />
    </div>
  </div>
  <div class="teaching-design-edit">
    <a-tabs v-model:activeKey="activeTab" class="custom-tabs">
      >
      <a-tab-pane key="edit" tab="教学设计">
        <!-- 主要内容区域 -->
        <div class="content-container">
          <!-- 左侧教学计划内容 -->
          <div class="plan-editor">
            <div class="head">
              <h3 style="float: left; margin-top: 4px">教学设计内容</h3>
              <div class="version-control" style="float: right">
                <a-button
                  type="primary"
                  @click="saveVersion"
                  :loading="saving"
                  block
                >
                  <template #icon><SaveOutlined /></template>
                  保存修改
                </a-button>
                <a-button
                  type="primary"
                  @click="setDefaultVersion"
                  :loading="settingDefault"
                  :disabled="!selectedVersionId"
                >
                  设为默认
                </a-button>
                <a-select
                  v-model:value="selectedVersionId"
                  style="width: 150px"
                  @change="handleVersionChange"
                >
                  <a-select-option
                    v-for="version in designVersions"
                    :key="version.id"
                    :value="version.id"
                  >
                    <span>
                      版本 {{ version.version }}
                      <a-tag v-if="version.id === defaultVersionId" color="gold"
                        >默认</a-tag
                      >
                    </span>
                  </a-select-option>
                </a-select>
              </div>
            </div>
            <div id="vditor" class="vditor-container"></div>
          </div>
        </div>
      </a-tab-pane>
      <!-- 新增推荐资源标签页 -->
      <a-tab-pane key="recommend" tab="推荐资源">
        <teacher-recommendations :design-id="designId" />
      </a-tab-pane>
      <!-- 新增思维导图标签页 -->
      <a-tab-pane key="mindmap" tab="思维导图">
        <MindMapEditor :design-id="designId" @update="handleMindMapUpdate" />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script lang="ts">
import {
  defineComponent,
  ref,
  onMounted,
  onBeforeUnmount,
  // computed,
} from "vue";
import { useRoute } from "vue-router";
import { message } from "ant-design-vue";
import {
  SaveOutlined,
  ClockCircleOutlined,
  HomeOutlined,
  RightOutlined,
} from "@ant-design/icons-vue";
import {
  getDesignVersions,
  getDesignVersionDetail,
  getDesignDetail,
  updateDesignVersion,
  updateTeachingDesign,
  setDesignVisibility,
  // controlDesignTimer,
  // getDesignTimer,
  type TeachingDesignVersion,
  type TeachingDesign,
} from "@/api/teachingdesign";
import Vditor from "vditor";
import "vditor/dist/index.css";
import TeacherRecommendations from "@/components/TeacherRecommendations.vue";
import MindMapEditor from "@/components/mindmap/MindMapEditor.vue";
import router from "@/router";

export default defineComponent({
  name: "TeachingDesignEdit",
  components: {
    SaveOutlined,
    TeacherRecommendations,
    MindMapEditor,
    // ClockCircleOutlined,
    HomeOutlined,
    RightOutlined,
  },
  setup() {
    const preanalysis = ref(
      "学生整体预习效果良好，对TFLite的核心概念（转换器作用、FlatBuffers优势）理解到位，但在实践细节（Android配置）和完整工作流程记忆上存在提升空间。需在课堂强化转换模型与优化模型的操作演示，并解释`noCompress`配置的技术必要性。"
    );
    const route = useRoute();
    const courseId = ref<number | null>(null);
    const courseName = ref<string | null>(null);
    const courseclassId = ref<number | null>(null);
    const courseclassName = ref<string | null>(null);
    const activeTab = ref("edit");
    const design = ref<TeachingDesign>();
    const designId = ref<number>(0);
    const designVersions = ref<TeachingDesignVersion[]>([]);
    const selectedVersionId = ref<number | null>(null);
    // 新增状态
    const defaultVersionId = ref<number>();
    const currentVersion = ref<TeachingDesignVersion>({
      id: 0,
      design_id: 0,
      version: "",
      plan_content: "",
      analysis: "",
      recommendation_score: 0,
      level: "",
      created_at: "",
      author_id: 0,
    });
    const saving = ref(false);
    const vditor = ref<Vditor | null>(null);

    // 初始化 Vditor
    const initVditor = () => {
      vditor.value = new Vditor("vditor", {
        height: 500,
        placeholder: "请输入Markdown格式的教学计划内容...",
        mode: "wysiwyg",
        preview: {
          hljs: {
            enable: true,
            style: "a11y-dark",
            lineNumber: true, // 显示行号// 可选值如：github、github-dark、monokai、base16/dracula 等
          },
        },
        outline: {
          enable: true,
          position: "left",
        },
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
          "quote",
          "line",
          "code",
          "inline-code",
          "insert-before",
          "insert-after",
          "|",
          "upload",
          "table",
          "|",
          "undo",
          "redo",
          "|",
          "fullscreen",
          "edit-mode",
          "outline",
          "export",
          {
            name: "more",
            toolbar: ["both", "code-theme", "content-theme", "preview"],
          },
        ],
        after: () => {
          if (currentVersion.value.plan_content) {
            vditor.value?.setValue(currentVersion.value.plan_content);
            // 初始化后自动展开大纲
            setTimeout(() => {
              const outlineBtn = document.querySelector(
                '.vditor-toolbar__item[data-type="outline"]'
              );
              if (
                outlineBtn &&
                !outlineBtn.classList.contains("vditor-menu--current")
              ) {
                (outlineBtn as HTMLElement).click();
              }
            }, 100);
          }
        },
        input: (value: string) => {
          currentVersion.value.plan_content = value;
        },
        cache: {
          enable: false,
        },
      });
    };

    // 获取教学设计的所有版本
    // 修改获取教学设计版本的方法
    const fetchDesignVersions = async () => {
      try {
        const response = await getDesignVersions(designId.value);
        designVersions.value = response.versions;
        console.log(response.versions);

        // 设置初始选中版本
        if (defaultVersionId.value) {
          selectedVersionId.value = defaultVersionId.value;
        } else if (designVersions.value.length > 0) {
          selectedVersionId.value = designVersions.value[0].id;
        }

        if (selectedVersionId.value) {
          await fetchVersionDetail(selectedVersionId.value);
        }
      } catch (error) {
        message.error("获取教学设计版本失败");
        console.error("获取教学设计版本错误:", error);
      }
    };

    // 获取单个版本的详细信息
    const fetchVersionDetail = async (versionId: number) => {
      try {
        const response = await getDesignVersionDetail(versionId);
        currentVersion.value = response;
        console.log("具体版本：", response);
        if (vditor.value) {
          vditor.value.setValue(currentVersion.value.plan_content || "");
        }
      } catch (error) {
        message.error("获取版本详情失败");
        console.error("获取版本详情错误:", error);
      }
    };

    // 版本切换
    const handleVersionChange = (versionId: number) => {
      fetchVersionDetail(versionId);
    };

    // 保存当前版本
    const saveVersion = async () => {
      if (!selectedVersionId.value) {
        message.warning("请选择一个版本");
        return;
      }

      try {
        saving.value = true;
        await updateDesignVersion(designId.value, selectedVersionId.value!, {
          plan_content: currentVersion.value.plan_content,
          analysis: currentVersion.value.analysis,
        });
        message.success("保存成功");
      } catch (error) {
        message.error("保存失败");
        console.error("保存错误:", error);
      } finally {
        saving.value = false;
      }
    };

    // 初始化
    onMounted(async () => {
      try {
        const id = Number(route.params.designId);
        if (isNaN(id)) throw new Error("无效的教学设计ID");
        designId.value = id;
        defaultVersionId.value = Number(route.query.default_version_id);
        // 读取用于面包屑的路由信息
        courseId.value = route.query.courseId
          ? Number(route.query.courseId)
          : null;
        courseName.value = (route.query.courseName as string) || null;
        courseclassId.value = route.query.courseclassId
          ? Number(route.query.courseclassId)
          : null;
        courseclassName.value = (route.query.courseclassName as string) || null;
        initVditor();
        await fetchDesignDetail(); // 新增
        await fetchDesignVersions();
      } catch (err) {
        message.error("初始化失败");
        console.error("初始化错误:", err);
      }
      // await initTimer();
    });

    // 组件卸载前销毁 Vditor 实例
    onBeforeUnmount(() => {
      if (vditor.value) {
        vditor.value.destroy();
      }
    });

    // 新增状态
    const settingDefault = ref(false);

    // 修改设置默认版本方法
    const setDefaultVersion = async () => {
      if (!selectedVersionId.value) return;

      try {
        settingDefault.value = true;
        const updatedDesign = await updateTeachingDesign(designId.value, {
          default_version_id: selectedVersionId.value,
        });

        // 更新本地默认版本状态
        defaultVersionId.value = updatedDesign.default_version_id;
        message.success("默认版本设置成功");
      } catch (error) {
        message.error("设置默认版本失败");
        console.error("设置默认版本错误:", error);
      } finally {
        settingDefault.value = false;
      }
    };

    // 新增处理思维导图更新的方法
    const handleMindMapUpdate = async () => {
      message.success("思维导图已更新");
    };

    // 在 setup() 中添加以下代码
    const isPublic = ref(false);
    const togglingVisibility = ref(false);

    // 获取当前教学设计的状态
    const fetchDesignDetail = async () => {
      try {
        design.value = await getDesignDetail(designId.value);
        isPublic.value = design.value.is_public;
        console.log(
          "获取教学设计详情成功:",
          isPublic.value,
          design.value.is_public
        );
      } catch (error) {
        message.error("获取教学设计详情失败");
      }
    };

    // 切换可见性状态
    const toggleVisibility = async (checked: boolean) => {
      try {
        togglingVisibility.value = true;
        await setDesignVisibility(designId.value, {
          is_public: checked,
          is_recommended: checked, // 同时设置推荐状态
        });
        isPublic.value = !isPublic.value;
        message.success(checked ? "已设为公开" : "已设为私有");
      } catch (error) {
        message.error("状态切换失败");
        // 恢复原来的状态
        isPublic.value = !checked;
      } finally {
        togglingVisibility.value = false;
      }
    };

    return {
      preanalysis,
      design,
      designId,
      courseId,
      courseName,
      courseclassId,
      courseclassName,
      activeTab,
      designVersions,
      selectedVersionId,
      currentVersion,
      saving,
      fetchDesignVersions,
      handleVersionChange,
      saveVersion,
      settingDefault,
      defaultVersionId,
      setDefaultVersion,
      handleMindMapUpdate,
      isPublic,
      togglingVisibility,
      toggleVisibility,
      // formattedTime,
      ClockCircleOutlined,
    };
  },
});
</script>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
}

.breadcrumb-link {
  height: 30px;
  display: inline-flex;
  align-items: center;
  color: #1677ff;
  padding: 10px 16px;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f7ff 100%);
  border: 1px solid #c8e5fb;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.12);
}

.breadcrumb-link:hover {
  color: #0958d9;
}

.breadcrumb-home-icon {
  font-size: 14px;
  margin-right: 6px;
}

.breadcrumb-sep-icon {
  color: #8c8c8c;
  font-size: 12px;
}

.breadcrumb-text {
  font-weight: 500;
}

.breadcrumb-current {
  height: 30px;
  display: inline-flex;
  align-items: center;
  padding: 10px 16px;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f7ff 100%);
  border: 1px solid #c8e5fb;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.12);
  font-weight: 600;
  color: #1d2129;
}

.visibility-switch {
  margin-top: 24px;
  margin-right: 24px;
}
/* 面包屑导航样式 */
.ant-breadcrumb {
  padding-top: 16px;
  padding-left: 24px; /* 上下间距和左间距 */
  font-size: 16px; /* 字体大小 */
  line-height: 1.5;
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

.teaching-design-edit {
  background: inherit;
  padding: 15px;
  height: 100%;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.custom-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 8px;
}

.custom-tabs :deep(.ant-tabs-tab) {
  padding: 12px 24px;
  font-weight: 500;
}

.custom-tabs :deep(.ant-tabs-tab-active) {
  color: #1677ff;
}

.content-container {
  gap: 24px;
  height: 90vh;
}

.plan-editor {
  padding: 10px;
  display: flex;
  flex-direction: column;
  height: 84vh;
  border-radius: 8px;
  background-color: #e2f4ff;
}

.version-control {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.ant-tag {
  margin-left: 8px;
  vertical-align: middle;
}

.vditor-container {
  flex: 1;
  max-height: 80vh;
}

.footer {
  margin-top: 24px;
  text-align: right;
  padding: 16px 0;
  border-top: 1px solid #e8e8e8;
}

h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: rgba(0, 0, 0, 0.85);
}

/* 新增样式 */
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.preparation-timer {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  color: rgba(0, 0, 0, 0.85);
  background: #f0f9ff;
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid #d9f7be;
}

.timer-text {
  font-weight: 600;
}
</style>
