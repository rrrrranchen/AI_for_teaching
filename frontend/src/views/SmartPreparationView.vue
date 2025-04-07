<template>
  <div class="smart-preparation">
    <a-row :gutter="16" class="full-height">
      <a-col :span="24" class="top-section">
        <a-row :gutter="16">
          <PreQuestionCard />
          <TeachingDesignCard />
          <a-col :span="8">
            <a-card hoverable>
              <template #cover>
                <img alt="example" src="https://example.com/coming-soon.png" />
              </template>
              <a-card-meta title="功能待开发" description="敬请期待" />
              <template #actions>
                <a-button type="primary" disabled>暂不可用</a-button>
              </template>
            </a-card>
          </a-col>
        </a-row>
      </a-col>
      <a-col :span="24" class="bottom-section">
        <!-- 下半部分留空 -->
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import PreQuestionCard from "@/components/PreQuestionCard.vue";
import TeachingDesignCard from "@/components/TeachingDesignCard.vue";

export default defineComponent({
  name: "SmartPreparationView",
  components: {
    PreQuestionCard,
    TeachingDesignCard,
  },
});
</script>
