<template>
  <div class="profile-container">
    <a-card :bordered="false" class="profile-card">
      <!-- 头部信息区 -->
      <div class="profile-header">
        <a-upload
          name="avatar"
          list-type="picture-card"
          class="avatar-uploader"
          :show-upload-list="false"
          :before-upload="beforeUpload"
          :customRequest="customRequest"
          @change="handleAvatarChange"
        >
          <img
            v-if="userInfo.avatar"
            :src="'http://localhost:5000/' + userInfo.avatar"
            alt="头像"
            class="avatar"
          />
          <div v-else>
            <loading-outlined v-if="uploading" />
            <plus-outlined v-else />
            <div class="ant-upload-text">上传头像</div>
          </div>
        </a-upload>

        <div class="profile-basic">
          <h1>{{ userInfo.username }}</h1>
          <div class="user-meta">
            <span
              ><user-outlined />
              {{ userInfo.role === "teacher" ? "教师" : "学生" }}</span
            >
            <span><mail-outlined /> {{ userInfo.email }}</span>
            <span><calendar-outlined /> 注册于 {{ userInfo.created_at }}</span>
          </div>
        </div>
        <div class="profile-actions">
          <a-button type="primary" danger @click="handleLogout">
            <template #icon><logout-outlined /></template>
            退出登录
          </a-button>
        </div>
      </div>

      <!-- 标签页 -->
      <a-tabs v-model:activeKey="activeKey" class="profile-tabs">
        <a-tab-pane key="1" tab="个人资料">
          <a-form
            :model="userInfo"
            :label-col="{ span: 4 }"
            :wrapper-col="{ span: 14 }"
          >
            <a-form-item label="用户名">
              <a-input v-model:value="userInfo.username" disabled />
            </a-form-item>
            <a-form-item label="电子邮箱">
              <a-input v-model:value="userInfo.email" />
            </a-form-item>
            <a-form-item label="个性签名">
              <a-textarea
                v-model:value="userInfo.signature"
                placeholder="介绍一下自己..."
                :rows="4"
              />
            </a-form-item>
            <a-form-item label="角色">
              <a-select v-model:value="userInfo.role" disabled>
                <a-select-option value="student">学生</a-select-option>
                <a-select-option value="teacher">教师</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item :wrapper-col="{ span: 14, offset: 4 }">
              <a-button type="primary" @click="updateProfile"
                >保存修改</a-button
              >
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="2" tab="账号安全" force-render>
          <a-form
            :model="passwordForm"
            :label-col="{ span: 4 }"
            :wrapper-col="{ span: 14 }"
          >
            <a-form-item label="当前密码">
              <a-input-password v-model:value="passwordForm.currentPassword" />
            </a-form-item>
            <a-form-item label="新密码">
              <a-input-password v-model:value="passwordForm.newPassword" />
            </a-form-item>
            <a-form-item label="确认密码">
              <a-input-password v-model:value="passwordForm.confirmPassword" />
            </a-form-item>
            <a-form-item :wrapper-col="{ span: 14, offset: 4 }">
              <a-button type="primary" @click="changePassword"
                >修改密码</a-button
              >
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="3" tab="其他信息">
          <div class="other-info">
            <a-descriptions bordered>
              <a-descriptions-item label="最后登录时间"
                >2023-06-15 14:30:22</a-descriptions-item
              >
              <a-descriptions-item label="登录IP"
                >192.168.1.100</a-descriptions-item
              >
              <a-descriptions-item label="账号状态">
                <a-tag color="green">正常</a-tag>
              </a-descriptions-item>
            </a-descriptions>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted } from "vue";
import {
  UserOutlined,
  MailOutlined,
  CalendarOutlined,
  PlusOutlined,
  LoadingOutlined,
  LogoutOutlined,
} from "@ant-design/icons-vue";
import { message } from "ant-design-vue";
import { useAuthStore } from "@/stores/auth";

