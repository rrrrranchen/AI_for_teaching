// api/studentanswer.ts
import api from "@/request";
import type { AxiosResponse } from "axios";

// 问题类型枚举
export type QuestionType = "choice" | "fill" | "short_answer";

// 答题记录基础类型
export interface StudentAnswer {
  id: number;
  student_id: number;
  question_id: number;
  class_id?: number;
  course_id?: number;
  answer: string;
  correct_percentage: number;
  answered_at: string;
  modified_by?: number;
  modified_at?: string;
}

// 分析报告类型
export interface AnalysisReport {
  markdown_report: string;
}

// 分页响应类型
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  pages: number;
  current_page: number;
}

// 添加作答请求参数
export interface AddAnswersParams {
  courseclass_id: number;
  answers: Array<{
    question_id: number;
    answer: string;
  }>;
}

// 更新分数请求参数
interface UpdateScoreParams {
  new_score: number;
}

// ======================== 学生作答API ========================

/**
 * 批量添加学生作答记录
 * @param params 作答数据
 */
export const addStudentAnswers = (
  params: AddAnswersParams
): Promise<
  AxiosResponse<
    Array<{
      question_id: number;
      message: string;
      answer_id?: number;
      correct_percentage?: number;
      error?: string;
    }>
  >
> => {
  return api.post("/add_answers", params);
};

/**
 * 教师更新作答分数
 * @param answerId 作答记录ID
 * @param params 分数参数
 */
export const updateAnswerScore = (
  answerId: number,
  params: UpdateScoreParams
): Promise<
  AxiosResponse<{
    message: string;
    data: {
      answer_id: number;
      new_score: number;
      modified_at: string;
    };
  }>
> => {
  return api.post(`/update_score/${answerId}`, params);
};

/**
 * 获取单个作答记录详情
 * @param answerId 作答记录ID
 */
export const getAnswerDetail = (
  answerId: number
): Promise<
  AxiosResponse<{
    id: number;
    student_id: number;
    question_id: number;
    class_id: number;
    answer: string;
    score: number;
    answered_at: string;
    is_modified: boolean;
    modified_at?: string;
    modified_by?: string;
  }>
> => {
  return api.get(`/studentanswer/${answerId}`);
};

/**
 * 分页获取课程答题记录（教师用）
 * @param courseId 课程ID
 * @param page 页码
 * @param perPage 每页数量
 * @param studentId 可选学生ID
 */
export const getCourseAnswers = (
  courseId: number,
  page = 1,
  perPage = 10,
  studentId?: number
): Promise<
  AxiosResponse<
    PaginatedResponse<{
      question_id: number;
      question_content: string;
      answers: Array<{
        answer_id: number;
        student_name: string;
        answer_content: string;
        score: number;
        answered_at: string;
        is_modified: boolean;
        modified_at?: string;
        modified_by?: string;
      }>;
      average_score: number;
    }>
  >
> => {
  return api.get(`/course/${courseId}/answers`, {
    params: {
      page,
      per_page: perPage,
      student_id: studentId,
    },
  });
};

/**
 * 获取单个题目的所有作答记录
 * @param questionId 题目ID
 */
export const getQuestionAnswers = (
  questionId: number
): Promise<
  AxiosResponse<{
    question_id: number;
    question_content: string;
    answers: Array<{
      answer_id: number;
      student_name: string;
      answer_content: string;
      score: number;
      answered_at: string;
      is_modified: boolean;
      modified_at?: string;
      modified_by?: string;
    }>;
    average_score: number;
  }>
> => {
  return api.get(`/question/${questionId}/answers`);
};

// ======================== 分析报告API ========================

/**
 * 获取学生课程班个人报告
 * @param studentId 学生ID
 * @param courseclassId 课程班ID
 */
export const getStudentClassReport = (
  studentId: number,
  courseclassId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.get(`/getstudentanswerreport/${studentId}/${courseclassId}`);
};

/**
 * 获取课程班整体分析报告（教师用）
 * @param courseclassId 课程班ID
 */
export const getClassAnalysisReport = (
  courseclassId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.get(`/getclassanswerreport/${courseclassId}`);
};

/**
 * 获取课程整体分析报告（教师用）
 * @param courseId 课程ID
 */
export const getCourseAnalysisReport = (
  courseId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.get(`/getcourseanswersreport/${courseId}`);
};

/**
 * 获取学生课程个人报告
 * @param studentId 学生ID
 * @param courseId 课程ID
 */
export const getStudentCourseReport = (
  studentId: number,
  courseId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.get(`/getstudentincourseanswerreport/${studentId}/${courseId}`);
};

/**
 * 手动更新课程班报告（教师用）
 * @param courseclassId 课程班ID
 */
export const updateClassReport = (
  courseclassId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.post(`/updateclassanswerreport/${courseclassId}`);
};

/**
 * 手动更新课程报告（教师用）
 * @param courseId 课程ID
 */
export const updateCourseReport = (
  courseId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.post(`/updatecourseanswersreport/${courseId}`);
};

/**
 * 手动更新学生课程班报告
 * @param studentId 学生ID
 * @param courseclassId 课程班ID
 */
export const updateStudentClassReport = (
  studentId: number,
  courseclassId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.post(`/updatestudentanswerreport/${studentId}/${courseclassId}`);
};

/**
 * 手动更新学生课程报告
 * @param studentId 学生ID
 * @param courseId 课程ID
 */
export const updateStudentCourseReport = (
  studentId: number,
  courseId: number
): Promise<AxiosResponse<AnalysisReport>> => {
  return api.post(
    `/updatestudentincourseanswerreport/${studentId}/${courseId}`
  );
};
