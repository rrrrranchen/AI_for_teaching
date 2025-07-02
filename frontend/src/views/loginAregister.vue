<template>
  <a-row class="auth-section" type="flex" justify="center" align="middle">
    <a-col :span="12" class="auth-background">
      <img src="../assets/aiedu.png" alt="Background" class="bg-image" />
    </a-col>
    <a-col :span="12" class="auth-container">
      <div class="auth-content">
        <div class="auth-header">
          <img src="../assets/sys_logo.png" class="auth-logo" alt="Logo" />
          <h1 class="auth-system-name">教备通</h1>
        </div>

        <a-card class="auth-form-container" :bordered="false">
          <a-tabs v-model:activeKey="currentTab" centered>
            <!-- 登录表单 -->
            <a-tab-pane key="login" tab="登录">
              <a-form
                layout="vertical"
                :model="loginForm"
                @finish="handleLogin"
              >
                <a-form-item
                  label="用户名"
                  name="username"
                  :rules="[{ required: true, message: '请输入用户名' }]"
                >
                  <a-input
                    v-model:value="loginForm.username"
                    placeholder="请输入用户名"
                    size="large"
                  >
                    <template #prefix>
                      <UserOutlined style="color: rgba(0, 0, 0, 0.25)" />
                    </template>
                  </a-input>
                </a-form-item>

                <a-form-item
                  label="密码"
                  name="password"
                  :rules="[{ required: true, message: '请输入密码' }]"
                >
                  <a-input-password
                    v-model:value="loginForm.password"
                    placeholder="请输入密码"
                    size="large"
                  >
                    <template #prefix>
                      <LockOutlined style="color: rgba(0, 0, 0, 0.25)" />
                    </template>
                  </a-input-password>
                </a-form-item>

                <a-form-item
                  label="验证码"
                  name="captcha"
                  :rules="[{ required: true, message: '请输入验证码' }]"
                >
                  <a-row :gutter="8">
                    <a-col :span="16">
                      <a-input
                        v-model:value="loginForm.captcha"
                        placeholder="请输入验证码"
                        size="large"
                      />
                    </a-col>
                    <a-col :span="8">
                      <div class="captcha-image" @click="refreshCaptcha">
                        <img
                          :src="captchaImage"
                          alt="验证码"
                          v-if="captchaImage"
                        />
                        <reload-outlined v-else />
                      </div>
                    </a-col>
                  </a-row>
                </a-form-item>

                <a-form-item>
                  <a-checkbox v-model:checked="loginForm.remember">
                    记住我
                  </a-checkbox>
                  <a class="forgot-password" href="">忘记密码?</a>
                </a-form-item>

                <a-form-item>
                  <a-button
                    type="primary"
                    html-type="submit"
                    size="large"
                    block
                    :loading="auth.isLoading"
                  >
                    {{ auth.isLoading ? "登录中..." : "登录" }}
                  </a-button>
                </a-form-item>

                <a-alert
                  v-if="auth.error"
                  :message="auth.error"
                  type="error"
                  show-icon
                  closable
                />
              </a-form>
            </a-tab-pane>

            <!-- 注册表单（分步实现） -->
            <a-tab-pane key="register" tab="注册">
              <a-steps :current="registerStep" class="register-steps">
                <a-step title="基本信息" />
                <a-step title="账户设置" />
                <a-step title="完成注册" />
              </a-steps>

              <!-- 第一步：基本信息 -->
              <div v-show="registerStep === 0" class="step-content">
                <a-form
                  layout="vertical"
                  :model="registerForm"
                  :rules="step1Rules"
                  ref="step1Form"
                >
                  <a-form-item label="用户名" name="username">
                    <a-input
                      v-model:value="registerForm.username"
                      placeholder="请输入用户名"
                      size="large"
                    >
                      <template #prefix>
                        <UserOutlined style="color: rgba(0, 0, 0, 0.25)" />
                      </template>
                    </a-input>
                  </a-form-item>

                  <a-form-item label="邮箱" name="email">
                    <a-input
                      v-model:value="registerForm.email"
                      placeholder="请输入邮箱"
                      size="large"
                    >
                      <template #prefix>
                        <MailOutlined style="color: rgba(0, 0, 0, 0.25)" />
                      </template>
                    </a-input>
                  </a-form-item>

                  <a-form-item label="角色" name="role">
                    <a-select
                      v-model:value="registerForm.role"
                      size="large"
                      placeholder="请选择角色"
                    >
                      <a-select-option value="student">学生</a-select-option>
                      <a-select-option value="teacher">教师</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-form>
              </div>

              <!-- 第二步：账户设置 -->
              <div v-show="registerStep === 1" class="step-content">
                <a-form
                  layout="vertical"
                  :model="registerForm"
                  :rules="step2Rules"
                  ref="step2Form"
                >
                  <a-form-item label="密码" name="password">
                    <a-input-password
                      v-model:value="registerForm.password"
                      placeholder="请输入密码"
                      size="large"
                    >
                      <template #prefix>
                        <LockOutlined style="color: rgba(0, 0, 0, 0.25)" />
                      </template>
                    </a-input-password>
                  </a-form-item>

                  <a-form-item label="确认密码" name="confirmPassword">
                    <a-input-password
                      v-model:value="registerForm.confirmPassword"
                      placeholder="请再次输入密码"
                      size="large"
                    >
                      <template #prefix>
                        <LockOutlined style="color: rgba(0, 0, 0, 0.25)" />
                      </template>
                    </a-input-password>
                  </a-form-item>

                  <div class="agreement">
                    <a-checkbox v-model:checked="agreeTerms">
                      我已阅读并同意
                    </a-checkbox>
                    <a href="#" @click.prevent="showAgreement">《用户协议》</a>
                  </div>
                </a-form>
              </div>

              <!-- 第三步：确认信息 -->
              <div v-show="registerStep === 2" class="step-content">
                <div class="confirm-info">
                  <h3>请确认您的注册信息</h3>
                  <a-descriptions bordered size="small" :column="1">
                    <a-descriptions-item label="用户名">
                      {{ registerForm.username }}
                    </a-descriptions-item>
                    <a-descriptions-item label="邮箱">
                      {{ registerForm.email }}
                    </a-descriptions-item>
                    <a-descriptions-item label="角色">
                      {{ registerForm.role === "student" ? "学生" : "教师" }}
                    </a-descriptions-item>
                  </a-descriptions>
                </div>
              </div>

              <div class="step-actions">
                <a-button
                  v-if="registerStep > 0"
                  @click="prevStep"
                  :disabled="auth.isLoading"
                >
                  上一步
                </a-button>
                <a-button
                  v-if="registerStep < 2"
                  type="primary"
                  @click="nextStep"
                  :loading="auth.isLoading"
                >
                  下一步
                </a-button>
                <a-button
                  v-if="registerStep === 2"
                  type="primary"
                  @click="handleRegister"
                  :loading="auth.isLoading"
                  :disabled="!agreeTerms"
                >
                  提交注册
                </a-button>
              </div>

              <a-alert
                v-if="auth.error"
                :message="auth.error"
                type="error"
                show-icon
                closable
                class="error-alert"
              />
            </a-tab-pane>
          </a-tabs>

          <div class="auth-footer">
            <p>其他登录方式</p>
            <div class="social-login">
              <a-button shape="circle" size="large">
                <template #icon><wechat-outlined /></template>
              </a-button>
              <a-button shape="circle" size="large">
                <template #icon><alipay-outlined /></template>
              </a-button>
              <a-button shape="circle" size="large">
                <template #icon><qq-outlined /></template>
              </a-button>
            </div>
            <p class="copyright">© 2025 教备通 版权所有</p>
          </div>
        </a-card>
      </div>
    </a-col>
  </a-row>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  WechatOutlined,
  AlipayOutlined,
  QqOutlined,
  ReloadOutlined,
} from "@ant-design/icons-vue";
import { message } from "ant-design-vue";

