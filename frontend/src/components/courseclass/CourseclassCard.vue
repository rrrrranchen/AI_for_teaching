<template>
  <a-card
    class="courseclass-card"
    :hoverable="true"
    :style="{ width: '300px' }"
  >
    <template #cover>
      <img
        alt="courseclass"
        src="https://via.placeholder.com/300x180"
        class="courseclass-image"
      />
    </template>
    <a-card-meta :title="Courseclass.name">
      <template #description>
        <div class="courseclass-description">
          <p>{{ Courseclass.description }}</p>
          <div class="courseclass-details">
            <p>
              <strong>创建时间：</strong
              >{{ formatDate(Courseclass.created_at) }}
            </p>
            <p><strong>邀请码：</strong>{{ Courseclass.invite_code }}</p>
            <p v-if="Courseclass.student_count !== undefined">
              <strong>学生人数：</strong>{{ Courseclass.student_count }}
            </p>
          </div>
        </div>
      </template>
    </a-card-meta>
  </a-card>
</template>

<script setup lang="ts">
import { defineProps } from "vue";
import { Courseclass } from "@/api/courseclass";
// 简单的日期格式化函数
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
};
</script>

<style scoped>
.courseclass-card {
  margin-bottom: 20px;
}

.courseclass-image {
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.courseclass-description {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.courseclass-details p {
  margin: 0;
  font-size: 14px;
  color: #666;
}
</style>
