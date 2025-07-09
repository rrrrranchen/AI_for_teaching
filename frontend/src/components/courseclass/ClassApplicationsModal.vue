<template>
  <a-modal
    v-model:visible="visible"
    title="班级申请管理"
    @ok="handleOk"
    @cancel="handleCancel"
    width="800px"
    :footer="null"
  >
    <div class="applications-container">
      <div class="filter-section">
        <a-radio-group v-model:value="filterStatus" button-style="solid">
          <a-radio-button value="all">全部</a-radio-button>
          <a-radio-button value="pending">待处理</a-radio-button>
          <a-radio-button value="approved">已通过</a-radio-button>
          <a-radio-button value="rejected">已拒绝</a-radio-button>
        </a-radio-group>
        <a-button @click="fetchApplications" :loading="loading">
          <template #icon><reload-outlined /></template>
          刷新
        </a-button>
      </div>

      <a-table
        :columns="columns"
        :data-source="filteredApplications"
        :pagination="false"
        :loading="loading"
        rowKey="id"
        size="middle"
        class="applications-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'student'">
            <a-avatar :src="record.student?.avatar" />
            <span style="margin-left: 8px">{{ record.student_name }}</span>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'date'">
            {{ formatDate(record.application_date) }}
          </template>
          <template
            v-else-if="column.key === 'actions' && record.status === 'pending'"
          >
            <a-space>
              <a-button
                type="link"
                size="small"
                @click="handleApprove(record.id)"
              >
                通过
              </a-button>
              <a-button
                type="link"
                size="small"
                danger
                @click="handleReject(record.id)"
              >
                拒绝
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, computed, defineEmits, defineProps, defineExpose } from "vue";
import { message, Modal } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import {
  getCourseclassApplications,
  processApplication,
  type CourseClassApplication,
} from "@/api/courseclass";

const props = defineProps({
  courseclassId: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(["processed"]);

const visible = ref(false);
const loading = ref(false);
const applications = ref<CourseClassApplication[]>([]);
const filterStatus = ref("all");

const columns = [
  {
    title: "学生",
    key: "student",
    width: "25%",
  },
  {
    title: "申请时间",
    key: "date",
    width: "20%",
  },
  {
    title: "状态",
    key: "status",
    width: "15%",
  },
  {
    title: "留言",
    dataIndex: "message",
    key: "message",
    ellipsis: true,
    width: "25%",
  },
  {
    title: "操作",
    key: "actions",
    width: "15%",
  },
];

const filteredApplications = computed(() => {
  if (filterStatus.value === "all") return applications.value;
  return applications.value.filter((app) => app.status === filterStatus.value);
});

const showModal = () => {
  visible.value = true;
  fetchApplications();
};

const fetchApplications = async () => {
  try {
    loading.value = true;
    const data = await getCourseclassApplications(props.courseclassId);
    applications.value = data;
  } catch (error) {
    message.error("获取申请列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const handleApprove = async (applicationId: number) => {
  try {
    await processApplication(applicationId, { action: "approve" });
    message.success("已通过申请");
    fetchApplications();
    emit("processed");
  } catch (error) {
    message.error("操作失败");
    console.error(error);
  }
};

const handleReject = async (applicationId: number) => {
  Modal.confirm({
    title: "确定要拒绝此申请吗？",
    content: "拒绝后学生将收到通知",
    okText: "确认",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      try {
        await processApplication(applicationId, { action: "reject" });
        message.success("已拒绝申请");
        fetchApplications();
        emit("processed");
      } catch (error) {
        message.error("操作失败");
        console.error(error);
      }
    },
  });
};

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: "待处理",
    approved: "已通过",
    rejected: "已拒绝",
  };
  return map[status] || status;
};

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    pending: "orange",
    approved: "green",
    rejected: "red",
  };
  return map[status];
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString();
};

const handleOk = () => {
  visible.value = false;
};

const handleCancel = () => {
  visible.value = false;
};

defineExpose({
  showModal,
});
</script>

<style scoped>
.applications-container {
  padding: 16px;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.applications-table {
  margin-top: 16px;
}
</style>
