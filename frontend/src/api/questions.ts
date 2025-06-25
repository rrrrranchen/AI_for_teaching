// src/api/questions.ts
import api from "@/request";
import type { AxiosResponse } from "axios";

// 问题类型枚举
export type QuestionType = "choice" | "fill" | "short_answer";

// 难度枚举
export type QuestionDifficulty = "1" | "2" | "3" | "4" | "5";

//课前课后
export type QuestionTiming = "pre_class" | "post_class";
/**
 * 问题基础类型
 */
export interface Question {
  id: number;
  course_id: number;
  type: QuestionType;
  content: string;
  correct_answer: string;
  difficulty: QuestionDifficulty;
  timing: QuestionTiming;
  is_public?: boolean;
  studentAnswer?: StudentAnswer;
  knowledge_point_id?: number;
  knowledge_point_name?: string;
  knowledge_point_content?: string;
}

/**
 * 创建课前问题参数
 */
export interface CreatePreQuestionsParams {
  content: string; // 教师补充内容
}

/**
 * 生成课后习题参数
 */
interface GeneratePostQuestionsParams {
  design_id: number;
  version_id: number;
}

/**
 * 更新问题参数
 */
interface UpdateQuestionParams {
  type?: QuestionType;
  content?: string;
  correct_answer?: string;
  difficulty?: QuestionDifficulty;
  timing?: QuestionTiming;
  is_public?: boolean;
}

export interface StudentAnswer {
  question_id: number;
  answer: string;
  correct_percentage: number;
  submitted_at: string;
}

// 新增类型定义
/**
 * 热力图数据项
 */
export interface HeatmapDataItem {
  x: number; // 题目序号
  y: number; // 难度等级
  value: number; // 平均正确率（0-1）
  original_id: number; // 原始题目ID
}

/**
 * 高频错误题目项
 */
export interface ErrorRankingItem {
  rank: number; // 排名
  question_id: number; // 题目ID
  content: string; // 题目内容摘要
  error_rate: number; // 错误率（0-1）
  common_errors: string[]; // 常见错误答案
}

// ======================== 问题API ========================
export const questionApi = {
  /**
   * 创建课前预习题目
   */
  async createPreQuestions(
    courseId: number,
    params: CreatePreQuestionsParams
  ): Promise<{ question_ids: number[] }> {
    const response: AxiosResponse<{ question_ids: number[] }> = await api.post(
      `/createprequestion/${courseId}`,
      params
    );
    return response.data;
  },

  /**
   * 删除题目
   */
  async deleteQuestion(
    questionId: number
  ): Promise<{ message: string; question_id: number }> {
    const response: AxiosResponse<{ message: string; question_id: number }> =
      await api.delete(`/deletequestion/${questionId}`);
    return response.data;
  },

  /**
   * 获取课程预习题目列表
   */
  async getPreQuestions(courseId: number): Promise<Question[]> {
    const response: AxiosResponse<Question[]> = await api.get(
      `/prequestions/${courseId}`
    );
    return response.data;
  },

  /**
   * 获取单个题目详情
   */
  async getQuestionDetail(questionId: number): Promise<Question> {
    const response: AxiosResponse<Question> = await api.get(
      `/question/${questionId}`
    );
    return response.data;
  },

  /**
   * 更新题目信息
   */
  async updateQuestion(
    questionId: number,
    params: UpdateQuestionParams
  ): Promise<Question> {
    const response: AxiosResponse<Question> = await api.put(
      `/question/${questionId}`,
      params
    );
    return response.data;
  },

  /**
   * 切换题目公开状态
   */
  async toggleQuestionPublic(
    questionId: number,
    isPublic: boolean
  ): Promise<{ message: string; question_id: number; is_public: boolean }> {
    const response: AxiosResponse<{
      message: string;
      question_id: number;
      is_public: boolean;
    }> = await api.put(`/question/${questionId}/toggle_public`, {
      is_public: isPublic,
    });
    return response.data;
  },

  /**
   * 根据教学设计版本生成课后习题（带参数版本）
   */
  async generatePostQuestions(
    params: GeneratePostQuestionsParams
  ): Promise<Question[]> {
    const { design_id, version_id } = params;
    const response: AxiosResponse<Question[]> = await api.post(
      `/design/${design_id}/version/${version_id}/generate_post_class_questions`
    );
    return response.data;
  },

  /**
   * 获取课程课后习题列表
   */
  async getPostQuestions(courseId: number): Promise<Question[]> {
    const response: AxiosResponse<Question[]> = await api.get(
      `/postquestions/${courseId}`
    );
    return response.data;
  },

  /**
   * 获取课程所有题目（含课前课后）
   */
  async getAllQuestions(courseId: number): Promise<Question[]> {
    const response: AxiosResponse<Question[]> = await api.get(
      `/allquestions/${courseId}`
    );
    return response.data;
  },

  /**
   * 获取课程热力图数据
   * @param courseId 课程ID
   */
  async getCourseHeatmapData(courseId: number): Promise<{
    heatmap_data: HeatmapDataItem[];
    course_name: string;
  }> {
    const response: AxiosResponse = await api.get(
      `/course/${courseId}/heatmap_data`
    );
    return response.data;
  },

  /**
   * 获取课程高频错误排行
   * @param courseId 课程ID
   * @param topN 返回数量
   */
  async getCourseErrorRanking(
    courseId: number,
    topN = 10
  ): Promise<{
    ranking: ErrorRankingItem[];
    threshold: number;
  }> {
    const response: AxiosResponse = await api.get(
      `/course/${courseId}/error_ranking`,
      {
        params: {
          top_n: topN,
        },
      }
    );
    return response.data;
  },
};

export default questionApi;
