<template>
  <a-breadcrumb separator=">">
    <a-breadcrumb-item>
      <router-link to="/home/smart-preparation">智慧备课</router-link>
    </a-breadcrumb-item>
    <a-breadcrumb-item>{{ designTitle }}</a-breadcrumb-item>
  </a-breadcrumb>
  <div class="teaching-design-edit">
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="edit" tab="教学设计">
        <!-- 主要内容区域 -->
        <div class="content-container">
          <!-- 左侧教学计划内容 -->
          <div class="plan-editor">
            <h3>教学设计内容</h3>
            <div id="vditor" class="vditor-container"></div>
          </div>

          <div class="analysis-section">
            <div class="version-control">
              <a-button
                type="primary"
                @click="saveVersion"
                :loading="saving"
                block
              >
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
                style="width: 140px"
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
            <!-- 上半部分：课前预习水平分析 -->
            <div class="analysis-top">
              <h3>课前预习水平分析</h3>
              <a-textarea
                v-model:value="currentVersion.analysis"
                :rows="8"
                placeholder="请输入分析内容"
                class="analysis-textarea"
              />
            </div>

            <!-- 下半部分：PPT资源 -->
            <div class="ppt-resources">
              <h3>教学设计PPT</h3>
              <a-empty
                v-if="pptResources.length === 0"
                description="暂无PPT资源"
              >
                <a-button type="primary" @click="showTemplateModal">
                  <template #icon><file-ppt-outlined /></template>
                  生成PPT
                </a-button>
              </a-empty>

              <a-spin :spinning="loadingPPT">
                <div v-if="pptResources.length > 0" class="ppt-list">
                  <a-card
                    v-for="resource in pptResources"
                    :key="resource.id"
                    class="ppt-card"
                  >
                    <template #actions>
                      <a-button type="link" @click="downloadPPT(resource)">
                        下载
                      </a-button>
                      <a
                        target="_blank"
                        :href="getPPTPreviewUrl(resource)"
                        class="preview-link"
                      >
                        预览
                      </a>
                    </template>
                    <div class="ppt-card-content">
                      <img
                        src="@/assets/icons8-ms-powerpoint.svg"
                        alt="PPT Icon"
                        class="ppt-icon"
                      />
                      <a-card-meta
                        :title="resource.title"
                        :description="resource.description"
                      ></a-card-meta>
                    </div>
                  </a-card>
                </div>
              </a-spin>
            </div>
          </div>
        </div>
        <!-- PPT模板选择模态框 -->
        <!-- 修改模板展示部分的模板 -->
        <!-- 模态框部分 -->
        <a-modal
          v-model:visible="showPPTModal"
          title="选择PPT模板"
          @ok="handleGeneratePPT"
          :confirm-loading="generatingPPT"
          :width="800"
          :body-style="{
            padding: '16px',
            maxHeight: '60vh',
            overflowY: 'auto',
          }"
          wrap-class-name="fixed-modal"
        >
          <div class="template-grid">
            <div
              v-for="template in pptTemplates"
              :key="template.id"
              class="template-item"
              :class="{ selected: selectedTemplate?.id === template.id }"
              @click="selectTemplate(template)"
            >
              <a-image
                :src="'http://localhost:5000/' + template.image_url"
                class="template-preview"
                :preview="false"
              />
              <div class="template-name">{{ template.name }}</div>
            </div>
          </div>
        </a-modal>
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
import { defineComponent, ref, onMounted, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import { message } from "ant-design-vue";
import { FilePptOutlined } from "@ant-design/icons-vue";
import {
  getDesignVersions,
  getDesignVersionDetail,
  updateDesignVersion,
  updateTeachingDesign,
} from "@/api/teachingdesign";
import Vditor from "vditor";
import "vditor/dist/index.css";
import {
  getDesignVersionResources,
  generateTeachingPPT,
  getAllPPTTemplates,
} from "@/api/resource";
import type { PPTTemplate, MultimediaResource } from "@/api/resource";
import TeacherRecommendations from "@/components/TeacherRecommendations.vue";
import MindMapEditor from "@/components/MindMapEditor.vue";

export interface TeachingDesignVersion {
  id: number;
  design_id: number;
  version: string;
  plan_content?: string;
  analysis?: string;
  recommendation_score: number;
  level: string;
  created_at: string;
  updated_at?: string;
  author_id: number;
}

export default defineComponent({
  name: "TeachingDesignEdit",
  components: {
    FilePptOutlined,
    TeacherRecommendations,
    MindMapEditor,
  },
  setup() {
    const route = useRoute();
    const activeTab = ref("edit");
    const designId = ref<number>(0);
    const designTitle = ref<string>("");
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
          {
            name: "more",
            toolbar: [
              "both",
              "code-theme",
              "content-theme",
              "export",
              "outline",
              "preview",
            ],
          },
        ],
        after: () => {
          if (currentVersion.value.plan_content) {
            vditor.value?.setValue(currentVersion.value.plan_content);
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
      fetchPPTResources(versionId);
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
        designTitle.value = route.query.title as string;
        initVditor();
        await fetchDesignVersions();
        await fetchPPTResources(defaultVersionId.value);
      } catch (err) {
        message.error("初始化失败");
        console.error("初始化错误:", err);
      }
    });

    // 组件卸载前销毁 Vditor 实例
    onBeforeUnmount(() => {
      if (vditor.value) {
        vditor.value.destroy();
      }
    });

    // 新增PPT相关状态
    const pptResources = ref<MultimediaResource[]>([]);
    const pptTemplates = ref<PPTTemplate[]>([]);
    const showPPTModal = ref(false);
    const selectedTemplate = ref<PPTTemplate | null>(null);
    const generatingPPT = ref(false);
    const loadingPPT = ref(false);

    // 获取PPT资源
    const fetchPPTResources = async (versionId: number) => {
      try {
        loadingPPT.value = true;
        pptResources.value = await getDesignVersionResources(versionId);
      } catch (err) {
        message.error("获取PPT资源失败");
      } finally {
        loadingPPT.value = false;
      }
    };

    // 获取PPT模板
    const fetchPPTTemplates = async () => {
      try {
        pptTemplates.value = await getAllPPTTemplates();
        console.log("所有模板内容：", pptTemplates.value);
      } catch (err) {
        message.error("获取模板失败");
      }
    };

    // 显示模板选择模态框
    const showTemplateModal = async () => {
      if (pptTemplates.value.length === 0) {
        await fetchPPTTemplates();
      }
      showPPTModal.value = true;
    };

    // 选择模板
    const selectTemplate = (template: PPTTemplate) => {
      selectedTemplate.value = template;
    };

    // 生成PPT
    const handleGeneratePPT = async () => {
      if (!selectedTemplate.value) {
        message.warning("请选择模板");
        return;
      }

      try {
        generatingPPT.value = true;
        await generateTeachingPPT(
          currentVersion.value.design_id, // 使用课程ID
          currentVersion.value.id, // 使用版本ID
          selectedTemplate.value.id,
          `教学设计-${currentVersion.value.version}版`
        );
        message.success("PPT生成任务已开始，请稍后刷新查看");
        showPPTModal.value = false;
        await fetchPPTResources(currentVersion.value.id);
      } catch (err) {
        message.error("生成失败");
      } finally {
        generatingPPT.value = false;
      }
    };

    // 下载PPT
    const downloadPPT = (resource: MultimediaResource) => {
      console.log("下载资源ppt:", resource);
      window.open("http://localhost:5000/" + resource.storage_path, "_blank");
    };
    // 获取PPT预览URL
    const getPPTPreviewUrl = (resource: MultimediaResource) => {
      const pptUrl = encodeURIComponent(
        `http://localhost:5000/${resource.storage_path}`
      );
      return `http://view.officeapps.live.com/op/view.aspx?src=${pptUrl}`;
    };
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

    return {
      designId,
      activeTab,
      designTitle,
      designVersions,
      selectedVersionId,
      currentVersion,
      saving,
      fetchDesignVersions,
      handleVersionChange,
      saveVersion,

      //ppt
      pptResources,
      pptTemplates,
      showPPTModal,
      selectedTemplate,
      generatingPPT,
      loadingPPT,
      showTemplateModal,
      selectTemplate,
      handleGeneratePPT,
      downloadPPT,
      getPPTPreviewUrl,
      settingDefault,
      defaultVersionId,
      setDefaultVersion,
      handleMindMapUpdate,
    };
  },
});
</script>

