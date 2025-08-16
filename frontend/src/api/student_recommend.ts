// src/api/student_recommend.ts
import api from "@/request";
import type { AxiosResponse } from "axios";

export interface RecommendationData {
  video_recommendations: string | null; // 修改为可空类型
  message?: string; // 添加可选的消息字段
}

// 学生推荐资源类型
export interface StudentRecommendation {
  type: "pre_class" | "post_class";
  content: string; // Markdown格式内容
  course_id?: number;
}

// 生成推荐响应类型
interface GenerateRecommendResponse {
  message: string;
  recommendation_id: number;
}

/**
 * 生成课前推荐资源
 * @param courseId 课程ID
 */
export const generatePreClassRecommendations = async (
  courseId: number
): Promise<GenerateRecommendResponse> => {
  try {
    const response: AxiosResponse<GenerateRecommendResponse> = await api.post(
      `/generate_pre_class_recommendations/${courseId}`
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "课前推荐生成失败");
  }
};

/**
 * 获取用户课前推荐资源
 * @param courseId 课程ID
 */
export const getPreClassRecommendations = async (
  courseId: number
): Promise<StudentRecommendation[]> => {
  try {
    const response: AxiosResponse<{ data: StudentRecommendation[] }> =
      await api.get(`/get_user_pre_class_recommendations/${courseId}`);
    return response.data.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "获取课前推荐失败");
  }
};

/**
 * 生成课后推荐资源
 * @param courseId 课程ID
 */
export const generatePostClassRecommendations = async (
  courseId: number
): Promise<GenerateRecommendResponse> => {
  try {
    const response: AxiosResponse<GenerateRecommendResponse> = await api.post(
      `/generate_post_class_recommendations/${courseId}`
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "课后推荐生成失败");
  }
};

/**
 * 获取用户课后推荐资源
 * @param courseId 课程ID
 */
export const getPostClassRecommendations = async (
  courseId: number
): Promise<RecommendationData> => {
  try {
    const response: AxiosResponse<RecommendationData> = await api.get(
      `/get_user_post_class_recommendations/${courseId}`
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "获取课后推荐失败");
  }
};

// 类型导出
export type { GenerateRecommendResponse };
