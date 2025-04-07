import api from "@/request";
import type { AxiosResponse } from "axios";

// 教学设计基础类型
export interface TeachingDesign {
  id: number;
  title: string;
  course_id: number;
  creator_id: number;
  current_version_id?: number;
  created_at: string;
}

// 教学设计版本类型
export interface TeachingDesignVersion {
  id: number;
  design_id: number;
  version: string;
  content: {
    objectives?: string;
    plan_content?: string;
    analysis?: string;
    [key: string]: any;
  };
  recommendation_score: number;
  level: string;
  created_at: string;
  updated_at?: string;
  author_id: number;
}

// 创建教学设计参数
export interface CreateTeachingDesignParams {
  course_id: number;
  title?: string;
  course_content?: string;
}

// 更新教学设计参数
interface UpdateTeachingDesignParams {
  title?: string;
  course_id?: number;
}

// 更新版本参数
interface UpdateVersionParams {
  content?: Record<string, any>;
  recommendation_score?: number;
  level?: string;
}

// 公用接口
//
//
//
// 获取单个教学设计的所有版本
export const getDesignVersions = async (
  designId: number
): Promise<{ design: TeachingDesign; versions: TeachingDesignVersion[] }> => {
  const response: AxiosResponse = await api.get(`/${designId}/versions`);
  return response.data.data;
};

// 获取单个教学设计版本详情
export const getDesignVersionDetail = async (
  versionId: number
): Promise<TeachingDesignVersion> => {
  const response: AxiosResponse = await api.get(`/versions/${versionId}`);
  return response.data.data;
};

// 获取课程的所有教学设计
export const getCourseDesigns = async (
  courseId: number
): Promise<TeachingDesign[]> => {
  const response: AxiosResponse = await api.get(`/course/${courseId}/designs`);
  return response.data.data;
};

// 教师专用接口
//
//
//
// 创建教学设计（自动生成版本）
export const createTeachingDesign = async (
  params: CreateTeachingDesignParams
): Promise<{ design: TeachingDesign; versions: TeachingDesignVersion[] }> => {
  const response: AxiosResponse = await api.post(
    "/createteachingdesign",
    params
  );
  return response.data.data;
};

// 获取当前用户的教学设计
export const getMyDesigns = async (): Promise<TeachingDesign[]> => {
  const response: AxiosResponse = await api.get("/mydesigns");
  return response.data.data;
};

// 更新教学设计基本信息
export const updateTeachingDesign = async (
  designId: number,
  params: UpdateTeachingDesignParams
): Promise<TeachingDesign> => {
  const response: AxiosResponse = await api.put(`/design/${designId}`, params);
  return response.data.data;
};

// 更新教学设计版本
export const updateDesignVersion = async (
  designId: number,
  versionId: number,
  params: UpdateVersionParams
): Promise<TeachingDesignVersion> => {
  const response: AxiosResponse = await api.put(
    `/design/${designId}/version/${versionId}`,
    params
  );
  return response.data.data;
};

// 迁移教学设计
export const migrateCourseDesigns = async (
  sourceCourseId: number,
  targetCourseId: number
): Promise<TeachingDesign[]> => {
  const response: AxiosResponse = await api.post(
    `/course/${sourceCourseId}/migrate/${targetCourseId}`
  );
  return response.data.data;
};
