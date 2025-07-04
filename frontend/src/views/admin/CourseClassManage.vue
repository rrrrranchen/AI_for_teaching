<template>
  <div class="courseclass-management">
    <a-card title="课程班管理" :bordered="false">
      <div class="table-header">
        <a-space>
          <a-button type="primary" @click="showSearchModal">
            <template #icon><SearchOutlined /></template>
            高级搜索
          </a-button>
          <a-button
            danger
            @click="batchDelete"
            :disabled="selectedRowKeys.length === 0"
          >
            <template #icon><DeleteOutlined /></template>
            批量删除
          </a-button>
        </a-space>
        <a-space>
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索课程班名称"
            style="width: 200px"
            @search="handleSearch"
          />
        </a-space>
      </div>

      <a-table
        :columns="columns"
        :data-source="courseClasses"
        :row-key="(record: any) => record.id"
        :row-selection="{
          selectedRowKeys: selectedRowKeys,
          onChange: onSelectChange,
        }"
        :pagination="pagination"
        :loading="loading"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'image_path'">
            <a-image
              v-if="record.image_path"
              :width="80"
              :src="getImageUrl(record.image_path)"
              :preview="false"
            />
            <span v-else>无封面</span>
          </template>
          <template v-if="column.key === 'teachers'">
            <a-tag v-for="teacher in record.teachers" :key="teacher.id">
              {{ teacher.name }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="showEditModal(record)">
                <template #icon><EditOutlined /></template>
              </a-button>
              <a-popconfirm
                title="确定要删除此课程班吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="deleteCourseClass(record.id)"
              >
                <a-button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 编辑课程班模态框 -->
    <a-modal
      v-model:visible="editModalVisible"
      title="编辑课程班"
      @ok="handleEditOk"
      @cancel="handleEditCancel"
      :confirm-loading="confirmLoading"
    >
      <a-form
        :model="editForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
        ref="editFormRef"
      >
        <a-form-item label="课程班名称" name="name">
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-form-item label="课程班描述" name="description">
          <a-textarea v-model:value="editForm.description" />
        </a-form-item>
        <a-form-item label="封面图片">
          <a-upload :before-upload="beforeUpload" :show-upload-list="false">
            <a-button> <UploadOutlined /> 上传新封面 </a-button>
          </a-upload>
          <div v-if="editForm.image" style="margin-top: 10px">
            已选择: {{ editForm.image.name }}
          </div>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 高级搜索模态框 -->
    <a-modal
      v-model:visible="searchModalVisible"
      title="高级搜索"
      @ok="handleSearchOk"
      @cancel="handleSearchCancel"
    >
      <a-form :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="课程班名称">
          <a-input v-model:value="searchParams.name" />
        </a-form-item>
        <a-form-item label="教师ID">
          <a-input-number
            v-model:value="searchParams.teacher_id"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="学生ID">
          <a-input-number
            v-model:value="searchParams.student_id"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="课程ID">
          <a-input-number
            v-model:value="searchParams.course_id"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="邀请码">
          <a-input v-model:value="searchParams.invite_code" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 排行榜卡片 -->
    <a-card title="公开课程班排行榜" style="margin-top: 20px">
      <a-list item-layout="horizontal" :data-source="ranking">
        <template #renderItem="{ item, index }">
          <a-list-item>
            <a-list-item-meta>
              <template #title>
                <a-tag :color="getRankColor(index + 1)"
                  >第{{ index + 1 }}名</a-tag
                >
                {{ item.name }}
              </template>
              <template #description>
                <a-space>
                  <span>推荐指数: {{ item.recommend_index }}</span>
                  <span>学生数: {{ item.student_count }}</span>
                  <span>平均准确率: {{ item.avg_accuracy }}%</span>
                </a-space>
              </template>
              <template #avatar>
                <a-image
                  :width="60"
                  :src="getImageUrl(item.image_path)"
                  :preview="false"
                />
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from "vue";
import { message } from "ant-design-vue";
import type { TableProps } from "ant-design-vue";
import {
  SearchOutlined,
  DeleteOutlined,
  EditOutlined,
  UploadOutlined,
} from "@ant-design/icons-vue";
import adminCourseClassApi from "@/api/courseclassmanage";
import type {
  CourseClass,
  RankedCourseClass,
  QueryCourseClassesParams,
  UpdateCourseClassParams,
} from "@/api/courseclassmanage";

// 表格列定义
const columns = [
  {
    title: "ID",
    dataIndex: "id",
    key: "id",
    width: 80,
  },
  {
    title: "课程班名称",
    dataIndex: "name",
    key: "name",
  },
  {
    title: "封面",
    dataIndex: "image_path",
    key: "image_path",
    width: 100,
  },
  {
    title: "教师数",
    dataIndex: "teacher_count",
    key: "teacher_count",
    width: 100,
  },
  {
    title: "学生数",
    dataIndex: "student_count",
    key: "student_count",
    width: 100,
  },
  {
    title: "课程数",
    dataIndex: "course_count",
    key: "course_count",
    width: 100,
  },
  {
    title: "教师",
    dataIndex: "teachers",
    key: "teachers",
  },
  {
    title: "操作",
    key: "action",
    width: 120,
  },
];

// 数据状态
const courseClasses = ref<CourseClass[]>([]);
const ranking = ref<RankedCourseClass[]>([]);
const loading = ref(false);
const selectedRowKeys = ref<number[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  pageSizeOptions: ["10", "20", "50", "100"],
});