export default defineComponent({
  name: "MyProfileView",
  components: {
    UserOutlined,
    MailOutlined,
    CalendarOutlined,
    PlusOutlined,
    LoadingOutlined,
    LogoutOutlined,
  },
  setup() {
    const authStore = useAuthStore();
    const activeKey = ref("1");
    const uploading = ref(false);

    // 用户信息
    const userInfo = ref({
      username: "",
      email: "",
      role: "",
      signature: "",
      password: "",
      avatar: "",
      created_at: "",
    });

    // 密码表单
    const passwordForm = ref({
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    });

    // 加载用户数据
    const loadUserData = async () => {
      try {
        // 这里应该是从store或API获取用户数据
        userInfo.value = {
          ...authStore.user,
          created_at: formatDate(authStore.user?.created_at),
        };
      } catch (error) {
        message.error("加载用户信息失败");
      }
    };

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return "";
      const date = new Date(dateString);
      return date.toLocaleDateString();
    };

    // 更新个人资料
    const updateProfile = async () => {
      try {
        // 这里应该是调用API更新用户信息
        await authStore.updateProfile(userInfo.value);
        message.success("资料更新成功");
      } catch (error) {
        message.error("资料更新失败");
      }
    };

    // 修改密码
    const changePassword = async () => {
      if (
        passwordForm.value.newPassword !== passwordForm.value.confirmPassword
      ) {
        message.error("两次输入的密码不一致");
        return;
      }
      try {
        // 这里应该是调用API修改密码
        userInfo.value.password = passwordForm.value.newPassword;
        await authStore.updateProfile(userInfo.value);
        message.success("密码修改成功");
        passwordForm.value = {
          currentPassword: "",
          newPassword: "",
          confirmPassword: "",
        };
      } catch (error) {
        message.error("密码修改失败");
      }
    };

    const handleLogout = async () => {
      try {
        await authStore.logout();
        message.success("已安全退出");
      } catch (error) {
        message.error("退出登录失败");
      }
    };
    const beforeUpload = (file) => {
      const isImage = file.type.includes("image/");
      if (!isImage) {
        message.error("只能上传图片文件!");
      }
      const isLt2M = file.size / 1024 / 1024 < 2;
      if (!isLt2M) {
        message.error("图片大小不能超过2MB!");
      }
      return isImage && isLt2M;
    };

    const handleAvatarChange = async (info) => {
      if (info.file.status === "uploading") {
        uploading.value = true;
        return;
      }
    };

    const customRequest = async ({ file, onSuccess, onError }) => {
      try {
        await authStore.updateAvatar(file);
        onSuccess();
        userInfo.value.avatar = authStore.user?.avatar;
        message.success("头像上传成功");
      } catch (error) {
        onError();
        message.error("头像上传失败");
      } finally {
        uploading.value = false;
      }
    };
    onMounted(() => {
      loadUserData();
    });

    return {
      activeKey,
      userInfo,
      passwordForm,
      uploading,
      updateProfile,
      changePassword,
      handleLogout,
      beforeUpload,
      handleAvatarChange,
      customRequest,
    };
  },
});
</script>

<style scoped>
/* 新增修复代码 */
.profile-header {
  position: relative; /* 为绝对定位提供参考 */
  flex-wrap: wrap; /* 允许换行 */
}

.profile-actions {
  position: absolute; /* 桌面端保持原位 */
  right: 24px;
  top: 24px;
}

@media (max-width: 768px) {
  .profile-actions {
    position: static; /* 移动端恢复文档流 */
    order: 2; /* 调整排列顺序 */
    width: 100%;
    margin-top: 16px;
    text-align: center;
  }

  .profile-basic {
    order: 1; /* 调整排列顺序 */
    width: 100%;
    margin-top: 16px;
  }
}

.profile-container {
  background: inherit;
  min-height: calc(100vh - 64px);
  display: flex;
  justify-content: center;
}

.profile-card {
  background: inherit;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.profile-header {
  display: flex;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #f0f0f0;
  gap: 24px;
  min-height: 160px; /* 确保最小高度 */
}

.profile-basic {
  flex: 1;
  min-width: 300px;
  padding-right: 100px; /* 为操作按钮留出空间 */
}

.avatar-uploader {
  flex-shrink: 0;
}

.avatar-uploader :deep(.ant-upload) {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f5f5;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-basic {
  flex: 1;
  min-width: 300px;
}

.profile-basic h1 {
  margin-bottom: 12px;
  font-size: 24px;
  color: rgba(0, 0, 0, 0.85);
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: rgba(0, 0, 0, 0.45);
}

.user-meta span {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.user-meta :deep(.anticon) {
  margin-right: 8px;
  font-size: 16px;
}

.profile-actions {
  margin-left: auto;
  flex-shrink: 0;
}

.profile-tabs {
  height: calc(100% - 160px);
}

.profile-tabs :deep(.ant-tabs-nav) {
  padding: 0 24px;
  margin: 0;
}

.profile-tabs :deep(.ant-tabs-tab) {
  padding: 16px 24px;
  font-size: 16px;
}

.profile-tabs :deep(.ant-tabs-content) {
  padding: 24px;
  height: calc(100% - 48px);
  overflow-y: auto;
}

.other-info {
  padding: 16px 0;
}

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    text-align: center;
  }

  .avatar-uploader {
    margin-bottom: 16px;
  }

  .profile-basic {
    width: 100%;
    text-align: center;
  }

  .profile-actions {
    margin: 16px 0 0;
    width: 100%;
  }

  .profile-tabs :deep(.ant-tabs-tab) {
    padding: 12px 16px;
    font-size: 14px;
  }
}
</style>
