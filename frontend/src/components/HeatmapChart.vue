<template>
  <div ref="heatmapRef" style="width: 100%; height: 100%"></div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeUnmount, watch } from "vue";
import * as echarts from "echarts";
import questionApi from "@/api/questions";
import { HeatmapDataItem } from "@/api/questions";

export default defineComponent({
  name: "HeatmapChart",
  props: {
    courseId: {
      type: Number,
      required: true,
    },
  },
  setup(props) {
    const heatmapRef = ref<HTMLElement | null>(null);
    const heatmapData = ref<HeatmapDataItem[]>([]);
    let heatmapChart: echarts.ECharts | null = null;

    // 获取热力图数据
    const fetchHeatmapData = async () => {
      try {
        const res = await questionApi.getCourseHeatmapData(props.courseId);
        heatmapData.value = res.heatmap_data;
        initHeatmapChart();
      } catch (error) {
        console.error("获取热力图数据失败:", error);
      }
    };

    // 初始化热力图
    const initHeatmapChart = () => {
      if (!heatmapRef.value) return;

      // 生成x轴和y轴的类别数据
      const xCategories = Array.from(
        new Set(heatmapData.value.map((item) => item.x))
      ).sort((a, b) => a - b);
      const yCategories = Array.from(
        new Set(heatmapData.value.map((item) => item.y))
      ).sort((a, b) => a - b);

      heatmapChart = echarts.init(heatmapRef.value);
      heatmapChart.setOption({
        tooltip: {},
        xAxis: {
          type: "category",
          data: xCategories, // 使用类别轴
        },
        yAxis: {
          type: "category",
          data: yCategories, // 使用类别轴
        },
        visualMap: {
          min: 0,
          max: 1,
          text: ["高", "低"],
          inRange: {
            color: ["#d94e5d", "#eac736", "#50a3ba"],
          },
          calculable: true,
        },
        series: [
          {
            name: "正确率",
            type: "heatmap",
            data: heatmapData.value.map((item) => [item.x, item.y, item.value]),
            label: {
              show: true,
              formatter: (params: any) => params.value[2].toFixed(2),
            },
          },
        ],
      });
    };

    // 窗口大小变化时重新调整图表大小
    const handleResize = () => {
      if (heatmapChart) {
        heatmapChart.resize();
      }
    };

    onMounted(() => {
      fetchHeatmapData();
      window.addEventListener("resize", handleResize);
    });

    onBeforeUnmount(() => {
      window.removeEventListener("resize", handleResize);
      if (heatmapChart) {
        heatmapChart.dispose();
        heatmapChart = null;
      }
    });

    // 监听 courseId 变化
    watch(
      () => props.courseId,
      (newCourseId) => {
        if (newCourseId) {
          fetchHeatmapData();
        }
      }
    );

    return {
      heatmapRef,
    };
  },
});
</script>
