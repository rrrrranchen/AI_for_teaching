<template>
  <div class="user-management">
    <a-card title="用户管理" :bordered="false">
      <div class="table-header">
        <a-space>
          <a-button type="primary" @click="showAddModal">
            <template #icon><UserAddOutlined /></template>
            添加用户
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
          <a-select
            v-model:value="searchParams.role"
            placeholder="按角色筛选"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="student">学生</a-select-option>
            <a-select-option value="teacher">教师</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
          </a-select>
          <a-input-search
            v-model:value="searchParams.username"
            placeholder="搜索用户名"
            style="width: 200px"
            @search="fetchUsers"
          />
        </a-space>
      </div>

      <a-table
        :columns="columns"
        :data-source="userList"
        :row-key="(record: User) => record.id"
        :row-selection="{
          selectedRowKeys: selectedRowKeys,
          onChange: onSelectChange,
        }"
        :pagination="pagination"
        :loading="loading"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">
            <a-tag :color="roleColors[record.role as UserRole]">
              {{ roleNames[record.role as UserRole] }}
            </a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="showEditModal(record)">
                <template #icon><EditOutlined /></template>
              </a-button>
              <a-popconfirm
                title="确定要删除此用户吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="deleteUser(record.id)"
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

    <!-- 添加用户模态框 -->
    <a-modal
      v-model:visible="addModalVisible"
      title="添加用户"
      @ok="handleAddOk"
      @cancel="handleAddCancel"
      :confirm-loading="confirmLoading"
    >
      <a-form
        :model="addForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
        ref="addFormRef"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input v-model:value="addForm.username" />
        </a-form-item>
        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password v-model:value="addForm.password" />
        </a-form-item>
        <a-form-item
          label="邮箱"
          name="email"
          :rules="[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]"
        >
          <a-input v-model:value="addForm.email" />
        </a-form-item>
        <a-form-item
          label="角色"
          name="role"
          :rules="[{ required: true, message: '请选择角色' }]"
        >
          <a-select v-model:value="addForm.role">
            <a-select-option value="student">学生</a-select-option>
            <a-select-option value="teacher">教师</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="签名" name="signature">
          <a-input v-model:value="addForm.signature" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑用户模态框 -->
    <a-modal
      v-model:visible="editModalVisible"
      title="编辑用户"
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
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input v-model:value="editForm.username" />
        </a-form-item>
        <a-form-item label="密码" name="password">
          <a-input-password
            v-model:value="editForm.password"
            placeholder="留空则不修改密码"
          />
        </a-form-item>
        <a-form-item
          label="邮箱"
          name="email"
          :rules="[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]"
        >
          <a-input v-model:value="editForm.email" />
        </a-form-item>
        <a-form-item
          label="角色"
          name="role"
          :rules="[{ required: true, message: '请选择角色' }]"
        >
          <a-select v-model:value="editForm.role">
            <a-select-option value="student">学生</a-select-option>
            <a-select-option value="teacher">教师</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="签名" name="signature">
          <a-input v-model:value="editForm.signature" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { message } from "ant-design-vue";
import type { TableProps } from "ant-design-vue";
import {
  UserAddOutlined,
  DeleteOutlined,
  EditOutlined,
} from "@ant-design/icons-vue";
import adminApi from "@/api/usermanage";
import type {
  User,
  QueryUsersParams,
  AddUserParams,
  UpdateUserParams,
} from "@/api/usermanage";

// 定义角色类型
type UserRole = "student" | "teacher" | "admin";

// 表格列定义
const columns = [
  {
    title: "ID",
    dataIndex: "id",
    key: "id",
    width: 80,
  },
  {
    title: "用户名",
    dataIndex: "username",
    key: "username",
  },
  {
    title: "邮箱",
    dataIndex: "email",
    key: "email",
  },
  {
    title: "角色",
    dataIndex: "role",
    key: "role",
  },
  {
    title: "签名",
    dataIndex: "signature",
    key: "signature",
    ellipsis: true,
  },
  {
    title: "创建时间",
    dataIndex: "created_at",
    key: "created_at",
  },
  {
    title: "操作",
    key: "action",
    width: 120,
  },
];

// 角色颜色和名称映射
const roleColors: Record<UserRole, string> = {
  student: "blue",
  teacher: "orange",
  admin: "red",
};

