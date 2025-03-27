import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import FScreen from "../views/FScreen.vue";
import LoginAregister from "../views/loginAregister.vue";
import BasicLayout from "../layouts/BasicLayout.vue";
import HomeView from "../views/HomeView.vue";
import MyClassView from "../views/MyClassView.vue";
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
        name: "my-class",
        component: MyClassView,
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
        path: "/profile",
        name: "profile",
        component: MyProfileView,
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

  // 如果路由需要认证但用户未登录
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // 先检查当前认证状态
    await authStore.checkAuth();

    // 如果仍然未认证，重定向到登录页
    if (!authStore.isAuthenticated) {
      return { name: "login", query: { redirect: to.fullPath } };
    }
  }

  // 如果用户已登录但访问的是登录页，重定向到首页
  if (to.name === "login" && authStore.isAuthenticated) {
    return { name: "home" };
  }
});

export default router;
