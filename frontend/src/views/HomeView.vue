<template>
  <div class="home">
    <a-row :gutter="24" class="main-content">
      <!-- 左边数据统计大屏 (2/3宽度) -->
      <a-col :span="16">
        <div class="data-dashboard">
          <!-- 第一行统计卡片 -->
          <a-row :gutter="16" class="dashboard-row">
            <a-col :span="8">
              <a-card hoverable>
                <div class="stat-card">
                  <rocket-two-tone style="font-size: 36px; color: #1890ff" />
                  <div class="stat-content">
                    <div class="stat-title">智能备课平均耗时</div>
                    <div class="stat-value">33.56分钟</div>
                    <div class="stat-trend">
                      相比传统备课时间节省<arrow-down-outlined
                        style="color: #52c41a"
                      />
                      38%
                    </div>
                  </div>
                </div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card hoverable>
                <div class="stat-card">
                  <check-circle-two-tone
                    style="font-size: 36px; color: #52c41a"
                  />
                  <div class="stat-content">
                    <div class="stat-title">作业正确率</div>
                    <div class="stat-value">78.50%</div>
                    <div class="stat-trend">最近一次布置的作业</div>
                  </div>
                </div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card hoverable>
                <div class="stat-card">
                  <clock-circle-two-tone
                    style="font-size: 36px; color: #722ed1"
                  />
                  <div class="stat-content">
                    <div class="stat-title">系统使用时长</div>
                    <div class="stat-value">10.4小时/周</div>
                    <div class="stat-trend">
                      <arrow-up-outlined style="color: #52c41a" /> 8%
                    </div>
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
          <div class="carousel-section">
            <a-carousel autoplay>
              <div v-for="(image, index) in carouselImages" :key="index">
                <img
                  :src="image.src"
                  class="carousel-image"
                  alt="轮播图"
                  @click="handleCarouselClick(image.action)"
                />
              </div>
            </a-carousel>
          </div>
          <!-- 学生学习时长和正确率图表 -->
          <a-row :gutter="16">
            <!-- 学生学习时长和正确率图表 -->
            <a-col :span="12">
              <a-card
                title="学生学习时长与正确率"
                hoverable
                style="margin-top: 16px; height: 430px"
              >
                <div ref="studentChart" style="height: 340px"></div>
              </a-card>
            </a-col>

            <!-- AI资源使用占比饼图 -->
            <a-col :span="12">
              <a-card
                title="AI资源使用占比"
                hoverable
                style="margin-top: 16px; height: 430px"
              >
                <div ref="aiUsageChart" style="height: 350px"></div>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </a-col>

      <!-- 右边区域 (1/3宽度) -->
      <a-col :span="8">
        <div class="right-section">
          <!-- 日历热力图 -->
          <a-card hoverable>
            <div class="calendar-container">
              <div class="calendar-header">
                <div class="month-selector">
                  <a-button @click="prevMonth" icon="<" size="small"></a-button>
                  <div class="current-month">{{ currentMonth }}</div>
                  <a-button @click="nextMonth" icon=">" size="small"></a-button>
                </div>
              </div>
              <div class="calendar-grid">
                <div class="weekdays">
                  <div
                    v-for="day in ['日', '一', '二', '三', '四', '五', '六']"
                    :key="day"
                    class="weekday"
                  >
                    {{ day }}
                  </div>
                </div>
                <div class="days-grid">
                  <div
                    v-for="(day, index) in calendarDays"
                    :key="index"
                    class="calendar-day"
                    :class="{
                      'current-month': day.inMonth,
                      today: day.isToday,
                    }"
                    :style="{ backgroundColor: getHeatColor(day.activity) }"
                  >
                    <div class="day-number">{{ day.date }}</div>
                    <div class="activity-level">{{ day.activity }}%</div>
                  </div>
                </div>
              </div>
              <div class="calendar-legend">
                <div
                  class="legend-item"
                  v-for="(item, index) in heatLevels"
                  :key="index"
                >
                  <div
                    class="legend-color"
                    :style="{ backgroundColor: item.color }"
                  ></div>
                  <div class="legend-label">{{ item.label }}</div>
                </div>
              </div>
            </div>
          </a-card>

          <!-- 课程班列表 -->
          <div class="section-title" style="margin-top: 20px">
            <h2>我的课程班</h2>
          </div>
          <a-list
            item-layout="horizontal"
            :data-source="courseClasses"
            :loading="loading"
            class="my-classes-list"
          >
            <template #renderItem="{ item }">
              <a-list-item class="class-item">
                <a-list-item-meta>
                  <template #title>
                    <router-link :to="`/home/courseclass/${item.id}`">
                      {{ item.name }}
                    </router-link>
                  </template>
                  <template #description>
                    <span class="class-description">{{
                      item.description || "暂无描述"
                    }}</span>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <span><book-outlined /> {{ item.course_count || 0 }}课</span>
                </template>
              </a-list-item>
            </template>
            <template #loadMore>
              <div class="view-more" style="margin-top: 16px">
                <a @click="$router.push('/home/my-class')">查看全部课程 →</a>
              </div>
            </template>
          </a-list>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import {
  BookOutlined,
  RocketTwoTone,
  CheckCircleTwoTone,
  ClockCircleTwoTone,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import { getAllCourseclasses } from "@/api/courseclass";
import dayjs from "dayjs";
import * as echarts from "echarts";

export default defineComponent({
  name: "HomeView",
  components: {
    BookOutlined,
    RocketTwoTone,
    CheckCircleTwoTone,
    ClockCircleTwoTone,
    ArrowUpOutlined,
    ArrowDownOutlined,
  },
  setup() {
    const authStore = useAuthStore();
    const courseClasses = ref<any[]>([]);
    const loading = ref<boolean>(false);
    const studentChart = ref(null);
    const aiUsageChart = ref(null);

    // 学生学习数据
    const studentData = ref([
      { name: "张三", studyTime: 240, accuracy: 85 },
      { name: "李四", studyTime: 180, accuracy: 72 },
      { name: "王五", studyTime: 210, accuracy: 78 },
      { name: "赵六", studyTime: 150, accuracy: 65 },
      { name: "钱七", studyTime: 270, accuracy: 92 },
      { name: "孙八", studyTime: 190, accuracy: 68 },
    ]);

    // AI资源使用数据
    const aiUsageData = ref([
      { name: "AI问答", value: 25, color: "#1890ff" },
      { name: "教学设计生成", value: 35, color: "#52c41a" },
      { name: "教学资源生成", value: 18, color: "#722ed1" },
      { name: "题目生成", value: 12, color: "#faad14" },
      { name: "学情分析", value: 10, color: "#faad14" },
    ]);

    // 初始化图表
    const initCharts = () => {
      // 学生学习时长与正确率图表
      const studentEchart = echarts.init(studentChart.value);
      studentEchart.setOption({
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "cross",
            crossStyle: {
              color: "#999",
            },
          },
        },
        legend: {
          data: ["学习时长(分钟)", "正确率(%)"],
        },
        grid: {
          left: "3%",
          right: "4%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "category",
          data: studentData.value.map((item) => item.name),
          axisPointer: {
            type: "shadow",
          },
        },
        yAxis: [
          {
            type: "value",
            name: "学习时长(分钟)",
            min: 0,
            max: 300,
            axisLabel: {
              formatter: "{value}",
            },
          },
          {
            type: "value",
            name: "正确率(%)",
            min: 0,
            max: 100,
            axisLabel: {
              formatter: "{value}%",
            },
          },
        ],
        series: [
          {
            name: "学习时长(分钟)",
            type: "bar",
            data: studentData.value.map((item) => item.studyTime),
            itemStyle: {
              color: "#1890ff",
            },
          },
          {
            name: "正确率(%)",
            type: "line",
            yAxisIndex: 1,
            data: studentData.value.map((item) => item.accuracy),
            itemStyle: {
              color: "#52c41a",
            },
          },
        ],
      });

      // AI资源使用占比图表
      const aiEchart = echarts.init(aiUsageChart.value);
      aiEchart.setOption({
        tooltip: {
          trigger: "item",
        },
        legend: {
          top: "5%",
          left: "center",
        },
        series: [
          {
            name: "AI资源使用占比",
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
            data: aiUsageData.value,
          },
        ],
      });

      // 窗口大小变化时重新调整图表大小
      window.addEventListener("resize", function () {
        studentEchart.resize();
        aiEchart.resize();
      });
    };

    // 日历热力图相关数据
    const currentDate = ref(dayjs());
    const currentMonth = computed(() => currentDate.value.format("YYYY年MM月"));

    // 热力等级配置
    const heatLevels = ref([
      { level: 0, label: "无活动", color: "#ebedf0" },
      { level: 1, label: "低活跃度", color: "#c6e48b" },
      { level: 2, label: "中等活跃", color: "#7bc96f" },
      { level: 3, label: "高活跃度", color: "#239a3b" },
      { level: 4, label: "非常高", color: "#196127" },
    ]);

    const calendarDays = computed(() => {
      const startOfMonth = currentDate.value.startOf("month");
      const endOfMonth = currentDate.value.endOf("month");
      const startDay = startOfMonth.day();
      const daysInMonth = endOfMonth.date();
      const today = dayjs();
      const yesterday = today.subtract(1, "day");

      // 生成当月的日期数组
      const days = [];
      for (let i = 1; i <= daysInMonth; i++) {
        const date = startOfMonth.date(i);
        const isPast = date.isBefore(today, "day");
        const isToday = date.isSame(today, "day");
        const isYesterday = date.isSame(yesterday, "day");

        // 只伪造今天之前的日期数据
        let activity = 0;
        if (isPast) {
          activity = Math.floor(Math.random() * 100);
        } else if (isYesterday) {
          activity = Math.floor(Math.random() * 100);
        }

        days.push({
          date: i,
          inMonth: true,
          isToday: isToday,
          activity: activity,
        });
      }
      // 填充上个月的空白
      const prevMonthDays = startDay;
      for (let i = 0; i < prevMonthDays; i++) {
        days.unshift({
          date: startOfMonth.subtract(prevMonthDays - i, "day").date(),
          inMonth: false,
          isToday: false,
          activity: 0,
        });
      }

      // 填充下个月的空白
      const totalCells = 42; // 6行*7天
      const nextMonthDays = totalCells - days.length;
      for (let i = 1; i <= nextMonthDays; i++) {
        days.push({
          date: i,
          inMonth: false,
          isToday: false,
          activity: 0,
        });
      }

      return days;
    });

    // 根据活跃度获取热力颜色
    const getHeatColor = (activity: number) => {
      if (activity === 0) return heatLevels.value[0].color;
      if (activity < 20) return heatLevels.value[1].color;
      if (activity < 50) return heatLevels.value[2].color;
      if (activity < 80) return heatLevels.value[3].color;
      return heatLevels.value[4].color;
    };

    // 月份切换
    const prevMonth = () => {
      currentDate.value = currentDate.value.subtract(1, "month");
    };

    const nextMonth = () => {
      currentDate.value = currentDate.value.add(1, "month");
    };

    // 获取课程班数据
    const loadCourseClasses = async () => {
      try {
        loading.value = true;
        const data = await getAllCourseclasses();
        courseClasses.value = data.slice(0, 4);
      } catch (error) {
        console.error("获取课程班失败:", error);
      } finally {
        loading.value = false;
      }
    };

    onMounted(() => {
      initCharts();
      if (authStore.isAuthenticated) {
        loadCourseClasses();
      }
    });

    const carouselImages = ref([
      {
        src: require("@/assets/carousel1.png"),
        action: () => (window.location.href = "/home"),
      },
      {
        src: require("@/assets/aiforedu.png"),
        action: () => (window.location.href = "/home/smart-preparation"),
      },
      {
        src: require("@/assets/community.png"),
        action: () => (window.location.href = "/home/community"),
      },
    ]);

    // 处理轮播图点击
    const handleCarouselClick = (action: () => void) => {
      action();
    };

    return {
      courseClasses,
      studentData,
      aiUsageData,
      currentMonth,
      calendarDays,
      heatLevels,
      getHeatColor,
      prevMonth,
      nextMonth,
      loading,
      studentChart,
      aiUsageChart,
      carouselImages,
      handleCarouselClick,
    };
  },
});
</script>

