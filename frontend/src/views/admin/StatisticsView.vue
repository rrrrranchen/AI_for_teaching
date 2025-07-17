<template>
  <a-layout>
    <a-layout-content style="padding: 20px; background: #f0f2f5">
      <a-row :gutter="16">
        <!-- 顶部指标卡 -->
        <a-col :span="6">
          <a-card hoverable>
            <div class="stat-card">
              <user-outlined style="font-size: 36px; color: #1890ff" />
              <div class="stat-content">
                <div class="stat-title">学生总数</div>
                <div class="stat-value">1,842</div>
                <div class="stat-trend">
                  <arrow-up-outlined style="color: #52c41a" /> 12.5%
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card hoverable>
            <div class="stat-card">
              <team-outlined style="font-size: 36px; color: #722ed1" />
              <div class="stat-content">
                <div class="stat-title">教师总数</div>
                <div class="stat-value">128</div>
                <div class="stat-trend">
                  <arrow-up-outlined style="color: #52c41a" /> 8.3%
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card hoverable>
            <div class="stat-card">
              <dashboard-outlined style="font-size: 36px; color: #13c2c2" />
              <div class="stat-content">
                <div class="stat-title">教师活跃度</div>
                <div class="stat-value">86.5%</div>
                <div class="stat-trend">
                  <arrow-up-outlined style="color: #52c41a" /> 5.2%
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card hoverable>
            <div class="stat-card">
              <clock-circle-outlined style="font-size: 36px; color: #fa8c16" />
              <div class="stat-content">
                <div class="stat-title">备课平均用时</div>
                <div class="stat-value">42分钟</div>
                <div class="stat-trend">
                  <arrow-down-outlined style="color: #f5222d" /> 15.7%
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="16" style="margin-top: 20px">
        <!-- 学生学习活跃曲线 -->
        <a-col :span="16">
          <a-card title="学生学习活跃曲线（最近30天）" hoverable>
            <div ref="studentActivityChart" style="height: 350px"></div>
          </a-card>
        </a-col>

        <!-- AI教学助手使用情况 -->
        <a-col :span="8">
          <a-card title="AI教学助手使用情况" hoverable>
            <div ref="aiUsageChart" style="height: 350px"></div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="16" style="margin-top: 20px">
        <!-- 学生学习排行榜 -->
        <a-col :span="12">
          <a-card title="学生学习排行榜（本周）" hoverable>
            <a-table
              :columns="rankColumns"
              :data-source="studentRankData"
              :pagination="false"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'rank'">
                  <a-tag :color="getRankColor(record.rank)">
                    {{ record.rank }}
                  </a-tag>
                </template>
                <template v-if="column.key === 'progress'">
                  <a-progress
                    :percent="
                      (record.studyHours / maxStudyHours).toFixed(3) * 100
                    "
                    :stroke-color="
                      getProgressColor(
                        (record.studyHours / maxStudyHours) * 100
                      )
                    "
                    size="small"
                  />
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>

        <!-- 热门课程分布 -->
        <a-col :span="12">
          <a-card title="热门课程分布" hoverable>
            <div ref="courseDistributionChart" style="height: 350px"></div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="16" style="margin-top: 20px">
        <!-- 教师备课时间分布 -->
        <a-col :span="12">
          <a-card title="教师备课时间分布" hoverable>
            <div ref="preparationTimeChart" style="height: 300px"></div>
          </a-card>
        </a-col>

        <!-- 系统健康状态 -->
        <a-col :span="12">
          <a-card title="系统健康状态" hoverable>
            <div class="system-health">
              <a-row>
                <a-col
                  :span="12"
                  v-for="(item, index) in systemHealth"
                  :key="index"
                >
                  <div class="health-item">
                    <div class="health-label">{{ item.label }}</div>
                    <a-progress
                      :percent="item.value"
                      :status="item.status"
                      :stroke-color="item.color"
                    />
                    <div class="health-value">{{ item.value }}%</div>
                  </div>
                </a-col>
              </a-row>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-layout-content>
  </a-layout>
</template>

