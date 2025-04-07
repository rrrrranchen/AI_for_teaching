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
}

/**
 * 问题列表响应类型
 */
// export interface QuestionsResponse {
//   questions: Question[];
// }

/**
 * 创建课前问题参数
 */
export interface CreatePreQuestionsParams {
  content: string; // 教师补充内容
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
   * 批量删除问题 (扩展示例)
   */
  // async batchDeleteQuestions(questionIds: number[]): Promise<number[]> {
  //   const results = await Promise.all(
  //     questionIds.map((id) => this.deleteQuestion(id))
  //   );
  //   return results.map((r) => r.question_id);
  // },
};

export default questionApi;
