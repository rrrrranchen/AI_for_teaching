<template>
  <div ref="docmeeContainer" class="docmee-container"></div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { DocmeeUI, CreatorType } from "@docmee/sdk-ui"; // 导入相关依赖

const docmeeContainer = ref<HTMLDivElement | null>(null);

onMounted(() => {
  if (!docmeeContainer.value) return;

  new DocmeeUI({
    container: docmeeContainer.value, // 挂载容器
    token: "ak_s4A1dDT5E33FEAkgDU", // 替换为你自己的 token
    page: "creator", // 页面类型：'creator'（创建页面）、'dashboard'（文档列表）、'editor'（编辑页面）、'customTemplate'（自定义模板）
    creatorVersion: "v2", // 创建 PPT 的版本选择：'v1'（旧版）、'v2'（新版）
    mode: "light", // 主题模式：'light'（亮色模式）、'dark'（暗色模式）
    lang: "zh", // 语言：'zh'（中文）、'en'（英文）等
    padding: "40px 20px 40px",
    creatorData: {
      type: CreatorType.AI_GEN, // 使用 CreatorType 枚举
    },
    onMessage: (message: any) => {
      console.log("收到消息：", message);
      // 处理事件
      if (message.type === "invalid-token") {
        console.log("token 认证错误");
      } else if (message.type === "beforeGenerate") {
        console.log("即将生成 PPT", message.data);
      }
    },
  });
});
</script>

<style scoped>
.docmee-container {
  width: 100%;
  height: 100vh; /* 根据需要调整高度 */
}
</style>
