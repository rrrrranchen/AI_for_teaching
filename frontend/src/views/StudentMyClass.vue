<template>
  <div class="student-class p-6">
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
        <a-button type="primary" size="large" @click="showJoinModal">
          <template #icon><plus-outlined /></template>
          加入课程班
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
                      path: `/home/s-courseclass/${item.id}`,
                      query: { className: item.name },
                    }"
                    class="text-base font-semibold hover:text-blue-600 transition-colors"
                  >
                    {{ item.name }}
                  </router-link>
                  <div class="flex gap-2">
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
                  <!-- 如果有老师信息，展示第一个老师的头像 -->
                  <a-avatar
                    v-if="item.teachers && item.teachers.length > 0"
                    :src="
                      'http://localhost:5000/' + item.teachers[0].avatar ||
                      '/default-avatar.png'
                    "
                    class="text-lg bg-blue-100 p-2 rounded-full"
                  />
                  <!-- 如果没有老师信息，展示默认头像 -->
                  <user-outlined
                    v-else
                    class="text-lg bg-blue-100 p-2 rounded-full"
                  />
                </template>
              </a-card-meta>
            </a-card>
          </a-col>
        </a-row>
        <a-empty v-else description="暂无课程班" class="mt-20" />
      </a-spin>
    </div>

    <!-- 加入模态框 -->
    <a-modal
      v-model:visible="joinVisible"
      title="加入课程班"
      @ok="handleJoin"
      :confirm-loading="joining"
    >
      <a-form layout="vertical">
        <a-form-item label="邀请码" required>
          <a-input
            v-model:value="inviteCode"
            placeholder="请输入老师提供的邀请码"
            allow-clear
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import { message } from "ant-design-vue";
import { PlusOutlined, UserOutlined } from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import {
  getAllCourseclasses,
  joinCourseclassByCode,
  leaveCourseclass,
} from "@/api/courseclass";
import type { Courseclass } from "@/api/courseclass";

export default defineComponent({
  name: "StudentMyClassView",
  components: { PlusOutlined, UserOutlined },
  setup() {
    const authStore = useAuthStore();
    const loading = ref(false);
    const searchKeyword = ref("");
    const courseClasses = ref<Courseclass[]>([]);

    // 加入相关
    const joinVisible = ref(false);
    const joining = ref(false);
    const inviteCode = ref("");

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

    const handleJoin = async () => {
      if (!inviteCode.value) {
        message.warning("请输入邀请码");
        return;
      }
      try {
        joining.value = true;
        const newClass = await joinCourseclassByCode({
          invite_code: inviteCode.value,
        });
        courseClasses.value.unshift(newClass);
        message.success("加入成功");
        joinVisible.value = false;
        inviteCode.value = "";
      } catch (err) {
        message.error("加入失败");
      } finally {
        joining.value = false;
      }
    };

    const handleLeave = async (id: number) => {
      try {
        await leaveCourseclass({ courseclass_id: id });
        courseClasses.value = courseClasses.value.filter((c) => c.id !== id);
        message.success("已退出");
      } catch (err) {
        message.error("操作失败");
      }
    };

    onMounted(loadData);

    return {
      authStore,
      loading,
      searchKeyword,
      filteredClasses,
      joinVisible,
      joining,
      inviteCode,
      handleJoin,
      handleLeave,
      showJoinModal: () => (joinVisible.value = true),
      handleSearch: () => loadData(),
      formatDate: (dateStr: string) => new Date(dateStr).toLocaleDateString(),
    };
  },
});
</script>
<style scoped>
.student-class {
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
  .student-class {
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
</style>
