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

// 学习路线节点类型
export interface LearningPathNode {
  name: string;
  itemStyle?: { color: string };
  children?: LearningPathNode[];
}

// 学习路线响应类型
export interface LearningPathResponse {
  name: string;
  itemStyle: { color: string };
  children: LearningPathNode[];
}

// 公开课程搜索结果类型
export interface PublicClassResult {
  id: number;
  name: string;
  description: string;
  image_path: string | null;
  invite_code: string;
  courses: Array<{
    id: number;
    name: string;
    description: string;
  }>;
  score: number;
}

/**
 * 生成个性化学习路线
 * @param target 学习目标
 */
export const generateLearningPath = async (
  target: string
): Promise<LearningPathResponse> => {
  try {
    const response: AxiosResponse<{ data: LearningPathResponse }> =
      await api.get(`/generate_learn`, { params: { target } });
    return response.data.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "学习路线生成失败");
  }
};

// 公开课程搜索响应类型
export interface PublicClassSearchResponse {
  total: number;
  page: number;
  per: number;
  results: PublicClassResult[];
}

/**
 * 搜索公开课程
 * @param query 搜索关键词
 * @param page 页码
 * @param perPage 每页数量
 */
export const searchPublicClasses = async (
  query: string,
  page = 1,
  perPage = 10
): Promise<PublicClassSearchResponse> => {
  try {
    const response: AxiosResponse<{ data: PublicClassSearchResponse }> =
      await api.get(`/generate_learn/search`, {
        params: {
          q: query,
          page,
          per: perPage,
        },
      });
    return response.data.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "课程搜索失败");
  }
};

// 在 student_recommend.ts 中添加以下接口
/**
 * 获取用户已生成的学习路径
 */
export const getUserLearningPath =
  async (): Promise<LearningPathResponse | null> => {
    try {
      const response: AxiosResponse<{
        code: number;
        msg: string;
        data: LearningPathResponse | null;
      }> = await api.get(`/get_user_learning_path`);

      if (response.data.code === 0 && response.data.data) {
        return response.data.data;
      }
      return null;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null; // 没有学习路径是正常情况
      }
      throw new Error(error.response?.data?.msg || "获取学习路径失败");
    }
  };

// 类型导出
export type { GenerateRecommendResponse };
