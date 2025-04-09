<template>
  <div class="teaching-design-edit">
    <!-- 标题和版本选择 -->
    <div class="header">
      <div
        style="
          display: flex;
          justify-content: space-between;
          align-items: center;
        "
      >
        <h2 style="margin: 0">教学设计编辑</h2>
        <a-select
          v-model:value="selectedVersionId"
          style="width: 120px"
          @change="handleVersionChange"
        >
          <a-select-option
            v-for="version in designVersions"
            :key="version.id"
            :value="version.id"
          >
            版本 {{ version.version }}
          </a-select-option>
        </a-select>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-container">
      <!-- 左侧教学计划内容 -->
      <div class="plan-editor">
        <h3>教学计划内容</h3>
        <div id="vditor" class="vditor-container"></div>
      </div>

      <!-- 右侧分析内容 -->
      <div class="analysis-section">
        <h3>分析</h3>
        <a-textarea
          v-model:value="currentVersion.analysis"
          :rows="21"
          placeholder="请输入分析内容"
          class="analysis-textarea"
        />
        <a-button type="primary" @click="saveVersion" :loading="saving">
          保存当前版本
        </a-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import { message } from "ant-design-vue";
import {
  getDesignVersions,
  getDesignVersionDetail,
  updateDesignVersion,
} from "@/api/teachingdesign";
import Vditor from "vditor";
import "vditor/dist/index.css";

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
  setup() {
    const route = useRoute();
    const designId = ref<number>(0);
    const designVersions = ref<TeachingDesignVersion[]>([]);
    const selectedVersionId = ref<number | null>(null);
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
              "devtools",
              "info",
              "help",
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
    const fetchDesignVersions = async () => {
      try {
        const response = await getDesignVersions(designId.value);
        designVersions.value = response.versions;
        if (designVersions.value.length > 0) {
          selectedVersionId.value = designVersions.value[0].id;
          await fetchVersionDetail(selectedVersionId.value!);
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
        initVditor();
        await fetchDesignVersions();
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

    return {
      designId,
      designVersions,
      selectedVersionId,
      currentVersion,
      saving,
      fetchDesignVersions,
      handleVersionChange,
      saveVersion,
    };
  },
});
</script>

<style scoped>
.teaching-design-edit {
  padding: 24px;
  background: #fff;
  height: 100%;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.header {
  margin-bottom: 20px;
  padding: 12px 0;
  border-bottom: 1px solid #e8e8e8;
  height: 8vh;
}

.content-container {
  flex: 1;
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 24px;
  height: 90vh;
}

.plan-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.analysis-section {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.vditor-container {
  flex: 1;
  max-height: 80vh;
}

.analysis-textarea {
  flex: 1;
  margin-top: 5px;
  margin-bottom: 5px;
  height: 500px;
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
</style>
