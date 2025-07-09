import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import FScreen from "../views/FScreen.vue";
import LoginAregister from "../views/loginAregister.vue";
import BasicLayout from "../layouts/BasicLayout.vue";
import AdminLayout from "../layouts/AdminLayout.vue";
import HomeView from "../views/HomeView.vue";
import SmartPreparationView from "../views/SmartPreparationView.vue";
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
    path: "/admin",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "statistics",
        component: () => import("../views/admin/StatisticsView.vue"),
        meta: { menuKey: 1 },
      },
      {
        path: "ppt-manage",
        name: "ppt-manage",
        component: () => import("../views/admin/pptManage.vue"),
        meta: { menuKey: 2 },
      },
      {
        path: "user-manage",
        name: "user-manage",
        component: () => import("../views/admin/UserManage.vue"),
        meta: { menuKey: 3 },
      },
      {
        path: "class-manage",
        name: "class-manage",
        component: () => import("../views/admin/CourseClassManage.vue"),
        meta: { menuKey: 4 },
      },
      {
        path: "knowledge-base",
        name: "knowledge-base",
        component: () => import("../views/admin/AdminKnowledgeBase.vue"),
        meta: { menuKey: 5 },
      },
    ],
  },
  {
    path: "/home",
    component: BasicLayout,
    children: [
      {
        path: "",
        name: "home",
        redirect: () => {
          const authStore = useAuthStore();
          return authStore.user?.role === "teacher"
            ? "/home/t-home"
            : "/home/s-home";
        },
      },
      {
        path: "t-home",
        name: "t-home",
        component: HomeView,
        meta: { menuKey: 1 },
      },
      {
        path: "s-home",
        name: "s-home",
        component: () => import("../views/StuHomeView.vue"),
        meta: { menuKey: 1 },
      },
      {
        path: "public-courseclass/:id",
        name: "publicclass",
        component: () => import("../views/PublicCourseClassDetail.vue"),
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
          keepAlive: true, // 添加缓存标识
        },
      },
      {
        path: "s-courseclass/:id",
        name: "StuCourseClassDetail",
        component: () => import("../views/StuCourseClassDetail.vue"),
        meta: {
          menuKey: 2, // 保持在同一菜单项下
          keepAlive: true, // 添加缓存标识
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
        meta: { menuKey: 2, keepAlive: true },
      },
      {
        path: "s-course/:courseId",
        name: "s-course",
        component: () => import("../views/StudentCourseDetail.vue"),
        meta: { menuKey: 2, keepAlive: true },
      },
      {
        path: "smart-preparation",
        name: "smart-preparation",
        component: SmartPreparationView,
        meta: { menuKey: 3 },
      },
      {
        path: "teaching-design/:designId",
        name: "teaching-design",
        component: () => import("../views/TeachingDesignEdit.vue"),
        meta: { menuKey: 3 },
      },
      {
        path: "community",
        name: "community",
        component: () => import("@/views/CommunityView.vue"),
        meta: { menuKey: 4, keepAlive: true },
        children: [
          {
            path: "",
            redirect: { name: "forum-home" },
          },
          {
            path: "home",
            name: "forum-home",
            component: () => import("@/views/community/ComHomeView.vue"),
          },
          {
            path: "post-editor",
            name: "post-editor",
            component: () => import("@/views/community/PostEditor.vue"),
          },
          {
            path: "my-posts",
            name: "my-posts",
            component: () => import("@/views/community/MyPostView.vue"),
          },
          {
            path: "favorites",
            name: "favorites",
            component: () => import("@/views/community/FavoritesView.vue"),
          },
          {
            path: "posts/:id",
            name: "post-detail",
            component: () => import("@/views/community/PostDetailView.vue"),
          },
        ],
      },
      {
        path: "knowledgebase",
        name: "knowledgebase",
        component: () => import("../views/TeacherKnowledgeBase.vue"),
        meta: {
          menuKey: 5,
          requiresAuth: true,
        },
      },
      {
        path: "profile", // 修改为相对路径
        name: "profile",
        component: MyProfileView,
        meta: {
          menuKey: 6, // 可以分配一个新的菜单键
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
