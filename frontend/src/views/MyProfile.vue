<template>
  <div class="profile-container">
    <a-card :bordered="false" class="profile-card">
      <!-- 头部信息区 -->
      <div class="profile-header">
        <!-- 头像和基本信息放在一个flex容器中 -->
        <div class="header-main">
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
            <div v-else class="avatar-placeholder">
              <loading-outlined v-if="uploading" />
              <plus-outlined v-else />
              <div class="ant-upload-text">上传头像</div>
            </div>
          </a-upload>

          <div class="profile-basic">
            <h1>{{ userInfo.username }}</h1>
            <div class="user-meta">
              <a-tag
                :color="userInfo.role === 'teacher' ? 'blue' : 'green'"
                class="role-tag"
              >
                <template #icon><user-outlined /></template>
                {{ userInfo.role === "teacher" ? "教师" : "学生" }}
              </a-tag>
              <span class="meta-item"
                ><mail-outlined /> {{ userInfo.email }}</span
              >
              <span class="meta-item"
                ><calendar-outlined /> 注册于 {{ userInfo.created_at }}</span
              >
            </div>
          </div>
        </div>

        <!-- 退出按钮单独放置 -->
        <div class="profile-actions">
          <a-button
            type="primary"
            danger
            @click="handleLogout"
            class="logout-btn"
          >
            <template #icon><logout-outlined /></template>
            退出登录
          </a-button>
        </div>
      </div>

      <!-- 标签页 -->
      <a-tabs v-model:activeKey="activeKey" class="profile-tabs" type="card">
        <a-tab-pane key="1" tab="个人资料">
          <div class="tab-content">
            <a-form
              :model="userInfo"
              :label-col="{ span: 4 }"
              :wrapper-col="{ span: 14 }"
              layout="horizontal"
            >
              <a-form-item label="用户名">
                <a-input
                  v-model:value="userInfo.username"
                  disabled
                  class="form-input"
                />
              </a-form-item>
              <a-form-item label="电子邮箱">
                <a-input v-model:value="userInfo.email" class="form-input" />
              </a-form-item>
              <a-form-item label="个性签名">
                <a-textarea
                  v-model:value="userInfo.signature"
                  placeholder="介绍一下自己..."
                  :rows="4"
                  class="form-textarea"
                />
              </a-form-item>
              <a-form-item label="角色">
                <a-select
                  v-model:value="userInfo.role"
                  disabled
                  class="form-select"
                >
                  <a-select-option value="student">学生</a-select-option>
                  <a-select-option value="teacher">教师</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item :wrapper-col="{ span: 14, offset: 4 }">
                <a-button
                  type="primary"
                  @click="updateProfile"
                  class="save-btn"
                >
                  <template #icon><save-outlined /></template>
                  保存修改
                </a-button>
              </a-form-item>
            </a-form>
          </div>
        </a-tab-pane>

        <a-tab-pane key="2" tab="账号安全" force-render>
          <div class="tab-content">
            <a-form
              :model="passwordForm"
              :label-col="{ span: 4 }"
              :wrapper-col="{ span: 14 }"
              layout="horizontal"
            >
              <a-form-item label="当前密码">
                <a-input-password
                  v-model:value="passwordForm.currentPassword"
                  class="form-input"
                />
              </a-form-item>
              <a-form-item label="新密码">
                <a-input-password
                  v-model:value="passwordForm.newPassword"
                  class="form-input"
                />
              </a-form-item>
              <a-form-item label="确认密码">
                <a-input-password
                  v-model:value="passwordForm.confirmPassword"
                  class="form-input"
                />
              </a-form-item>
              <a-form-item :wrapper-col="{ span: 14, offset: 4 }">
                <a-button
                  type="primary"
                  @click="changePassword"
                  class="save-btn"
                >
                  <template #icon><lock-outlined /></template>
                  修改密码
                </a-button>
              </a-form-item>
            </a-form>
          </div>
        </a-tab-pane>

        <a-tab-pane key="3" tab="登录记录">
          <div class="tab-content">
            <div class="other-info">
              <a-descriptions bordered :column="1">
                <a-descriptions-item label="最后登录时间">
                  <span class="info-value">2025-07-10 14:30:22</span>
                </a-descriptions-item>
                <a-descriptions-item label="登录IP">
                  <span class="info-value">192.168.1.100</span>
                </a-descriptions-item>
                <a-descriptions-item label="账号状态">
                  <a-tag color="green" class="status-tag">正常</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="登录设备">
                  <span class="info-value">Windows 11 / Edge</span>
                </a-descriptions-item>
              </a-descriptions>
            </div>
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
  SaveOutlined,
  LockOutlined,
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
    SaveOutlined,
    LockOutlined,
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

