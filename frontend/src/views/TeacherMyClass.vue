<template>
  <div class="teacher-class p-6">
    <div class="flex-1"></div>
    <!-- 占位元素 -->
    <div
      style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 20px;
      "
    >
      <div style="font-weight: bold; font-size: 24px; margin-left: 10px">
        我的班级
      </div>
      <div style="display: flex; align-items: center">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索课程班"
          enter-Button
          size="large"
          style="width: 200px; margin-right: 10px"
          @search="handleSearch"
        />
        <a-button type="primary" size="large" @click="showCreateModal">
          <template #icon><plus-outlined /></template>
          新建班级
        </a-button>
      </div>
    </div>

    <a-divider class="!my-4" />
    <!-- 分割线 -->

    <!-- 课程班列表 -->
    <div
      style="
        margin-left: 10px;
        margin-right: 10px;
        height: 89vh;
        overflow-y: auto;
        padding-top: 10px;
        padding-bottom: 20px;
      "
    >
      <a-spin :spinning="loading">
        <a-row
          v-if="filteredClasses.length > 0"
          :gutter="[24, 24]"
          class="mt-6"
        >
          <a-col
            v-for="item in filteredClasses"
            :key="item.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <a-card hoverable class="h-full p-4">
              <template #title>
                <div class="flex justify-between items-center flex-wrap gap-2">
                  <router-link
                    :to="{
                      path: `/home/courseclass/${item.id}`,
                      query: { className: item.name },
                    }"
                    class="text-base font-semibold hover:text-blue-600 transition-colors"
                  >
                    {{ item.name }}
                  </router-link>
                  <div class="flex gap-2">
                    <a-tag
                      color="blue"
                      class="cursor-pointer hover:bg-blue-50 transition-colors"
                      @click="copyInviteCode(item.invite_code)"
                    >
                      邀请码：{{ item.invite_code }}
                      <copy-outlined class="ml-1" />
                    </a-tag>
                    <a-tag color="green"
                      >课程：{{ item.course_count || 0 }}</a-tag
                    >
                  </div>
                </div>
              </template>

              <a-card-meta
                v-if="item.teachers && item.teachers.length > 0"
                :description="item.teachers[0].username || '暂无描述'"
              >
                <template #avatar>
                  <a-avatar
                    v-if="authStore.user?.avatar"
                    :src="'http://localhost:5000/' + authStore.user?.avatar"
                    class="nav-avatar"
                  >
                  </a-avatar>
                  <a-avatar v-else size="small" class="nav-avatar">
                    <UserOutlined />
                  </a-avatar>
                </template>
              </a-card-meta>
            </a-card>
          </a-col>
        </a-row>
        <a-empty v-else description="暂无课程班" class="mt-20" />
      </a-spin>
    </div>

    <!-- 创建/编辑模态框 -->
    <!-- 保持不变 -->
    <a-modal
      v-model:visible="createVisible"
      title="新建课程班"
      @ok="handleCreate"
      :confirm-loading="creating"
    >
      <a-form layout="vertical" :model="newClass" :rules="rules">
        <a-form-item label="课程班名称" name="name">
          <a-input v-model:value="newClass.name" />
        </a-form-item>
        <a-form-item label="课程班描述">
          <a-textarea v-model:value="newClass.description" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { message } from "ant-design-vue";
import {
  PlusOutlined,
  UserOutlined,
  CopyOutlined,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import { getAllCourseclasses, createCourseclass } from "@/api/courseclass";
import type { Courseclass } from "@/api/courseclass";

export default defineComponent({
  name: "TeacherMyClassView",
  components: { PlusOutlined, UserOutlined, CopyOutlined },
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const loading = ref(false);
    const searchKeyword = ref("");
    const courseClasses = ref<Courseclass[]>([]);

    // 创建相关
    const createVisible = ref(false);
    const creating = ref(false);
    const newClass = ref({
      name: "",
      description: "",
    });

    const rules = {
      name: [{ required: true, message: "请输入课程班名称" }],
    };

    const filteredClasses = computed(() => {
      return courseClasses.value.filter((c) =>
        c.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
      );
    });

    const loadData = async () => {
      try {
        loading.value = true;
        courseClasses.value = await getAllCourseclasses();
      } catch (err) {
        message.error("加载失败");
      } finally {
        loading.value = false;
      }
    };

    const handleCreate = async () => {
      try {
        creating.value = true;
        const newItem = await createCourseclass(newClass.value);
        await loadData();
        message.success("创建成功");
        createVisible.value = false;
        newClass.value = { name: "", description: "" };
        router.push("/home/my-class");
      } catch (err) {
        message.error("创建失败");
      } finally {
        creating.value = false;
      }
    };

    // 复制功能实现
    const copyInviteCode = async (code: string) => {
      try {
        await navigator.clipboard.writeText(code);
        message.success("邀请码已复制到剪贴板");
      } catch (err) {
        message.error("复制失败，请手动复制");
      }
    };

    onMounted(loadData);

    return {
      authStore,
      loading,
      searchKeyword,
      filteredClasses,
      createVisible,
      creating,
      newClass,
      rules,
      handleCreate,
      showCreateModal: () => (createVisible.value = true),
      handleSearch: () => loadData(),
      copyInviteCode,
    };
  },
});
</script>
<style scoped>
.teacher-class {
  margin: 0 auto;
  min-height: 100vh;
}

/* 卡片样式 */
.ant-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px !important;
  border: 1px solid #8ef1ea; /* 添加边框 */
  height: 100%;
  display: flex;
  flex-direction: column;
}

.ant-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1) !important;
}

.ant-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* 标题和内容间距 */
.ant-card :deep(.ant-card-head) {
  margin-bottom: 12px;
  min-height: auto;
  padding: 0 16px;
  border-bottom: 0;
}

.ant-card :deep(.ant-card-head-title) {
  padding: 12px 0;
}

/* 描述文本 */
.ant-card-meta-description {
  line-height: 1.6 !important;
  color: #64748b !important;
  margin-bottom: 16px !important;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .teacher-class {
    padding: 1.5rem !important;
  }

  .ant-card {
    margin-bottom: 0 !important;
  }

  .flex.justify-between {
    gap: 12px;
    margin-bottom: 1.5rem;
  }
}

/* 复制图标动画 */
.anticon-copy {
  transition: transform 0.2s;
}

.ant-tag:hover .anticon-copy {
  transform: translateX(2px);
}

/* 滚动条样式 */
/* ::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
} */
</style>
