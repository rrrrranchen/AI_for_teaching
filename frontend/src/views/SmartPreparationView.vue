<template>
  <div class="smart-preparation">
    <a-row :gutter="16" class="full-height">
      <a-col :span="24" class="top-section">
        <a-row :gutter="16">
          <PreQuestionCard />
          <TeachingDesignCard />
          <PostQuestionCard />
        </a-row>
      </a-col>
      <a-col :span="24" class="bottom-section">
        <div class="teaching-design-container">
          <h1 style="font-weight: bold; font-size: 20px; margin-top: 10px">
            我的教学设计
          </h1>
          <div class="teaching-design-cards" v-if="teachingDesigns.length > 0">
            <TeachingDesignItem
              v-for="design in teachingDesigns"
              :key="design.design_id"
              :design="design"
              class="teaching-design-item"
            />
          </div>
          <div v-else class="empty-state">
            <p>暂无教学设计，点击上方卡片开始创建！</p>
          </div>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from "vue";
import { getMyDesigns, type TeachingDesign } from "@/api/teachingdesign";
import PreQuestionCard from "@/components/PreQuestionCard.vue";
import TeachingDesignCard from "@/components/TeachingDesignCard.vue";
import PostQuestionCard from "@/components/PostQuestionCard.vue";
import TeachingDesignItem from "@/components/TeachingDesignItem.vue";

export default defineComponent({
  name: "SmartPreparationView",
  components: {
    PreQuestionCard,
    TeachingDesignCard,
    PostQuestionCard,
    TeachingDesignItem,
  },
  setup() {
    const teachingDesigns = ref<TeachingDesign[]>([]);

    // 获取当前用户的教学设计
    const loadTeachingDesigns = async () => {
      try {
        teachingDesigns.value = await getMyDesigns();
      } catch (error) {
        console.error("获取教学设计失败", error);
      }
    };

    onMounted(() => {
      loadTeachingDesigns();
    });

    return {
      teachingDesigns,
    };
  },
});
</script>

<style scoped>
.smart-preparation {
  padding: 20px;
}

.teaching-design-container {
  margin-top: 20px;
}

.teaching-design-cards {
  display: flex;
  overflow-x: auto;
  gap: 16px;
  padding: 10px 0;
}

.teaching-design-item {
  flex: 0 0 auto;
  width: 280px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>