const roleNames: Record<UserRole, string> = {
  student: "学生",
  teacher: "教师",
  admin: "管理员",
};

// 用户列表数据
const userList = ref<User[]>([]);
const loading = ref(false);
const selectedRowKeys = ref<number[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  pageSizeOptions: ["10", "20", "50", "100"],
});

// 搜索参数
const searchParams = reactive<QueryUsersParams>({
  role: undefined,
  username: undefined,
});

// 添加用户表单
const addModalVisible = ref(false);
const addFormRef = ref();
const addForm = reactive<AddUserParams>({
  username: "",
  password: "",
  email: "",
  role: "student",
  signature: "",
});

// 编辑用户表单
const editModalVisible = ref(false);
const editFormRef = ref();
const editForm = reactive<UpdateUserParams & { id: number }>({
  id: 0,
  username: "",
  password: "",
  email: "",
  role: "student",
  signature: "",
});

const confirmLoading = ref(false);

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

// 获取用户列表
const fetchUsers = async () => {
  try {
    loading.value = true;
    const params = {
      role: searchParams.role,
      username: searchParams.username,
      page: pagination.current,
      page_size: pagination.pageSize, // 注意后端可能使用page_size而不是pageSize
    };

    // 移除undefined参数
    const filteredParams = Object.fromEntries(
      Object.entries(params).filter(([_, v]) => v !== undefined)
    );

    const users = await adminApi.queryUsers(filteredParams);
    userList.value = users;
  } catch (error) {
    message.error("获取用户列表失败");
  } finally {
    loading.value = false;
  }
};

// 表格分页、排序、筛选变化
const handleTableChange: TableProps["onChange"] = (pag, filters, sorter) => {
  pagination.current = pag.current!;
  pagination.pageSize = pag.pageSize!;
  fetchUsers();
};

// 选择行变化
const onSelectChange = (selectedKeys: number[]) => {
  selectedRowKeys.value = selectedKeys;
};

// 显示添加用户模态框
const showAddModal = () => {
  addModalVisible.value = true;
};

// 添加用户确认
const handleAddOk = async () => {
  try {
    confirmLoading.value = true;
    await addFormRef.value.validate();
    await adminApi.addUser(addForm);
    message.success("添加用户成功");
    addModalVisible.value = false;
    fetchUsers();
    resetAddForm();
  } catch (error) {
    console.error(error);
  } finally {
    confirmLoading.value = false;
  }
};

// 添加用户取消
const handleAddCancel = () => {
  addModalVisible.value = false;
  resetAddForm();
};

// 重置添加表单
const resetAddForm = () => {
  addFormRef.value?.resetFields();
};

// 显示编辑用户模态框
const showEditModal = (record: User) => {
  editForm.id = record.id;
  editForm.username = record.username;
  editForm.email = record.email;
  editForm.role = record.role;
  editForm.signature = record.signature || "";
  editForm.password = "";
  editModalVisible.value = true;
};

// 编辑用户确认
const handleEditOk = async () => {
  try {
    confirmLoading.value = true;
    await editFormRef.value.validate();
    const { id, ...updateData } = editForm;
    if (!updateData.password) {
      delete updateData.password;
    }
    await adminApi.updateUser(id, updateData);
    message.success("更新用户成功");
    editModalVisible.value = false;
    fetchUsers();
  } catch (error) {
    console.error(error);
  } finally {
    confirmLoading.value = false;
  }
};

// 编辑用户取消
const handleEditCancel = () => {
  editModalVisible.value = false;
};

// 删除单个用户
const deleteUser = async (userId: number) => {
  try {
    await adminApi.deleteUsers([userId]);
    message.success("删除用户成功");
    fetchUsers();
  } catch (error) {
    message.error("删除用户失败");
  }
};

// 批量删除用户
const batchDelete = async () => {
  try {
    await adminApi.deleteUsers(selectedRowKeys.value);
    message.success(`成功删除 ${selectedRowKeys.value.length} 个用户`);
    selectedRowKeys.value = [];
    fetchUsers();
  } catch (error) {
    message.error("批量删除用户失败");
  }
};

// 初始化加载数据
onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
.user-management {
  padding: 16px;
  background: #fff;
}

.table-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
