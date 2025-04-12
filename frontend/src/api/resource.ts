// src/api/resource.ts
import api from "@/request";
import type { AxiosResponse } from "axios";

// 多媒体资源元数据接口
export interface ResourceMetadata {
  fileSize: number;
  format?: string;
  mimeType?: string;
  pageCount?: number;
  wordCount?: number;
  author?: string;
  colorMode?: string;
  dpi?: number;
  duration?: number;
  resolution?: string;
  bitrate?: number;
  extra?: Record<string, unknown>;
}

// 多媒体资源接口
export interface MultimediaResource {
  id: string;
  title: string;
  courseId: number;
  designVersion_id: number;
  description: string;
  type:
    | "ebook"
    | "document"
    | "presentation"
    | "image"
    | "video"
    | "audio"
    | "other";
  storage_path: string;
  preview_urls: {
    thumbnail?: string;
  };
  metadata: ResourceMetadata;
  created_at?: string;
  updated_at?: string;
}

// PPT模板接口
export interface PPTTemplate {
  id: number;
  name: string;
  image_url: string;
}

/**
 * 生成教学设计PPT
 * @param courseId 课程ID
 * @param teachingDesignVersionId 教学设计版本ID
 * @param pptTemplateId PPT模板ID
 * @param title PPT标题
 */
export const generateTeachingPPT = (
  courseId: number,
  teachingDesignVersionId: number,
  pptTemplateId: number,
  title?: string
): Promise<void> => {
  return api.post(
    `/createPPT/${courseId}/${teachingDesignVersionId}/${pptTemplateId}`,
    null,
    {
      params: { title },
    }
  );
};

/**
 * 获取指定教学设计版本的资源
 * @param designVersionId 教学设计版本ID
 */
export const getDesignVersionResources = (
  designVersionId: number
): Promise<MultimediaResource[]> => {
  return api
    .get(`/resources/teachingdesignversion/${designVersionId}`)
    .then(
      (res: AxiosResponse<{ resources: MultimediaResource[] }>) =>
        res.data.resources
    );
};

/**
 * 获取用户所有资源
 */
export const getAllResources = (): Promise<MultimediaResource[]> => {
  return api
    .get("/resources")
    .then(
      (res: AxiosResponse<{ resources: MultimediaResource[] }>) =>
        res.data.resources
    );
};

/**
 * 删除指定资源
 * @param resourceId 资源ID
 */
export const deleteResource = (resourceId: string): Promise<void> => {
  return api.delete(`/resources/${resourceId}`);
};

/**
 * 获取课程资源
 * @param courseId 课程ID
 */
export const getCourseResources = (
  courseId: number
): Promise<MultimediaResource[]> => {
  return api
    .get(`/resources/course/${courseId}`)
    .then(
      (res: AxiosResponse<{ resources: MultimediaResource[] }>) =>
        res.data.resources
    );
};

/**
 * 获取单个资源详情
 * @param resourceId 资源ID
 */
export const getResourceDetail = (
  resourceId: string
): Promise<MultimediaResource> => {
  return api
    .get(`/resources/${resourceId}`)
    .then(
      (res: AxiosResponse<{ resource: MultimediaResource }>) =>
        res.data.resource
    );
};

/**
 * 获取所有PPT模板
 */
export const getAllPPTTemplates = (): Promise<PPTTemplate[]> => {
  return api
    .get("/ppt-templates")
    .then((res: AxiosResponse<PPTTemplate[]>) => res.data);
};
