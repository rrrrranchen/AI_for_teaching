import { defineStore } from "pinia";
import api from "@/request";
import { ref } from "vue";
import { useRouter } from "vue-router";

interface User {
  id: number;
  username: string;
  email: string;
  role: "student" | "teacher";
  signature?: string;
}

export const useAuthStore = defineStore(
  "auth",
  () => {
    const user = ref<User | null>(null);
    const isAuthenticated = ref(false);
    const isLoading = ref(false);
    const error = ref<string | null>(null);
    const router = useRouter();

    const checkAuth = async () => {
      isLoading.value = true;
      try {
        const response = await api.get("/check_login");
        isAuthenticated.value = response.data.isLoggedIn;
        if (response.data.isLoggedIn && response.data.user) {
          user.value = response.data.user;
        }
        return isAuthenticated.value;
      } catch (err) {
        isAuthenticated.value = false;
        user.value = null;
        return false;
      } finally {
        isLoading.value = false;
      }
    };

    const login = async (username: string, password: string) => {
      isLoading.value = true;
      error.value = null;
      try {
        const response = await api.post("/login", { username, password });
        if (response.status === 200) {
          await checkAuth();
          router.push("/home"); // 登录成功后跳转首页
        }
      } catch (err: any) {
        error.value = err.response?.data?.message || "登录失败，请重试";
        throw err;
      } finally {
        isLoading.value = false;
      }
    };

    const register = async (formData: {
      username: string;
      email: string;
      password: string;
      role?: string;
      signature?: string;
    }) => {
      isLoading.value = true;
      error.value = null;
      try {
        const response = await api.post("/register", formData);
        if (response.status === 201) {
          // 注册成功后自动登录
          await login(formData.username, formData.password);
        }
      } catch (err: any) {
        error.value = err.response?.data?.message || "注册失败，请重试";
        throw err;
      } finally {
        isLoading.value = false;
      }
    };

    const logout = async () => {
      isLoading.value = true;
      try {
        await api.post("/logout");
        isAuthenticated.value = false;
        user.value = null;
        router.push("/login");
      } catch (err) {
        error.value = "登出失败";
      } finally {
        isLoading.value = false;
      }
    };
    // 添加初始化时检查后端状态的方法
    const initAuthState = async () => {
      const savedState = localStorage.getItem("auth");
      if (savedState) {
        await checkAuth(); // 验证后端 session 是否有效
      }
    };

    return {
      user,
      isAuthenticated,
      isLoading,
      error,
      checkAuth,
      login,
      register,
      logout,
      initAuthState,
    };
  },
  {
    persist: true,
  }
);