// 搜索相关
const searchText = ref("");
const searchModalVisible = ref(false);
const searchParams = reactive<QueryCourseClassesParams>({
  name: undefined,
  teacher_id: undefined,
  student_id: undefined,
  course_id: undefined,
  invite_code: undefined,
});

// 编辑相关
const editModalVisible = ref(false);
const editFormRef = ref();
const editForm = reactive<{
  id: number;
  name: string;
  description: string;
  image?: File;
}>({
  id: 0,
  name: "",
  description: "",
});
const confirmLoading = ref(false);

// 获取图片完整URL
const getImageUrl = (path: string) => {
  return path ? `http://localhost:5000/${path}` : "";
};

// 获取课程班列表
const fetchCourseClasses = async (params?: QueryCourseClassesParams) => {
  try {
    loading.value = true;
    const result = await adminCourseClassApi.queryCourseClasses(
      params || searchParams
    );
    courseClasses.value = result;
    pagination.total = result.length;
  } catch (error) {
    message.error("获取课程班列表失败");
  } finally {
    loading.value = false;
  }
};

// 获取排行榜
const fetchRanking = async () => {
  try {
    const result = await adminCourseClassApi.getPublicCourseClassRanking();
    ranking.value = result;
  } catch (error) {
    message.error("获取排行榜失败");
  }
};

// 表格分页变化处理
const handleTableChange: TableProps["onChange"] = (pag) => {
  pagination.current = pag.current!;
  pagination.pageSize = pag.pageSize!;
};

// 选择行变化
const onSelectChange = (selectedKeys: number[]) => {
  selectedRowKeys.value = selectedKeys;
};

// 搜索处理
const handleSearch = () => {
  searchParams.name = searchText.value;
  fetchCourseClasses();
};

// 高级搜索
const showSearchModal = () => {
  searchModalVisible.value = true;
};

const handleSearchOk = () => {
  fetchCourseClasses();
  searchModalVisible.value = false;
};

const handleSearchCancel = () => {
  searchModalVisible.value = false;
};

// 编辑课程班
const showEditModal = (record: CourseClass) => {
  editForm.id = record.id;
  editForm.name = record.name;
  editForm.description = record.description || "";
  editModalVisible.value = true;
};

const beforeUpload = (file: File) => {
  editForm.image = file;
  return false; // 阻止自动上传
};

const handleEditOk = async () => {
  try {
    confirmLoading.value = true;
    const updateData: UpdateCourseClassParams = {
      name: editForm.name,
      description: editForm.description,
    };
    const updateformdata = new FormData();
    updateformdata.append("name", editForm.name);
    updateformdata.append("description", editForm.description);
    if (editForm.image) {
      updateData.image = editForm.image;
    }

    await adminCourseClassApi.updateCourseClass(editForm.id, updateformdata);
    message.success("更新课程班成功");
    editModalVisible.value = false;
    fetchCourseClasses();
  } catch (error) {
    message.error("更新课程班失败");
  } finally {
    confirmLoading.value = false;
  }
};

const handleEditCancel = () => {
  editModalVisible.value = false;
};

// 删除课程班
const deleteCourseClass = async (id: number) => {
  try {
    await adminCourseClassApi.deleteCourseClasses([id]);
    message.success("删除课程班成功");
    fetchCourseClasses();
  } catch (error) {
    message.error("删除课程班失败");
  }
};

// 批量删除
const batchDelete = async () => {
  try {
    await adminCourseClassApi.deleteCourseClasses(selectedRowKeys.value);
    message.success(`成功删除 ${selectedRowKeys.value.length} 个课程班`);
    selectedRowKeys.value = [];
    fetchCourseClasses();
  } catch (error) {
    message.error("批量删除课程班失败");
  }
};

const getRankColor = (rank: number) => {
  switch (rank) {
    case 1:
      return "gold"; // 第一名金色
    case 2:
      return "silver"; // 第二名银色
    case 3:
      return "#cd7f32"; // 第三名铜色(青铜色)
    default:
      return "gray"; // 其他名次灰色
  }
};

// 初始化加载数据
onMounted(() => {
  fetchCourseClasses();
  fetchRanking();
});
</script>

<style scoped>
.courseclass-management {
  padding: 16px;
  background: #ffffff;
}

.table-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
