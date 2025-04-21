<template>
  <div id="app">
    <!-- <FScreen></FScreen> -->
    <!-- <LoginAregister></LoginAregister> -->
    <router-view></router-view>
    <!-- <MindMapEditor :data="mindData" @update:data="handleDataUpdate" /> -->
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import MindMapEditor from "./components/MindMapEditor.vue";

// import FScreen from "./views/FScreen.vue";
// import LoginAregister from "./views/loginAregister.vue";
</script>

<style></style>
