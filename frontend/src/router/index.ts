import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import FScreen from "../views/FScreen.vue";
import LoginAregister from "../views/loginAregister.vue";
import BasicLayout from "../layouts/BasicLayout.vue";
import HomeView from "../views/HomeView.vue";
import SmartPreparationView from "../views/SmartPreparationView.vue";
import CommunityView from "../views/CommunityView.vue";
import MyProfileView from "../views/MyProfile.vue";
import { useAuthStore } from "@/stores/auth";
const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "firstscreen",
    component: FScreen,
  },
  {
    path: "/login&register",
    name: "login&register",
    component: LoginAregister,
  },
  {
    path: "/home",
    component: BasicLayout,
    children: [
      {
        path: "",
        name: "home",
        component: HomeView,
        meta: { menuKey: 1 },
      },
      {
        path: "my-class",
        redirect: () => {
          const authStore = useAuthStore();
          return authStore.user?.role === "teacher"
            ? "/home/t-class"
            : "/home/s-class";
        },
      },
      {
        path: "t-class",
        name: "t-class",
        component: () => import("../views/TeacherMyClass.vue"),
        meta: { menuKey: 2 },
      },
      {
        path: "s-class",
        name: "s-class",
        component: () => import("../views/StudentMyClass.vue"),
        meta: { menuKey: 2 },
      },
      {
        path: "courseclass/:id",
        name: "CourseClassDetail",
        component: () => import("../views/CourseClassDetail.vue"),
        meta: {
          menuKey: 2, // 保持在同一菜单项下
        },
      },
      {
        path: "course/:courseId",
        name: "CourseDetail",
        redirect: () => {
          const authStore = useAuthStore();
          return authStore.user?.role === "teacher"
            ? "/home/t-course/:courseId"
            : "/home/s-course/:courseId";
        },
      },
      {
        path: "t-course/:courseId",
        name: "t-course",
        component: () => import("../views/TeacherCourseDetail.vue"),
        meta: { menuKey: 2 },
      },
      {
        path: "s-course/:courseId",
        name: "s-course",
        component: () => import("../views/StudentCourseDetail.vue"),
        meta: { menuKey: 2 },
      },
      {
        path: "smart-preparation",
        name: "smart-preparation",
        component: SmartPreparationView,
        meta: { menuKey: 3 },
      },
      {
        path: "community",
        name: "community",
        component: CommunityView,
        meta: { menuKey: 4 },
      },
      {
        path: "profile", // 修改为相对路径
        name: "profile",
        component: MyProfileView,
        meta: {
          menuKey: 5, // 可以分配一个新的菜单键
          requiresAuth: true, // 需要登录
        },
      },
    ],
  },
  {
    path: "/about",
    name: "about",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/AboutView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  console.log(
    "Navigation to:",
    to.name,
    "Auth state:",
    authStore.isAuthenticated
  );

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    console.log("Checking auth...");
    await authStore.checkAuth();
    if (!authStore.isAuthenticated) {
      console.log("Redirecting to login");
      return {
        name: "login&register",
        query: { redirect: to.fullPath },
      };
    }
  }

  // if (to.name === "login&register" && authStore.isAuthenticated) {
  //   console.log("Already authenticated, redirecting home");
  //   return { name: "home" };
  // }
});

export default router;
