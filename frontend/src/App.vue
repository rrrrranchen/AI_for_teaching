<template>
  <div id="app">
    <!-- <FScreen></FScreen> -->
    <!-- <LoginAregister></LoginAregister> -->
    <router-view></router-view>
    <!-- <MindMapTest /> -->
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import MindMapTest from "./components/EChartsTest.vue";

// import FScreen from "./views/FScreen.vue";
// import LoginAregister from "./views/loginAregister.vue";
</script>

<style></style>
