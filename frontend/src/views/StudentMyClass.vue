<template>
  <div class="student-class p-4">
    <!-- 搜索和加入 -->
    <div class="flex justify-between mb-6">
      <a-input-search
        v-model:value="searchKeyword"
        placeholder="搜索已加入课程班"
        style="width: 300px"
        @search="handleSearch"
      />
      <a-button type="primary" @click="showJoinModal">
        <template #icon><plus-outlined /></template>
        加入课程班
      </a-button>
    </div>

    <!-- 课程班列表 -->
    <a-list :data-source="filteredClasses" :loading="loading">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-card hoverable class="w-full">
            <template #title>
              <router-link :to="`/courseclass/${item.id}`">{{
                item.name
              }}</router-link>
            </template>

            <a-card-meta>
              <template #description>
                <div class="space-y-2">
                  <p>{{ item.description || "暂无描述" }}</p>
                  <div class="flex items-center gap-2 text-sm text-gray-500">
                    <span
                      >教师：{{
                        item.teachers.map((t: any) => t.username).join(", ")
                      }}</span
                    >
                    <a-divider type="vertical" />
                    <span>创建时间：{{ formatDate(item.created_at) }}</span>
                  </div>
                </div>
              </template>
            </a-card-meta>

            <template #actions>
              <a-popconfirm
                title="确定要退出这个课程班吗？"
                @confirm="handleLeave(item.id)"
              >
                <a-button type="link" danger>退出</a-button>
              </a-popconfirm>
            </template>
          </a-card>
        </a-list-item>
      </template>
    </a-list>

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
import { PlusOutlined } from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import {
  getAllCourseclasses,
  joinCourseclassByCode,
  leaveCourseclass,
} from "@/api/courseclass";
import type { Courseclass } from "@/api/courseclass";

export default defineComponent({
  name: "StudentMyClassView",
  components: { PlusOutlined },
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