<style scoped>
.home {
  padding: 20px;
  background: #edf6fbcc;
  height: 100%;
}

.main-content {
  height: calc(95vh - 48px);
}

.data-dashboard {
  border-radius: 12px;
  height: 100%;
}

.stat-card {
  display: flex;
  align-items: center;
  /* background-color: #f9fbff; */
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

.carousel-section {
  margin-top: 32px;
  margin-bottom: 32px;

  .carousel-image {
    width: 100%;
    height: 300px;
    object-fit: cover;
    cursor: pointer;
    border-radius: 8px;
    transition: transform 0.3s;
  }
}

.right-section {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.calendar-container {
  .calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .month-selector {
      display: flex;
      align-items: center;

      .current-month {
        font-size: 16px;
        font-weight: 500;
        margin: 0 12px;
      }
    }
  }

  .calendar-grid {
    background: #fff;
    border-radius: 8px;
    overflow: hidden;

    .weekdays {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      background: #fafafa;
      border-bottom: 1px solid #f0f0f0;

      .weekday {
        text-align: center;
        padding: 8px;
        font-size: 14px;
        color: #595959;
      }
    }

    .days-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 1px;
      background: #f0f0f0;

      .calendar-day {
        aspect-ratio: 1/1;
        background: #fff;
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;

        &:not(.current-month) {
          background: #fafafa;

          .day-number,
          .activity-level {
            color: #bfbfbf;
          }
        }

        &.today {
          border: 2px solid #1890ff;
        }

        .day-number {
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 4px;
        }

        .activity-level {
          font-size: 10px;
          color: #8c8c8c;
        }
      }
    }
  }

  .calendar-legend {
    display: flex;
    justify-content: center;
    margin-top: 16px;

    .legend-item {
      display: flex;
      align-items: center;
      margin: 0 8px;

      .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 3px;
        margin-right: 4px;
      }

      .legend-label {
        font-size: 12px;
        color: #8c8c8c;
      }
    }
  }
}

.section-title {
  margin-bottom: 16px;

  h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
    color: #1f1f1f;
  }
}

.my-classes-list {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 16px;

  .class-item {
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;

    :deep(.ant-list-item-meta-title) {
      font-weight: 500;
    }

    .class-description {
      color: #8c8c8c;
      font-size: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 1;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.view-more {
  text-align: center;
}

@media (max-width: 992px) {
  .ant-col-16,
  .ant-col-8 {
    width: 100%;
  }

  .right-section {
    margin-top: 24px;
  }
}
</style>