<script>
import { ref, onMounted } from "vue";
import * as echarts from "echarts";
import {
  UserOutlined,
  TeamOutlined,
  DashboardOutlined,
  ClockCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from "@ant-design/icons-vue";

export default {
  components: {
    UserOutlined,
    TeamOutlined,
    DashboardOutlined,
    ClockCircleOutlined,
    ArrowUpOutlined,
    ArrowDownOutlined,
  },
  setup() {
    // 学生学习排行榜数据
    const studentRankData = ref([
      { key: "1", rank: 1, name: "张三", studyHours: 28.5, course: "高等数学" },
      { key: "2", rank: 2, name: "李四", studyHours: 26.0, course: "线性代数" },
      { key: "3", rank: 3, name: "王五", studyHours: 24.5, course: "概率统计" },
      { key: "4", rank: 4, name: "赵六", studyHours: 22.0, course: "数据结构" },
      { key: "5", rank: 5, name: "钱七", studyHours: 20.5, course: "算法设计" },
      {
        key: "6",
        rank: 6,
        name: "孙八",
        studyHours: 18.0,
        course: "计算机组成",
      },
      { key: "7", rank: 7, name: "周九", studyHours: 16.5, course: "操作系统" },
      {
        key: "8",
        rank: 8,
        name: "吴十",
        studyHours: 15.0,
        course: "计算机网络",
      },
    ]);

    const maxStudyHours = Math.max(
      ...studentRankData.value.map((item) => item.studyHours)
    );

    // 排行榜表格列配置
    const rankColumns = ref([
      { title: "排名", key: "rank", dataIndex: "rank", width: 80 },
      { title: "学生姓名", key: "name", dataIndex: "name" },
      { title: "学习时长(小时)", key: "studyHours", dataIndex: "studyHours" },
      { title: "主修课程", key: "course", dataIndex: "course" },
      { title: "进度", key: "progress" },
    ]);

    // 系统健康状态数据
    const systemHealth = ref([
      { label: "AI响应速度", value: 98, status: "active", color: "#52c41a" },
      { label: "系统稳定性", value: 99.5, status: "active", color: "#52c41a" },
      { label: "资源使用率", value: 65, status: "active", color: "#faad14" },
      { label: "数据准确性", value: 97, status: "active", color: "#52c41a" },
    ]);

    // 图表引用
    const studentActivityChart = ref(null);
    const aiUsageChart = ref(null);
    const courseDistributionChart = ref(null);
    const preparationTimeChart = ref(null);

    // 初始化图表
    const initCharts = () => {
      // 学生学习活跃曲线
      const activityChart = echarts.init(studentActivityChart.value);
      activityChart.setOption({
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "shadow",
          },
        },
        legend: {
          data: ["活跃学生数", "学习时长(小时)"],
        },
        grid: {
          left: "3%",
          right: "4%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "category",
          data: Array.from({ length: 30 }, (_, i) => `${i + 1}日`),
        },
        yAxis: [
          {
            type: "value",
            name: "活跃学生数",
            position: "left",
          },
          {
            type: "value",
            name: "学习时长(小时)",
            position: "right",
          },
        ],
        series: [
          {
            name: "活跃学生数",
            type: "line",
            smooth: true,
            data: Array.from(
              { length: 30 },
              () => Math.floor(Math.random() * 500) + 800
            ),
            itemStyle: {
              color: "#1890ff",
            },
          },
          {
            name: "学习时长(小时)",
            type: "bar",
            yAxisIndex: 1,
            data: Array.from(
              { length: 30 },
              () => Math.floor(Math.random() * 2000) + 3000
            ),
            itemStyle: {
              color: "#13c2c2",
            },
          },
        ],
      });

      // AI教学助手使用情况
      const aiChart = echarts.init(aiUsageChart.value);
      aiChart.setOption({
        tooltip: {
          trigger: "item",
        },
        legend: {
          top: "5%",
          left: "center",
        },
        series: [
          {
            name: "AI使用情况",
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
            data: [
              { value: 1048, name: "智能备课" },
              { value: 735, name: "题目生成" },
              { value: 580, name: "学情分析" },
              { value: 484, name: "智能问答" },
              { value: 300, name: "其他功能" },
            ],
          },
        ],
      });

      // 热门课程分布
      const courseChart = echarts.init(courseDistributionChart.value);
      courseChart.setOption({
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
          containLabel: true,
        },
        xAxis: {
          type: "value",
        },
        yAxis: {
          type: "category",
          data: [
            "高等数学",
            "线性代数",
            "概率统计",
            "数据结构",
            "算法设计",
            "计算机组成",
            "操作系统",
            "计算机网络",
          ],
        },
        series: [
          {
            name: "学习人数",
            type: "bar",
            data: [320, 302, 301, 234, 210, 198, 186, 150],
            itemStyle: {
              color: function (params) {
                const colorList = [
                  "#c23531",
                  "#2f4554",
                  "#61a0a8",
                  "#d48265",
                  "#91c7ae",
                  "#749f83",
                  "#ca8622",
                  "#bda29a",
                ];
                return colorList[params.dataIndex];
              },
            },
          },
        ],
      });

      // 教师备课时间分布
      const prepChart = echarts.init(preparationTimeChart.value);
      prepChart.setOption({
        tooltip: {
          trigger: "item",
          formatter: "{a} <br/>{b}: {c} ({d}%)",
        },
        legend: {
          orient: "vertical",
          left: 10,
          data: [
            "0-30分钟",
            "30-60分钟",
            "60-90分钟",
            "90-120分钟",
            "120分钟以上",
          ],
        },
        series: [
          {
            name: "备课时间分布",
            type: "pie",
            radius: ["50%", "70%"],
            avoidLabelOverlap: false,
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
            data: [
              { value: 335, name: "0-30分钟" },
              { value: 310, name: "30-60分钟" },
              { value: 234, name: "60-90分钟" },
              { value: 135, name: "90-120分钟" },
              { value: 154, name: "120分钟以上" },
            ],
          },
        ],
      });

      // 窗口大小变化时重新调整图表大小
      window.addEventListener("resize", function () {
        activityChart.resize();
        aiChart.resize();
        courseChart.resize();
        prepChart.resize();
      });
    };

    // 获取排名颜色
    const getRankColor = (rank) => {
      if (rank === 1) return "#f5222d";
      if (rank === 2) return "#fa8c16";
      if (rank === 3) return "#faad14";
      return "#d9d9d9";
    };

    // 获取进度条颜色
    const getProgressColor = (percent) => {
      if (percent > 90) return "#52c41a";
      if (percent > 70) return "#13c2c2";
      if (percent > 50) return "#1890ff";
      if (percent > 30) return "#722ed1";
      return "#fa8c16";
    };

    onMounted(() => {
      initCharts();
    });

    return {
      studentRankData,
      rankColumns,
      systemHealth,
      maxStudyHours,
      studentActivityChart,
      aiUsageChart,
      courseDistributionChart,
      preparationTimeChart,
      getRankColor,
      getProgressColor,
    };
  },
};
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
}

.stat-content {
  margin-left: 16px;
}

.stat-title {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin: 4px 0;
}

.stat-trend {
  font-size: 12px;
}

.health-item {
  padding: 10px;
}

.health-label {
  margin-bottom: 8px;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.health-value {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  text-align: right;
}
</style>
