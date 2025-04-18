<template>
  <a-card hoverable class="teaching-design-item" @click="handleCardClick">
    <a-card-meta :title="design.title">
      <template #description>
        <div class="card-info">
          <p>{{ formatDate(design.created_at) }}</p>
        </div>
      </template>
    </a-card-meta>
  </a-card>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { useRouter } from "vue-router";

export default defineComponent({
  name: "TeachingDesignItem",
  props: {
    design: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    const router = useRouter();

    // 格式化日期
    const formatDate = (dateString: string) => {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    };

    // 点击卡片跳转到教学设计详情
    const handleCardClick = () => {
      router.push({
        path: `/home/teaching-design/${props.design.design_id}`,
        query: {
          title: props.design.title,
          default_version_id: props.design.default_version_id,
        },
      });
    };

    return {
      formatDate,
      handleCardClick,
    };
  },
});
</script>

<style scoped>
.teaching-design-item {
  background-color: #c1e1fc;
  cursor: pointer;
  transition: transform 0.3s;
  border: #8ec7f5 solid 1px;
}

.teaching-design-item:hover {
  transform: translateY(-5px);
}

.card-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}
</style>
