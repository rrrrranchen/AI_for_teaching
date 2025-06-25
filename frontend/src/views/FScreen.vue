<template>
  <section class="hero-section">
    <div class="hero-content">
      <div class="logo-container">
        <!-- Logo 图片 -->
        <img src="../assets/sys_logo.png" class="logo" alt="Logo" />

        <!-- 系统名称 -->
        <span class="system-name">教备通</span>
      </div>
      <h1 class="hero-title">
        让教师备课更简单<span class="highlight">更智能</span>
      </h1>
      <p class="hero-description">智能生成，轻松掌握教师备课的更佳方案。</p>
      <a @click="goToLoginRegister" class="hero-button">
        注册/登录
        <svg
          class="hero-arrow"
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M7.5 15L11.0858 11.4142C11.7525 10.7475 12.0858 10.4142 12.0858 10C12.0858 9.58579 11.7525 9.25245 11.0858 8.58579L7.5 5"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </a>
      <div class="dashboard-image-container">
        <img
          src="@/assets/fs_system.png"
          alt="Dashboard image"
          class="dashboard-image"
        />
      </div>
    </div>
  </section>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { useRouter } from "vue-router";

export default defineComponent({
  name: "FScreen",
  setup() {
    const router = useRouter();

    const goToLoginRegister = () => {
      console.log("Navigating to /login&register");
      router
        .push("/login&register")
        .then(() => {
          console.log("Navigation complete");
        })
        .catch((err) => {
          console.error("Navigation failed:", err);
        });
    };

    return {
      goToLoginRegister,
    };
  },
});
</script>

<style scoped>
.hero-section {
  padding-top: 10vh;
  padding-bottom: 20vh;
  background: url("../assets/FirstScreenbg.png") no-repeat center center fixed;
  background-size: cover;
  height: 100vh;
  width: 100%;
}

.hero-content {
  max-width: 7xl;
  padding-left: 1rem;
  padding-right: 1rem;
  margin-left: auto;
  margin-right: auto;
  text-align: center;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.logo {
  width: 100px;
  height: 100px;
}

.system-name {
  font-size: 2.5rem;
  font-weight: bold;
  color: #2d3748;
}

.hero-title {
  max-width: 40rem;
  margin-left: auto;
  margin-right: auto;
  font-family: "Manrope", sans-serif;
  font-weight: bold;
  font-size: 2.5rem;
  color: #2d3748;
  margin-bottom: 1.25rem;
}

.hero-title .highlight {
  color: #2755de;
}

.hero-description {
  max-width: 28rem;
  margin-left: auto;
  margin-right: auto;
  font-size: 1rem;
  font-weight: normal;
  line-height: 1.5;
  color: #a0aec0;
  margin-bottom: 2.25rem;
}

.hero-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding-top: 1rem;
  padding-bottom: 1rem;
  padding-left: 2.5rem;
  padding-right: 2.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #ffffff;
  background-color: #2755de;
  border-radius: 9999px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  transition: all 0.5s ease;
  margin-bottom: 1rem;
  text-decoration: none;
}

.hero-button:hover {
  background-color: #4c66f5;
}

.hero-arrow {
  margin-left: 0.5rem;
}

.dashboard-image-container {
  display: flex;
  justify-content: center;
}

.dashboard-image {
  border-top-left-radius: 1.5rem;
  border-top-right-radius: 1.5rem;
  height: auto;
  width: 70%;
  object-fit: cover;
}
</style>
