<template>
  <a-space direction="vertical" :size="16" style="width: 100%">
    <a-space v-if="showLanguageSelector || showThemeSelector" :size="16">
      <a-space v-if="showLanguageSelector" :size="8" align="center">
        <span>语言：</span>
        <a-select
          v-model:value="internalLanguage"
          style="width: 120px"
          size="small"
        >
          <a-select-option value="python">Python</a-select-option>
          <a-select-option value="javascript">JavaScript</a-select-option>
          <a-select-option value="java">Java</a-select-option>
          <a-select-option value="c">C</a-select-option>
          <a-select-option value="cpp">C++</a-select-option>
        </a-select>
      </a-space>

      <a-space v-if="showThemeSelector" :size="8" align="center">
        <span>主题：</span>
        <a-select
          v-model:value="internalTheme"
          style="width: 120px"
          size="small"
        >
          <a-select-option value="dracula">Dracula</a-select-option>
          <a-select-option value="default">Default</a-select-option>
          <a-select-option value="monokai">Monokai</a-select-option>
        </a-select>
      </a-space>
    </a-space>

    <Codemirror
      ref="cmRef"
      v-model:value="internalCode"
      :options="cmOptions"
      border
      :height="height"
      :width="width"
      :tabSize="2"
      @change="handleChange"
      @input="handleInput"
      @ready="handleReady"
    />
  </a-space>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  watch,
  toRefs,
  defineProps,
  defineEmits,
  defineExpose,
} from "vue";
import { Space, Select } from "ant-design-vue";
import Codemirror from "codemirror-editor-vue3";
import type { CmComponentRef } from "codemirror-editor-vue3";

// 引入语言 mode
import "codemirror/mode/javascript/javascript";
import "codemirror/mode/python/python";
import "codemirror/mode/clike/clike";

// 引入主题样式
import "codemirror/theme/monokai.css";
import "codemirror/theme/dracula.css";
import "codemirror/theme/eclipse.css";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  language: {
    type: String,
    default: "python",
  },
  theme: {
    type: String,
    default: "dracula",
  },
  height: {
    type: String,
    default: "400",
  },
  width: {
    type: String,
    default: "100%",
  },
  options: {
    type: Object,
    default: () => ({}),
  },
  showLanguageSelector: {
    type: Boolean,
    default: true,
  },
  showThemeSelector: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits([
  "update:modelValue",
  "update:language",
  "update:theme",
  "change",
  "input",
  "ready",
]);

const { modelValue, language: propLanguage, theme: propTheme } = toRefs(props);

const cmRef = ref<CmComponentRef>();
const internalCode = ref(propLanguage.value);
const internalLanguage = ref(propLanguage.value);
const internalTheme = ref(propTheme.value);

// 同步外部props到内部状态
watch(propLanguage, (newVal) => {
  internalLanguage.value = newVal;
});

watch(propTheme, (newVal) => {
  internalTheme.value = newVal;
});

watch(modelValue, (newVal) => {
  internalCode.value = newVal;
});

// 内部状态变化时通知父组件
watch(internalCode, (newVal) => {
  emit("update:modelValue", newVal);
});

watch(internalLanguage, (newVal) => {
  emit("update:language", newVal);
});

watch(internalTheme, (newVal) => {
  emit("update:theme", newVal);
});

const cmOptions = computed(() => {
  // 处理语言映射
  let mode = internalLanguage.value;
  if (mode === "java") {
    mode = "text/x-java";
  } else if (mode === "c") {
    mode = "text/x-csrc";
  } else if (mode === "cpp") {
    mode = "text/x-c++src";
  }

  return {
    mode: mode,
    theme: internalTheme.value,
    lineNumbers: true,
    autofocus: true,
    fontSize: "24px", // 设置字体大小
    ...props.options,
  };
});
const handleChange = (val: string) => {
  emit("change", val);
};

const handleInput = (val: string) => {
  emit("input", val);
};

const handleReady = () => {
  cmRef.value?.cminstance?.focus();
  emit("ready");
};

// 暴露方法给父组件
defineExpose({
  focus: () => cmRef.value?.cminstance?.focus(),
  getValue: () => internalCode.value,
  setValue: (val: string) => {
    internalCode.value = val;
  },
  getLanguage: () => internalLanguage.value,
  setLanguage: (val: string) => {
    internalLanguage.value = val;
  },
  getTheme: () => internalTheme.value,
  setTheme: (val: string) => {
    internalTheme.value = val;
  },
});
</script>

<style scoped>
/* 可以添加自定义样式 */
</style>
