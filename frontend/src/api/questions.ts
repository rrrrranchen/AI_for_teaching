import api from "@/request";
import type { AxiosResponse } from "axios";

/**
 * 问题基础类型
 */
export interface Question {
  id: number;
  course_id: number;
  type: string;
  content: string;
  correct_answer: string;
  difficulty: string;
  timing: "pre_class" | "in_class" | "post_class";
  created_at?: string;
  updated_at?: string;
}

/**
 * 问题列表响应类型
 */
export interface QuestionsResponse {
  total?: number;
  questions: Question[];
}

/**
 * 创建课前问题参数
 */
interface CreatePreQuestionsParams {
  content: string; // 教师补充内容
}

/**
 * 更新问题参数
 */
interface UpdateQuestionParams {
  type?: string;
  content?: string;
  correct_answer?: string;
  difficulty?: string;
  timing?: "pre_class" | "in_class" | "post_class";
}

// ======================== 公用接口 ========================

/**
 * 获取课程所有预习题目
 */
export const getPreQuestions = async (
  courseId: number
): Promise<QuestionsResponse> => {
  const response: AxiosResponse<QuestionsResponse> = await api.get(
    `/prequestions/${courseId}`
  );
  return response.data;
};

/**
 * 获取单个题目详情
 */
export const getQuestionDetail = async (
  questionId: number
): Promise<Question> => {
  const response: AxiosResponse<Question> = await api.get(
    `/question/${questionId}`
  );
  return response.data;
};

// ======================== 教师专用接口 ========================

/**
 * 创建课前预习题目
 */
export const createPreQuestions = async (
  courseId: number,
  params: CreatePreQuestionsParams
): Promise<{ question_ids: number[] }> => {
  const response: AxiosResponse<{ question_ids: number[] }> = await api.post(
    `/createprequestion/${courseId}`,
    params
  );
  return response.data;
};

/**
 * 更新题目信息
 */
export const updateQuestion = async (
  questionId: number,
  params: UpdateQuestionParams
): Promise<Question> => {
  const response: AxiosResponse<Question> = await api.put(
    `/question/${questionId}`,
    params
  );
  return response.data;
};

/**
 * 删除题目
 */
export const deleteQuestion = async (
  questionId: number
): Promise<{ question_id: number }> => {
  const response: AxiosResponse<{ question_id: number }> = await api.delete(
    `/deletequestion/${questionId}`
  );
  return response.data;
};

// ======================== 扩展接口 ========================

/**
 * 批量删除问题 (扩展示例)
 */
export const batchDeleteQuestions = async (
  questionIds: number[]
): Promise<{ deleted_ids: number[] }> => {
  const responses = await Promise.all(
    questionIds.map((id) => deleteQuestion(id))
  );
  return {
    deleted_ids: responses.map((r) => r.question_id),
  };
};

/**
 * 搜索问题 (扩展示例)
 */
export const searchQuestions = async (
  courseId: number,
  keyword: string
): Promise<QuestionsResponse> => {
  const response: AxiosResponse<QuestionsResponse> = await api.get(
    `/courses/${courseId}/search_questions`,
    { params: { q: keyword } }
  );
  return response.data;
};
