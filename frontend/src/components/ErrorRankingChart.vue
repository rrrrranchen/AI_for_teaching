<template>
  <div ref="errorRankingRef" style="width: 100%; height: 100%"></div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeUnmount, watch } from "vue";
import * as echarts from "echarts";
import questionApi from "@/api/questions";
import { ErrorRankingItem } from "@/api/questions";

export default defineComponent({
  name: "ErrorRankingChart",
  props: {
    courseId: {
      type: Number,
      required: true,
    },
  },
  setup(props) {
    const errorRankingRef = ref<HTMLElement | null>(null);
    const errorRanking = ref<ErrorRankingItem[]>([]);
    let errorRankingChart: echarts.ECharts | null = null;

    // 获取错误排行榜数据
    const fetchErrorRanking = async () => {
      try {
        const res = await questionApi.getCourseErrorRanking(props.courseId);
        errorRanking.value = res.ranking;
        initErrorRankingChart();
      } catch (error) {
        console.error("获取错误排行榜数据失败:", error);
      }
    };

    // 初始化错误排行榜图表
    const initErrorRankingChart = () => {
      if (!errorRankingRef.value) return;

      errorRankingChart = echarts.init(errorRankingRef.value);
      errorRankingChart.setOption({
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "shadow",
          },
        },
        grid: {
          left: "3%",
          right: "4%",
          bottom: "3%",
          top: "15%",
          containLabel: true,
        },
        xAxis: {
          type: "value",
          name: "错误率",
        },
        yAxis: {
          type: "category",
          data: errorRanking.value.map((item) => item.content),
        },
        series: [
          {
            name: "错误率",
            type: "bar",
            data: errorRanking.value.map((item) => item.error_rate),
            label: {
              show: true,
              position: "right",
              formatter: (params: any) => (params.value * 100).toFixed(1) + "%",
            },
          },
        ],
      });
    };

    // 窗口大小变化时重新调整图表大小
    const handleResize = () => {
      if (errorRankingChart) {
        errorRankingChart.resize();
      }
    };

    onMounted(() => {
      fetchErrorRanking();
      window.addEventListener("resize", handleResize);
    });

    onBeforeUnmount(() => {
      window.removeEventListener("resize", handleResize);
      if (errorRankingChart) {
        errorRankingChart.dispose();
        errorRankingChart = null;
      }
    });

    // 监听 courseId 变化
    watch(
      () => props.courseId,
      (newCourseId) => {
        if (newCourseId) {
          fetchErrorRanking();
        }
      }
    );

    return {
      errorRankingRef,
    };
  },
});
</script>
