// src/api/teacher_recommend.ts
import api from "@/request";
import type { AxiosResponse } from "axios";

// 推荐内容数据结构
export interface RecommendationData {
  video_recommendations: string; // Markdown格式视频推荐
  image_recommendations: string[]; // 图片URL数组
}

// 生成推荐接口响应类型
interface GenerateRecommendResponse {
  message: string;
  recommendation_id: number;
}

// 获取推荐接口响应类型
interface GetRecommendResponse {
  data: RecommendationData | null;
}

/**
 * 生成教学设计推荐内容
 * @param teachingDesignId 教学设计ID
 */
export const generateTeachingRecommendation = async (
  teachingDesignId: number
): Promise<GenerateRecommendResponse> => {
  try {
    const response: AxiosResponse<GenerateRecommendResponse> = await api.post(
      `/generate_recommendation/${teachingDesignId}`
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "推荐生成失败");
  }
};

/**
 * 获取教学设计的推荐内容
 * @param teachingDesignId 教学设计ID
 */
export const getRecommendationByDesign = async (
  teachingDesignId: number
): Promise<RecommendationData | null> => {
  try {
    const response: AxiosResponse<GetRecommendResponse> = await api.get(
      `/get_recommendation_by_design/${teachingDesignId}`
    );
    return response.data.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.error || "获取推荐内容失败");
  }
};

// 类型导出
export type { GenerateRecommendResponse, GetRecommendResponse };
