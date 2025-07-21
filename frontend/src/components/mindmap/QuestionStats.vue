<template>
  <div class="question-stats-container">
    <div
      v-for="(question, qIndex) in questions"
      :key="question.id"
      class="question-item"
    >
      <div class="question-header">
        <h4>题目 {{ qIndex + 1 }} ({{ questionTypes[question.type] }})</h4>
        <div class="difficulty-tag">
          <a-tag :color="getDifficultyColor(question.difficulty)">
            {{ question.difficulty }}
          </a-tag>
        </div>
      </div>

      <div class="question-content">
        <Markdown :source="question.content" />
      </div>

      <div v-if="question.statistics" class="stats-section">
        <div class="correct-rate">
          <a-progress
            type="circle"
            :percent="question.statistics.average_correct_percentage"
            :stroke-color="
              getPercentageColor(question.statistics.average_correct_percentage)
            "
          />
          <span class="rate-label">平均正确率</span>
        </div>

        <div class="chart-container">
          <VChart
            v-if="question.type === 'choice'"
            :option="getChoiceChartOption(question)"
            class="chart"
          />
          <VChart
            v-else-if="question.type === 'fill'"
            :option="getFillChartOption(question)"
            class="chart"
          />
          <VChart
            v-else
            :option="getShortAnswerChartOption(question)"
            class="chart"
          />
        </div>

        <div
          v-if="question.type === 'fill' && question.statistics.top_errors"
          class="common-errors"
        >
          <h5>常见错误答案：</h5>
          <ul>
            <li
              v-for="(error, eIndex) in question.statistics.top_errors"
              :key="eIndex"
            >
              "{{ error.answer }}" ({{ error.percentage }}%)
            </li>
          </ul>
        </div>
      </div>

      <div v-else class="no-stats">
        <a-empty description="暂无答题统计数据" />
      </div>
    </div>
  </div>
</template>

<script>
import { use } from "echarts/core";
import { PieChart } from "echarts/charts";
import { CanvasRenderer } from "echarts/renderers";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import Markdown from "vue3-markdown-it";

use([
  PieChart,
  CanvasRenderer,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
]);

export default {
  components: { VChart, Markdown },
  props: {
    questions: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      questionTypes: {
        choice: "选择题",
        fill: "填空题",
        short_answer: "简答题",
        programming: "编程题",
        practice: "实践题",
      },
    };
  },
  methods: {
    getDifficultyColor(difficulty) {
      const map = {
        简单: "green",
        中等: "orange",
        困难: "red",
      };
      return map[difficulty] || "blue";
    },

    getPercentageColor(percent) {
      if (percent >= 80) return "#52c41a";
      if (percent >= 60) return "#faad14";
      return "#f5222d";
    },

    getChoiceChartOption(question) {
      const options = question.statistics.options || [];
      return {
        title: {
          text: "选项分布",
          left: "center",
        },
        tooltip: {
          trigger: "item",
          formatter: "{b}: {c} ({d}%)",
        },
        legend: {
          orient: "vertical",
          left: "left",
        },
        series: [
          {
            name: "选项分布",
            type: "pie",
            radius: ["40%", "70%"],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: "#fff",
              borderWidth: 2,
            },
            label: {
              show: false,
              position: "center",
            },
            emphasis: {
              label: {
                show: true,
                fontSize: "18",
                fontWeight: "bold",
              },
            },
            labelLine: {
              show: false,
            },
            data: options.map((opt) => ({
              value: opt.percentage,
              name: `选项 ${opt.option}`,
              itemStyle: {
                color: opt.is_correct ? "#52c41a" : "#ff4d4f",
              },
            })),
          },
        ],
      };
    },

    getFillChartOption(question) {
      const stats = question.statistics;
      return {
        title: {
          text: "答题情况",
          left: "center",
        },
        tooltip: {
          trigger: "item",
          formatter: "{b}: {c} ({d}%)",
        },
        series: [
          {
            name: "答题情况",
            type: "pie",
            radius: "50%",
            data: [
              {
                value: stats.correct.percentage,
                name: "正确答案",
                itemStyle: { color: "#52c41a" },
              },
              {
                value: stats.other_errors.percentage,
                name: "其他错误",
                itemStyle: { color: "#ff4d4f" },
              },
              ...stats.top_errors.map((err) => ({
                value: err.percentage,
                name: `错误: "${err.answer}"`,
                itemStyle: { color: "#fa8c16" },
              })),
            ],
          },
        ],
      };
    },

    getShortAnswerChartOption(question) {
      const ranges = question.statistics.score_ranges || [];
      return {
        title: {
          text: "得分分布",
          left: "center",
        },
        tooltip: {
          trigger: "item",
          formatter: "{b}: {c} ({d}%)",
        },
        series: [
          {
            name: "得分分布",
            type: "pie",
            radius: "50%",
            data: ranges.map((range) => ({
              value: range.percentage,
              name: range.range,
              itemStyle: {
                color: this.getRangeColor(range.range),
              },
            })),
          },
        ],
      };
    },

    getRangeColor(range) {
      const map = {
        "0-25%": "#ff4d4f",
        "25-50%": "#fa8c16",
        "50-75%": "#faad14",
        "75-100%": "#52c41a",
      };
      return map[range] || "#1890ff";
    },
  },
};
</script>

<style scoped>
.question-stats-container {
  height: 65vh;
  overflow-y: auto;
  padding: 16px;
}

.question-item {
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-content {
  margin-bottom: 16px;
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.stats-section {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
}

.correct-rate {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 120px;
}

.rate-label {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.chart-container {
  flex: 1;
  min-width: 300px;
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}

.common-errors {
  flex-basis: 100%;
  margin-top: 16px;
  padding: 12px;
  background: #fff2f0;
  border-radius: 4px;
}

.common-errors h5 {
  margin-bottom: 8px;
  color: #ff4d4f;
}

.common-errors li {
  margin-bottom: 4px;
}

.no-stats {
  padding: 24px 0;
}
</style>