export default defineComponent({
  name: "AuthPage",
  components: {
    UserOutlined,
    LockOutlined,
    MailOutlined,
    WechatOutlined,
    AlipayOutlined,
    QqOutlined,
    ReloadOutlined,
  },
  setup() {
    const auth = useAuthStore();
    const currentTab = ref<"login" | "register">("login");
    const registerStep = ref(0);
    const step1Form = ref();
    const step2Form = ref();
    const agreeTerms = ref(false);
    const captchaImage = ref<string | null>(null);

    const loginForm = ref({
      username: "",
      password: "",
      captcha: "",
      remember: false,
    });

    const registerForm = ref({
      username: "",
      email: "",
      password: "",
      confirmPassword: "",
      role: "student",
    });

    const step1Rules = {
      username: [
        { required: true, message: "请输入用户名", trigger: "blur" },
        {
          min: 0,
          max: 16,
          message: "用户名长度在0到16个字符",
          trigger: "blur",
        },
      ],
      email: [
        { required: true, message: "请输入邮箱", trigger: "blur" },
        { type: "email", message: "请输入有效的邮箱地址", trigger: "blur" },
      ],
      role: [{ required: true, message: "请选择角色", trigger: "change" }],
    };

    const step2Rules = {
      password: [
        { required: true, message: "请输入密码", trigger: "blur" },
        { min: 6, max: 20, message: "密码长度在6到20个字符", trigger: "blur" },
      ],
      confirmPassword: [
        { required: true, message: "请确认密码", trigger: "blur" },
        {
          validator: (_: any, value: string) => {
            if (value !== registerForm.value.password) {
              return Promise.reject("两次输入的密码不一致");
            }
            return Promise.resolve();
          },
          trigger: "blur",
        },
      ],
    };

    const refreshCaptcha = () => {
      // 这里应该是从后端获取验证码图片的逻辑
      // 示例代码，实际应该调用API获取验证码
      captchaImage.value = "data:image/svg+xml;base64,..."; // 这里应该是实际的验证码图片数据
      message.info("验证码已刷新");
    };

    const nextStep = async () => {
      try {
        if (registerStep.value === 0) {
          await step1Form.value.validate();
        } else if (registerStep.value === 1) {
          await step2Form.value.validate();
          if (!agreeTerms.value) {
            message.warning("请先同意用户协议");
            return;
          }
        }
        registerStep.value++;
      } catch (error) {
        console.log("验证失败", error);
      }
    };

    const prevStep = () => {
      registerStep.value--;
    };

    const showAgreement = () => {
      // 这里可以弹出用户协议模态框
      message.info("显示用户协议内容");
    };

    const handleLogin = async () => {
      try {
        auth.isLoading = true;
        await auth.login(loginForm.value.username, loginForm.value.password);
        message.success("登录成功");
      } catch (error) {
        // refreshCaptcha();
      } finally {
        auth.isLoading = false;
      }
    };

    const handleRegister = async () => {
      try {
        auth.isLoading = true;
        await auth.register({
          username: registerForm.value.username,
          email: registerForm.value.email,
          password: registerForm.value.password,
          role: registerForm.value.role,
        });
        message.success("注册成功");
        // 注册成功后重置表单
        registerStep.value = 0;
        step1Form.value.resetFields();
        step2Form.value.resetFields();
        agreeTerms.value = false;
        currentTab.value = "login";
      } catch (error) {
        // 错误已在 store 中处理
      } finally {
        auth.isLoading = false;
      }
    };

    return {
      currentTab,
      loginForm,
      registerForm,
      auth,
      registerStep,
      step1Form,
      step2Form,
      step1Rules,
      step2Rules,
      agreeTerms,
      captchaImage,
      nextStep,
      prevStep,
      showAgreement,
      refreshCaptcha,
      handleLogin,
      handleRegister,
    };
  },
});
</script>

<style scoped>
.auth-section {
  min-height: 100vh;
  background-color: #f0f2f5;
}

.auth-background {
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #1890ff;
}

.bg-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.auth-content {
  max-width: 420px;
  width: 100%;
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
}

.auth-logo {
  width: 80px;
  height: 80px;
  margin-bottom: 16px;
}

.auth-system-name {
  font-size: 24px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 8px;
}

.auth-slogan {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.auth-form-container {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.captcha-image {
  height: 40px;
  width: 100%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  overflow: hidden;
}

.captcha-image img {
  height: 100%;
  width: 100%;
  object-fit: cover;
}

.forgot-password {
  float: right;
}

.register-steps {
  margin-bottom: 24px;
}

.step-content {
  min-height: 240px;
  padding: 0 8px;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
}

.agreement {
  margin: 16px 0;
  display: flex;
  align-items: center;
}

.agreement a {
  margin-left: 4px;
}

.confirm-info {
  padding: 8px;
}

.confirm-info h3 {
  text-align: center;
  margin-bottom: 16px;
}

.error-alert {
  margin-top: 16px;
}

.auth-footer {
  margin-top: 24px;
  text-align: center;
}

.social-login {
  margin: 16px 0;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.copyright {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 24px;
}
</style>