<style scoped lang="less">
@primary-color: #1890ff;
@border-color: #f0f0f0;
@card-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
@text-color: rgba(0, 0, 0, 0.85);
@text-color-secondary: rgba(0, 0, 0, 0.45);
@border-radius-base: 8px;

.profile-container {
  background: url("../assets/FirstScreenbg.png");
  background-size: cover; /* 确保背景图片覆盖整个容器 */
  height: 100%;
  display: flex;
  justify-content: center;
}

.profile-card {
  height: 100vh;
  width: 80%;
  box-shadow: @card-shadow;
  overflow: hidden;
  background: #fff;

  :deep(.ant-card-body) {
    padding: 0;
  }
}

.profile-header {
  display: flex;
  justify-content: space-between; /* 使两部分分开 */
  align-items: flex-start; /* 顶部对齐 */
  padding: 32px;
  border-bottom: 1px solid @border-color;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
}

.header-main {
  align-items: center;
  gap: 24px; /* 头像和基本信息之间的间距 */
  flex: 1; /* 占据剩余空间 */
  min-width: 0; /* 防止内容溢出 */
}

.profile-basic {
  flex: 1;
  min-width: 0; /* 防止文本溢出 */

  h1 {
    margin: 0 0 12px 0;
    font-size: 28px;
    font-weight: 600;
    color: @text-color;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.profile-actions {
  flex-shrink: 0; /* 防止按钮被压缩 */
  margin-left: 24px; /* 与主内容区的间距 */
}

/* 响应式调整 */
@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    padding: 24px 16px;
  }

  .header-main {
    width: 100%;
    margin-bottom: 16px;
  }

  .profile-actions {
    margin-left: 0;
    width: 100%;
    text-align: center;
  }
}

.avatar-uploader {
  flex-shrink: 0;

  :deep(.ant-upload) {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #fff;
    border: 4px solid #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s;

    &:hover {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  }
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: @text-color-secondary;

  .anticon {
    font-size: 24px;
    margin-bottom: 8px;
  }
}
.user-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;

  .meta-item {
    display: flex;
    align-items: center;
    font-size: 14px;
    color: @text-color-secondary;

    .anticon {
      margin-right: 8px;
      color: @primary-color;
    }
  }

  .role-tag {
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 12px;

    .anticon {
      margin-right: 4px;
    }
  }
}

.profile-tabs {
  :deep(.ant-tabs-nav) {
    padding: 0 32px;
    margin: 0;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);

    &::before {
      border-bottom: none;
    }

    .ant-tabs-tab {
      padding: 16px 24px;
      font-size: 16px;
      font-weight: 500;
      color: @text-color-secondary;
      border: none !important;
      margin: 0 4px 0 0;
      border-radius: @border-radius-base @border-radius-base 0 0;
      transition: all 0.3s;

      &:hover {
        color: @primary-color;
      }

      &.ant-tabs-tab-active {
        background: #f0f7ff;
        color: @primary-color;
      }
    }

    .ant-tabs-ink-bar {
      height: 3px;
      background: @primary-color;
    }
  }

  :deep(.ant-tabs-content) {
    padding: 32px;
    background: #fff;
  }
}

.tab-content {
  max-width: 80%;
  margin: 0 auto;
}

.form-input,
.form-select,
.form-textarea {
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  transition: all 0.3s;

  &:hover {
    border-color: @primary-color;
  }

  &:focus {
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }
}

.save-btn {
  padding: 0 24px;
  height: 40px;
  font-weight: 500;
  border-radius: 4px;
}

.other-info {
  :deep(.ant-descriptions) {
    border-radius: @border-radius-base;
    overflow: hidden;

    .ant-descriptions-item-label {
      background: #fafafa;
      font-weight: 500;
      color: @text-color;
    }

    .ant-descriptions-item-content {
      padding: 12px 16px;
    }

    .info-value {
      color: @text-color;
    }

    .status-tag {
      border-radius: 12px;
      padding: 2px 8px;
    }
  }
}

@media (max-width: 768px) {
  .profile-container {
    padding: 16px;
  }

  .profile-header {
    flex-direction: column;
    padding: 24px 16px;
    text-align: center;

    .header-content {
      flex-direction: column;
      gap: 16px;
    }
  }

  .profile-basic {
    width: 100%;
    text-align: center;

    h1 {
      font-size: 24px;
    }
  }

  .user-meta {
    justify-content: center;
  }

  .profile-actions {
    margin: 16px 0 0;
    width: 100%;
  }

  .profile-tabs {
    :deep(.ant-tabs-nav) {
      padding: 0 16px;

      .ant-tabs-tab {
        padding: 12px 16px;
        font-size: 14px;
      }
    }

    :deep(.ant-tabs-content) {
      padding: 24px 16px;
    }
  }
}
</style>
