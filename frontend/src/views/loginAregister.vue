<template>
  <section class="auth-section">
    <div class="auth-background">
      <img
        src="../assets/FirstScreenbg.png"
        alt="Background"
        class="bg-image"
      />
    </div>
    <div class="auth-container">
      <div class="auth-header">
        <img src="../assets/sys_logo.png" class="auth-logo" alt="Logo" />
        <span class="auth-system-name">教备通</span>
      </div>
      <div class="auth-form-container">
        <!-- 登录表单 -->
        <div v-if="currentTab === 'login'" class="auth-form">
          <h2 class="form-title">登录</h2>
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label for="login-username">用户名</label>
              <input
                type="text"
                id="login-username"
                v-model="loginForm.username"
                required
                placeholder="请输入用户名"
                :disabled="auth.isLoading"
              />
            </div>
            <div class="form-group">
              <label for="login-password">密码</label>
              <input
                type="password"
                id="login-password"
                v-model="loginForm.password"
                required
                placeholder="请输入密码"
                :disabled="auth.isLoading"
              />
            </div>
            <button
              type="submit"
              class="form-button"
              :disabled="auth.isLoading"
            >
              {{ auth.isLoading ? "登录中..." : "登录" }}
            </button>
            <div v-if="auth.error" class="error-message">
              {{ auth.error }}
            </div>
          </form>
        </div>

        <!-- 注册表单 -->
        <div v-if="currentTab === 'register'" class="auth-form">
          <h2 class="form-title">注册</h2>
          <form @submit.prevent="handleRegister">
            <div class="form-group">
              <label for="register-username">用户名</label>
              <input
                type="text"
                id="register-username"
                v-model="registerForm.username"
                required
                placeholder="请输入用户名"
                :disabled="auth.isLoading"
              />
            </div>
            <div class="form-group">
              <label for="register-email">邮箱</label>
              <input
                type="email"
                id="register-email"
                v-model="registerForm.email"
                required
                placeholder="请输入邮箱"
                :disabled="auth.isLoading"
              />
            </div>
            <div class="form-group">
              <label for="register-password">密码</label>
              <input
                type="password"
                id="register-password"
                v-model="registerForm.password"
                required
                placeholder="请输入密码"
                :disabled="auth.isLoading"
              />
            </div>
            <div class="form-group">
              <label for="register-confirm-password">确认密码</label>
              <input
                type="password"
                id="register-confirm-password"
                v-model="registerForm.confirmPassword"
                required
                placeholder="请再次输入密码"
                :disabled="auth.isLoading"
              />
            </div>
            <div v-if="passwordMismatch" class="error-message">
              两次输入的密码不一致
            </div>
            <div v-if="auth.error" class="error-message">
              {{ auth.error }}
            </div>
            <button
              type="submit"
              class="form-button"
              :disabled="auth.isLoading || passwordMismatch"
            >
              {{ auth.isLoading ? "注册中..." : "注册" }}
            </button>
          </form>
        </div>

        <div class="auth-switch">
          <button
            class="auth-tab"
            :class="{ active: currentTab === 'login' }"
            @click="switchTab('login')"
            :disabled="auth.isLoading"
          >
            登录
          </button>
          <button
            class="auth-tab"
            :class="{ active: currentTab === 'register' }"
            @click="switchTab('register')"
            :disabled="auth.isLoading"
          >
            注册
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth";

export default defineComponent({
  name: "LoginAregister",
  setup() {
    const auth = useAuthStore();
    const currentTab = ref<"login" | "register">("login");

    const loginForm = ref({
      username: "",
      password: "",
    });

    const registerForm = ref({
      username: "",
      email: "",
      password: "",
      confirmPassword: "",
      role: "student", // 默认角色
    });

    const passwordMismatch = computed(() => {
      return (
        registerForm.value.password !== registerForm.value.confirmPassword &&
        registerForm.value.confirmPassword.length > 0
      );
    });

    const switchTab = (tab: "login" | "register") => {
      currentTab.value = tab;
      auth.error = null; // 切换时清空错误信息
    };

    const handleLogin = async () => {
      try {
        await auth.login(loginForm.value.username, loginForm.value.password);
      } catch (error) {
        // 错误已在store中处理
      }
    };

    const handleRegister = async () => {
      if (passwordMismatch.value) return;

      try {
        await auth.register({
          username: registerForm.value.username,
          email: registerForm.value.email,
          password: registerForm.value.password,
          role: registerForm.value.role,
        });
      } catch (error) {
        // 错误已在store中处理
      }
    };

    return {
      currentTab,
      loginForm,
      registerForm,
      passwordMismatch,
      auth,
      switchTab,
      handleLogin,
      handleRegister,
    };
  },
});
</script>

<style scoped>
.auth-section {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: url("../assets/FirstScreenbg.png") no-repeat center center fixed;
  background-size: cover;
}

.auth-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.bg-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  margin-bottom: 10px;
}

.auth-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 10px;
}

.auth-logo {
  width: 80px;
  height: 80px;
  margin-bottom: 1rem;
}

.auth-system-name {
  font-size: 2rem;
  font-weight: bold;
  color: #2d3748;
}

.auth-form-container {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 1rem;
  border: 1px solid #ccc;
  padding: 2rem;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.auth-switch {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}

.auth-tab {
  padding: 0.5rem 1rem;
  margin: 0 0.5rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  color: #4299e1;
  transition: all 0.3s ease;
}

.auth-tab.active {
  background-color: #4299e1;
  color: white;
  border-radius: 0.5rem;
}

.auth-tab:hover {
  color: #3c91d7;
}

.auth-form {
  display: flex;
  flex-direction: column;
}

.form-title {
  text-align: center;
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1.5rem;
  color: #2d3748;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #4a5568;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  font-size: 1rem;
  color: #4a5568;
  transition: border-color 0.3s ease;
}

.form-group input:focus {
  border-color: #4299e1;
  outline: none;
}

.form-button {
  padding: 0.75rem;
  border: none;
  background-color: #2755de;
  color: white;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease;
  display: block;
  margin: auto;
  margin-bottom: 8px;
}

.form-button:hover {
  background-color: #4c66f5;
}

.error-message {
  color: #e53e3e;
  font-size: 0.875rem;
  margin-bottom: 1rem;
  text-align: center;
}
</style>
