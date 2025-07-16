<template>
  <div class="home">
    <a-row :gutter="24" class="main-content">
      <!-- 左边数据统计大屏 (2/3宽度) -->
      <a-col :span="16">
        <div class="data-dashboard">
          <!-- 第一行统计卡片 -->
          <a-row :gutter="24" class="dashboard-row">
            <a-col :span="8">
              <a-card class="stat-card">
                <div class="stat-header">
                  <rocket-two-tone
                    :style="{ fontSize: '24px', color: '#1890ff' }"
                  />
                  <h3>智能备课平均耗时</h3>
                </div>
                <div class="stat-value">42分钟</div>
                <div class="stat-trend">
                  相对传统备课，平均减少 <span class="positive">38%</span>
                </div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card class="stat-card">
                <div class="stat-header">
                  <check-circle-two-tone
                    :style="{ fontSize: '24px', color: '#52c41a' }"
                  />
                  <h3>作业正确率</h3>
                </div>
                <div class="stat-value">78.5%</div>
                <div class="stat-trend">最近一次布置的作业</div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card class="stat-card">
                <div class="stat-header">
                  <clock-circle-two-tone
                    :style="{ fontSize: '24px', color: '#722ed1' }"
                  />
                  <h3>系统使用时长</h3>
                </div>
                <div class="stat-value">12.4小时/周</div>
                <div class="stat-trend">
                  较上月增加 <span class="positive">8%</span>
                </div>
              </a-card>
            </a-col>
          </a-row>

          <!-- AI资源使用统计 -->
          <a-card title="AI资源使用统计" class="chart-card">
            <div class="chart-container">
              <div class="ai-resource-chart">
                <div
                  class="resource-bar"
                  v-for="(item, index) in aiUsageData"
                  :key="index"
                >
                  <div class="resource-label">{{ item.name }}</div>
                  <div class="bar-container">
                    <div
                      class="bar-fill"
                      :style="{
                        width: item.percentage + '%',
                        background: item.color,
                      }"
                    ></div>
                    <div class="bar-value">{{ item.count }}次</div>
                  </div>
                </div>
              </div>
            </div>
          </a-card>

          <!-- 学生数据图表 -->
          <a-row :gutter="24" class="dashboard-row">
            <a-col :span="12">
              <a-card title="学生活跃度分布" class="chart-card">
                <div class="chart-container">
                  <div class="activity-chart">
                    <div
                      v-for="(item, index) in activityData"
                      :key="index"
                      class="activity-item"
                    >
                      <div class="activity-label">{{ item.label }}</div>
                      <div class="activity-bar">
                        <div
                          class="activity-fill"
                          :style="{
                            width: item.percentage + '%',
                            background: item.color,
                          }"
                        ></div>
                      </div>
                      <div class="activity-value">{{ item.value }}人</div>
                    </div>
                  </div>
                </div>
              </a-card>
            </a-col>
            <a-col :span="12">
              <a-card title="学习进度分布" class="chart-card">
                <div class="chart-container">
                  <div class="progress-chart">
                    <div
                      v-for="(item, index) in progressData"
                      :key="index"
                      class="progress-item"
                    >
                      <div class="progress-label">{{ item.label }}</div>
                      <div class="progress-bar">
                        <div
                          class="progress-fill"
                          :style="{
                            width: item.percentage + '%',
                            background: item.color,
                          }"
                        ></div>
                      </div>
                      <div class="progress-value">{{ item.percentage }}%</div>
                    </div>
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </a-col>

      <!-- 右边区域 (1/3宽度) -->
      <a-col :span="8">
        <div class="right-section">
          <!-- 日历热力图 -->
          <a-card class="calendar-card">
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
          <div class="section-title">
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
              <div class="view-more">
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
import { defineComponent, ref, computed } from "vue";
import {
  BookOutlined,
  RocketTwoTone,
  CheckCircleTwoTone,
  ClockCircleTwoTone,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/stores/auth";
import { getAllCourseclasses } from "@/api/courseclass";
import dayjs from "dayjs";

export default defineComponent({
  name: "HomeView",
  components: {
    BookOutlined,
    RocketTwoTone,
    CheckCircleTwoTone,
    ClockCircleTwoTone,
  },
  setup() {
    const authStore = useAuthStore();
    const courseClasses = ref<any[]>([]);
    const loading = ref<boolean>(false);

    // 伪造的AI资源使用数据
    const aiUsageData = ref([
      { name: "AI问答", count: 245, percentage: 75, color: "#1890ff" },
      { name: "教学设计生成", count: 128, percentage: 40, color: "#52c41a" },
      { name: "教学资源生成", count: 96, percentage: 30, color: "#722ed1" },
      { name: "题目生成", count: 82, percentage: 25, color: "#faad14" },
    ]);

    // 伪造的学生活跃度数据
    const activityData = ref([
      { label: "高活跃度", value: 42, percentage: 35, color: "#237804" },
      { label: "中等活跃度", value: 68, percentage: 57, color: "#52c41a" },
      { label: "低活跃度", value: 10, percentage: 8, color: "#a0d911" },
    ]);

    // 伪造的学习进度数据
    const progressData = ref([
      { label: "超前学习", value: 18, percentage: 18, color: "#237804" },
      { label: "正常进度", value: 65, percentage: 65, color: "#52c41a" },
      { label: "进度落后", value: 17, percentage: 17, color: "#faad14" },
    ]);

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

    // 生成日历数据
    const calendarDays = computed(() => {
      const startOfMonth = currentDate.value.startOf("month");
      const endOfMonth = currentDate.value.endOf("month");
      const startDay = startOfMonth.day();
      const daysInMonth = endOfMonth.date();
      const today = dayjs();

      // 生成当月的日期数组
      const days = [];
      for (let i = 1; i <= daysInMonth; i++) {
        const date = startOfMonth.date(i);
        days.push({
          date: i,
          inMonth: true,
          isToday: date.isSame(today, "day"),
          activity: Math.floor(Math.random() * 100), // 随机生成活跃度数据
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
        courseClasses.value = data.slice(0, 3);
      } catch (error) {
        console.error("获取课程班失败:", error);
      } finally {
        loading.value = false;
      }
    };

    // 初始化加载数据
    if (authStore.isAuthenticated) {
      loadCourseClasses();
    }

    return {
      courseClasses,
      aiUsageData,
      activityData,
      progressData,
      currentMonth,
      calendarDays,
      heatLevels,
      getHeatColor,
      prevMonth,
      nextMonth,
      loading,
    };
  },
});
</script>

<style scoped lang="less">
.home {
  padding: 16px;
  // background-color: #91bbfa;
  height: 100%;
}

.main-content {
  height: calc(95vh - 48px);
}

.data-dashboard {
  // background-color: #fff;
  border-radius: 12px;
  height: 100%;
  .dashboard-row {
    margin-bottom: 24px;
  }
}

.stat-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  height: 140px;
  display: flex;
  flex-direction: column;
  justify-content: center;

  .stat-header {
    display: flex;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      margin: 0 0 0 12px;
      font-size: 16px;
      color: #595959;
    }
  }

  .stat-value {
    font-size: 28px;
    font-weight: 600;
    color: #1f1f1f;
    margin-bottom: 8px;
  }

  .stat-trend {
    font-size: 14px;
    color: #8c8c8c;

    .positive {
      color: #52c41a;
    }

    .negative {
      color: #f5222d;
    }
  }
}

.chart-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;

  :deep(.ant-card-head) {
    border-bottom: none;
  }
}

.chart-container {
  padding: 16px 0;
  height: 250px;
}

.ai-resource-chart {
  .resource-bar {
    display: flex;
    align-items: center;
    margin-bottom: 16px;

    .resource-label {
      width: 150px;
      font-size: 14px;
      color: #595959;
    }

    .bar-container {
      flex: 1;
      height: 30px;
      background: #f5f5f5;
      border-radius: 4px;
      position: relative;
      overflow: hidden;

      .bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
      }

      .bar-value {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        color: #fff;
        font-size: 12px;
        font-weight: 500;
      }
    }
  }
}

.activity-chart,
.progress-chart {
  .activity-item,
  .progress-item {
    display: flex;
    align-items: center;
    margin-bottom: 16px;

    .activity-label,
    .progress-label {
      width: 100px;
      font-size: 14px;
      color: #595959;
    }

    .activity-bar,
    .progress-bar {
      flex: 1;
      height: 20px;
      background: #f5f5f5;
      border-radius: 4px;
      position: relative;
      overflow: hidden;

      .activity-fill,
      .progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
      }
    }

    .activity-value,
    .progress-value {
      width: 60px;
      text-align: right;
      font-size: 14px;
      color: #8c8c8c;
    }
  }
}

.right-section {
  display: flex;
  flex-direction: column;
  height: 100%;

  .calendar-card {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 24px;
    flex: 1;

    :deep(.ant-card-body) {
      padding: 16px;
    }
  }

  .my-classes-list {
    flex: 1;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    padding: 16px;
    height: 200px !important;
  }
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
