import api from "@/request";
import type { AxiosResponse } from "axios";

// 教学设计基础类型
export interface TeachingDesign {
  design_id: number;
  title: string;
  course_id: number;
  creator_id: number;
  default_version_id?: number;
  created_at: string;
  updated_at?: string;
  is_public: boolean;
  is_recommended: boolean;
}

// 教学设计版本类型
export interface TeachingDesignVersion {
  id: number;
  design_id: number;
  version: string;
  plan_content?: string;
  analysis?: string;
  recommendation_score: number;
  level: string;
  created_at: string;
  updated_at?: string;
  author_id: number;
}

// 创建教学设计参数
export interface CreateTeachingDesignParams {
  course_id: number;
}

// 更新教学设计参数
interface UpdateTeachingDesignParams {
  title?: string;
  default_version_id?: number;
}

// 更新版本参数（根据后端接口调整）
interface UpdateVersionParams {
  plan_content?: string; // 改为顶层字段
  analysis?: string; // 改为顶层字段
  recommendation_score?: number;
  level?: string;
}

// ======================== 类型定义 ========================
export interface MindMapNode {
  data: {
    id: number;
    text: string;
    note?: string;
    backgroundColor?: string;
  };
  children: MindMapNode[];
}

export interface GenerateMindMapResponse {
  code: number;
  message: string;
  data: {
    design_id: number;
    mind_map: MindMapNode[];
  };
}

export interface UpdateMindMapParams {
  mind_map: MindMapNode[];
}

export interface UpdateMindMapResponse {
  code: number;
  message: string;
  data: {
    design_id: number;
    mind_map: MindMapNode[];
    stats: {
      updated_nodes: number;
      new_nodes: number;
    };
  };
}

export interface GetMindMapResponse {
  mindmap: MindMapNode[] | null;
  timestamp: string;
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

//获取单个教学设计详情
export const getDesignDetail = async (
  designId: number
): Promise<TeachingDesign> => {
  const response: AxiosResponse = await api.get(`/design/${designId}`);
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
  // 请求体直接使用顶层参数
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

/**
 * 生成并存储思维导图
 * @param designId 教学设计ID
 */
export async function generateMindMap(
  designId: number
): Promise<GenerateMindMapResponse> {
  const response: AxiosResponse = await api.post(
    `/generatemindmap/${designId}`
  );
  return response.data;
}

/**
 * 更新思维导图数据
 * @param designId 教学设计ID
 * @param mindMap 思维导图数据
 */
export async function updateMindMap(
  designId: number,
  mindMap: MindMapNode[]
): Promise<UpdateMindMapResponse> {
  const response: AxiosResponse = await api.post(`/updatemindmap/${designId}`, {
    mind_map: mindMap,
  });
  return response.data;
}

/**
 * 获取教学设计的思维导图
 * @param designId 教学设计ID
 */
export async function getMindMap(
  designId: number
): Promise<GetMindMapResponse> {
  const response: AxiosResponse = await api.get(
    `/teaching-design/${designId}/mindmap`
  );
  return response.data;
}

// 教学设计可见性状态类型
export interface TeachingDesignVisibility {
  design_id: number;
  is_public: boolean;
  is_recommended: boolean;
  recommend_time?: string;
}

// 设置教学设计可见性参数
interface SetDesignVisibilityParams {
  is_public: boolean;
  is_recommended: boolean;
}

/**
 * 设置教学设计的公开和推荐状态
 * @param designId 教学设计ID
 * @param params 可见性参数
 */
export async function setDesignVisibility(
  designId: number,
  params: SetDesignVisibilityParams
): Promise<TeachingDesignVisibility> {
  const response: AxiosResponse = await api.put(
    `/design/${designId}/set_visibility`,
    params
  );
  return response.data.data;
}

// 计时器相关类型
export interface TeachingDesignTimer {
  design_id: number;
  total_seconds: number;
  is_active: boolean;
}

export interface TimerActionParams {
  action: "start" | "pause";
}

/**
 * 控制教学设计计时器
 * @param designId 教学设计ID
 * @param params 计时器操作参数
 */
export async function controlDesignTimer(
  designId: number,
  params: TimerActionParams
): Promise<TeachingDesignTimer> {
  const response: AxiosResponse = await api.post(
    `/design/${designId}/timer`,
    params
  );
  return response.data.data;
}

/**
 * 获取教学设计计时器状态
 * @param designId 教学设计ID
 */
export async function getDesignTimer(
  designId: number
): Promise<TeachingDesignTimer> {
  const response: AxiosResponse = await api.get(`/design/${designId}/timer`);
  return response.data.data;
}