<style scoped>
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

.content-container {
  flex: 1;
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 24px;
  height: 90vh;
}

.plan-editor {
  padding: 10px;
  display: flex;
  flex-direction: column;
  height: 84vh;
  border-radius: 8px;
  background-color: #f8f6ea;
}

.analysis-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
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

.analysis-textarea {
  flex: 1;
  margin-top: 5px;
  margin-bottom: 5px;
  height: 35vh;
  resize: none;
}

.footer {
  margin-top: 24px;
  text-align: right;
  padding: 16px 0;
  border-top: 1px solid #e8e8e8;
}

h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: rgba(0, 0, 0, 0.85);
}

/* ppt */

.analysis-top {
  flex: 1;
}

.ppt-resources {
  flex: 1;
  min-height: 300px;
}

.ppt-list {
  display: grid;
  gap: 16px;
}

.ppt-card {
  transition: box-shadow 0.3s;
}

.ppt-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* PPT卡片内容样式 */
.ppt-card-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* PPT图标样式 */
.ppt-icon {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

/* 卡片元信息样式调整 */
:deep(.ppt-card .ant-card-meta) {
  flex: 1;
}

:deep(.ppt-card .ant-card-meta-title) {
  margin-bottom: 4px;
}

:deep(.ppt-card .ant-card-meta-description) {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

/* 修改模态框样式 */
:deep(.ant-modal) {
  max-width: 800px;
}

:deep(.ant-modal-body) {
  max-height: 60vh;
  overflow-y: auto;
  padding: 16px;
}

/* 模板网格布局 */
.template-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 8px;
}

/* 模板项样式 */
.template-item {
  position: relative;
  border: 2px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
  aspect-ratio: 1/0.7;
}

.template-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.template-item.selected {
  border-color: #1890ff;
  background: rgba(24, 144, 255, 0.05);
}

/* 图片预览 */
.template-preview {
  width: 100%;
  height: 160px;
  object-fit: cover;
  background: #fafafa;
}

/* 模板名称 */
.template-name {
  padding: 8px;
  font-size: 12px;
  text-align: center;
  color: rgba(0, 0, 0, 0.85);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 固定模态框样式 */
:deep(.fixed-modal) {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin: 0;
}

:deep(.fixed-modal .ant-modal-content) {
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

:deep(.fixed-modal .ant-modal-body) {
  flex: 1;
  overflow: hidden;
}
</style>
