<template>
  <div class="heatmap-chart">
    <div ref="chart" style="width: 100%; height: 400px"></div>
  </div>
</template>

<script>
import * as echarts from "echarts";

export default {
  name: "HeatMapChart",
  data() {
    return {
      chart: null,
      data: [
        { x: 0, y: 0, value: 1, original_id: 66 },
        { x: 1, y: 2, value: 0, original_id: 67 },
        { x: 2, y: 1, value: 1, original_id: 68 },
        { x: 3, y: 3, value: 0.87, original_id: 69 },
        { x: 4, y: 0, value: 1, original_id: 70 },
      ],
    };
  },
  mounted() {
    this.initChart();
    window.addEventListener("resize", this.resizeChart);
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.resizeChart);
    if (this.chart) {
      this.chart.dispose();
    }
  },
  methods: {
    initChart() {
      this.chart = echarts.init(this.$refs.chart);

      // 创建x轴和y轴的类目
      const xAxisData = [0, 1, 2, 3, 4];
      const yAxisData = [0, 1, 2, 3, 4];

      // 将数据转换为ECharts热力图所需的格式
      const convertedData = this.data.map((item) => {
        return [item.x, item.y, item.value];
      });

      const option = {
        tooltip: {
          position: "top",
          formatter: (params) => {
            const originalData = this.data.find(
              (d) => d.x === params.data[0] && d.y === params.data[1]
            );
            return `坐标: (${params.data[0]}, ${params.data[1]})<br>值: ${params.data[2]}<br>原始ID: ${originalData.original_id}`;
          },
        },
        grid: {
          left: "3%",
          right: "4%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "category",
          data: xAxisData,
          splitArea: {
            show: true,
          },
        },
        yAxis: {
          type: "category",
          data: yAxisData,
          splitArea: {
            show: true,
          },
        },
        visualMap: {
          min: 0,
          max: 1,
          calculable: true,
          inRange: {
            color: ["#5470c6", "#91cc75", "#fac858", "#ee6666"],
          },
          textStyle: {
            fontSize: 14,
          },
        },
        series: [
          {
            name: "热力图",
            type: "heatmap",
            data: convertedData,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: "rgba(0, 0, 0, 0.5)",
              },
            },
          },
        ],
      };

      this.chart.setOption(option);
    },
    resizeChart() {
      if (this.chart) {
        this.chart.resize();
      }
    },
  },
};
</script>

<style>
.heatmap-chart {
  width: 100%;
  height: 400px;
}
</style>
