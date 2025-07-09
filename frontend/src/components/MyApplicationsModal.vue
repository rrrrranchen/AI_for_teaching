<template>
  <!-- 在页面顶部右侧添加这个按钮 -->
  <div class="my-applications-btn">
    <a-button type="primary" @click="showModal">
      <template #icon><solution-outlined /></template>
      我的申请
      <a-badge
        v-if="pendingCount > 0"
        :count="pendingCount"
        :offset="[-10, 0]"
      />
    </a-button>

    <!-- 申请记录模态框 -->
    <a-modal
      v-model:visible="visible"
      title="我的申请记录"
      width="800px"
      :footer="null"
    >
      <div class="applications-container">
        <div class="applications-header">
          <a-radio-group v-model:value="filterStatus" button-style="solid">
            <a-radio-button value="all">全部</a-radio-button>
            <a-radio-button value="pending">待处理</a-radio-button>
            <a-radio-button value="approved">已通过</a-radio-button>
            <a-radio-button value="rejected">已拒绝</a-radio-button>
          </a-radio-group>

          <a-button type="text" @click="fetchApplications" :loading="loading">
            <template #icon><reload-outlined /></template>
            刷新
          </a-button>
        </div>

        <a-table
          :columns="columns"
          :data-source="filteredApplications"
          :pagination="false"
          :loading="loading"
          size="middle"
          class="applications-table"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'courseclass'">
              <router-link
                :to="`/home/s-courseclass/${record.courseclass_id}`"
                target="_blank"
              >
                {{ record.courseclass_name }}
              </router-link>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'date'">
              {{ formatDate(record.application_date) }}
            </template>
          </template>

          <template #emptyText>
            <a-empty description="暂无申请记录" />
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import { message } from "ant-design-vue";
import { SolutionOutlined, ReloadOutlined } from "@ant-design/icons-vue";
import { getMyApplications } from "@/api/courseclass";
import type { CourseClassApplication } from "@/api/courseclass";

export default defineComponent({
  name: "MyApplicationsModal",
  components: {
    SolutionOutlined,
    ReloadOutlined,
  },
  setup() {
    const visible = ref(false);
    const loading = ref(false);
    const applications = ref<CourseClassApplication[]>([]);
    const filterStatus = ref("all");

    // 表格列定义
    const columns = [
      {
        title: "课程班名称",
        key: "courseclass",
        dataIndex: ["courseclass_name"],
        width: "30%",
      },
      {
        title: "状态",
        key: "status",
        width: "20%",
      },
      {
        title: "申请时间",
        key: "date",
        width: "20%",
      },
      {
        title: "申请留言",
        key: "message",
        dataIndex: "message",
        ellipsis: true,
      },
    ];

    // 待处理申请数量
    const pendingCount = computed(() => {
      return applications.value.filter((app) => app.status === "pending")
        .length;
    });

    // 根据筛选状态过滤申请
    const filteredApplications = computed(() => {
      if (filterStatus.value === "all") {
        return applications.value;
      }
      return applications.value.filter(
        (app) => app.status === filterStatus.value
      );
    });

    // 获取申请状态文本
    const getStatusText = (status: string) => {
      const map: Record<string, string> = {
        pending: "待处理",
        approved: "已通过",
        rejected: "已拒绝",
      };
      return map[status] || status;
    };

    // 获取状态对应的颜色
    const getStatusColor = (status: string) => {
      const map: Record<string, string> = {
        pending: "orange",
        approved: "green",
        rejected: "red",
      };
      return map[status];
    };

    // 格式化日期
    const formatDate = (dateStr: string) => {
      return new Date(dateStr).toLocaleString();
    };

    // 获取申请列表
    const fetchApplications = async () => {
      try {
        loading.value = true;
        const data = await getMyApplications();
        applications.value = data;
      } catch (error) {
        message.error("获取申请列表失败");
        console.error(error);
      } finally {
        loading.value = false;
      }
    };

    // 显示模态框
    const showModal = () => {
      visible.value = true;
      if (applications.value.length === 0) {
        fetchApplications();
      }
    };

    return {
      visible,
      loading,
      applications,
      filterStatus,
      columns,
      pendingCount,
      filteredApplications,
      getStatusText,
      getStatusColor,
      formatDate,
      fetchApplications,
      showModal,
    };
  },
});
</script>

<style scoped>
.my-applications-btn {
  position: absolute;
  top: 20px;
  right: 20px;
}

.applications-container {
  padding: 16px;
}

.applications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.applications-table {
  margin-top: 16px;
}

:deep(.applications-table .ant-table-cell) {
  padding: 12px 16px !important;
}

:deep(.applications-table .ant-table-row:hover) {
  background-color: #fafafa;
}
</style>
