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
  avatar?: string; // 添加头像字段
  created_at?: string; // 可选添加创建时间
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
        const response = await api.get("/profile"); // 改为调用/profile接口获取完整信息
        isAuthenticated.value = true;
        user.value = {
          id: response.data.id,
          username: response.data.username,
          email: response.data.email,
          role: response.data.role,
          signature: response.data.signature,
          avatar: response.data.avatar, // 包含头像信息
          created_at: response.data.created_at,
        };
        return true;
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
        const response = await api.post(
          "/login",
          { username, password },
          { timeout: 10000 }
        );
        console.log(response.data);
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
        // 1. 调用后端登出 API
        await api.post("/logout");

        // 2. 重置 Pinia 状态
        isAuthenticated.value = false;
        user.value = null;
        error.value = null;

        // 3. 清除 Pinia 的持久化存储（关键！）
        sessionStorage.removeItem("auth");

        // 4. 清除可能的 Token（如果你手动存储了）
        localStorage.removeItem("token");
        document.cookie =
          "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

        // 5. 强制跳转到登录页（避免路由守卫干扰）
        router.push("/login&register");
      } catch (err) {
        error.value = "登出失败";
      } finally {
        isLoading.value = false;
      }
    };
    // 添加初始化时检查后端状态的方法
    const initAuthState = async () => {
      isLoading.value = false; // 确保初始化时设置为 false
      const savedState = localStorage.getItem("auth");
      if (savedState) {
        await checkAuth(); // 验证后端 session 是否有效
      }
    };

    const updateAvatar = async (file: File) => {
      isLoading.value = true;
      try {
        const formData = new FormData();
        formData.append("avatar", file);

        const response = await api.post("/profile/update_avatar", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        if (response.status === 200 && user.value) {
          user.value.avatar = response.data.avatar; // 更新本地状态
        }
        return response.data;
      } catch (err: any) {
        error.value = err.response?.data?.message || "头像更新失败";
        throw err;
      } finally {
        isLoading.value = false;
      }
    };
    const updateProfile = async (profileData: Partial<User>) => {
      isLoading.value = true;
      try {
        const response = await api.put("/profile/update", profileData);
        if (response.status === 200 && user.value) {
          // 更新本地用户信息
          user.value = { ...user.value, ...profileData };
        }
        return response.data;
      } catch (err: any) {
        error.value = err.response?.data?.message || "资料更新失败";
        throw err;
      } finally {
        isLoading.value = false;
      }
    };

    const hasRole = (role: string) => {
      return user.value?.role === role;
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
      updateAvatar, // 新增方法
      updateProfile, // 新增方法
      hasRole, // 新增方法
    };
  },
  {
    persist: true,
  }
);

export default useAuthStore;
