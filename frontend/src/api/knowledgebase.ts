// src/api/knowledge_for_teacher.ts
import api from "@/request";
import type { AxiosResponse } from "axios";

// 类目类型枚举
export type CategoryType = "structural" | "non_structural";

// 知识库类型枚举
export type KnowledgeBaseType = "structural" | "non_structural";

export interface LoadingState {
  main?: boolean; // 主内容加载
  action?: boolean; // 特定操作加载
  [key: string]: any; // 其他自定义状态
}

// 类目基础类型
export interface Category {
  id: number;
  name: string;
  description?: string;
  category_type: CategoryType;
  created_at: string;
  updated_at?: string;
  is_public: boolean;
  is_system: boolean;
  file_count: number;
  author_id: number;
  author_name?: string; //新增
}

// 类目文件类型
export interface CategoryFile {
  id: number;
  name: string;
  stored_filename: string;
  category_id: number;
  author_id: number;
  file_path: string;
  original_file_path?: string;
  file_type: string;
  created_at: string;
  updated_at?: string;
  is_public: boolean;
}

// 知识库基础类型
// 更新 KnowledgeBase 接口，添加管理员相关字段
export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  stored_basename: string;
  author_id: number;
  author_name?: string; // 新增字段
  is_public: boolean;
  is_system?: boolean; // 新增字段
  need_update: boolean;
  created_at: string;
  updated_at?: string;
  file_path: string;
  base_type: KnowledgeBaseType;
  categories: {
    id: number;
    name: string;
    type?: CategoryType; // 新增字段
  }[];
  updating?: boolean;
}

// 课程班基础类型
export interface Courseclass {
  id: number;
  name: string;
  description?: string;
  knowledge_bases?: KnowledgeBase[];
}

// ======================== 类目管理API ========================

/**
 * 获取当前用户的所有类目
 */
export const getCategories = async (): Promise<{
  structured_categories: Category[];
  non_structured_categories: Category[];
}> => {
  const response: AxiosResponse = await api.get("/teacher/categories");
  return response.data;
};

/**
 * 创建新类目
 * @param params 创建参数
 */
export const createCategory = async (params: {
  name: string;
  description?: string;
  category_type: CategoryType;
  is_public?: boolean;
}): Promise<{
  id: number;
  name: string;
  path: string;
  type: CategoryType;
  is_public: boolean;
}> => {
  const response: AxiosResponse = await api.post("/teacher/categories", params);
  return response.data.category;
};

/**
 * 更新类目信息
 * @param categoryId 类目ID
 * @param params 更新参数
 */
export const updateCategory = async (
  categoryId: number,
  params: {
    name?: string;
    description?: string;
    is_public?: boolean;
  }
): Promise<{
  success: boolean;
  message: string;
  updated_fields: string[];
}> => {
  const response: AxiosResponse = await api.put(
    `/teacher/categories/${categoryId}`,
    params
  );
  return response.data;
};

/**
 * 删除类目
 * @param categoryId 类目ID
 */
export const deleteCategory = async (
  categoryId: number
): Promise<{
  success: boolean;
  message: string;
  deleted_files_count: number;
  affected_knowledge_bases: number[];
}> => {
  const response: AxiosResponse = await api.delete(
    `/teacher/categories/${categoryId}`
  );
  return response.data;
};

// ======================== 类目文件管理API ========================

/**
 * 获取类目中的文件列表
 * @param categoryId 类目ID
 */
export const getCategoryFiles = async (
  categoryId: number
): Promise<CategoryFile[]> => {
  const response: AxiosResponse = await api.get(
    `/teacher/categories/${categoryId}/files`
  );
  return response.data.data;
};

/**
 * 上传文件到类目
 * @param categoryId 类目ID
 * @param files 文件列表
 */
export const uploadFilesToCategory = async (
  categoryId: number,
  files: File[]
): Promise<{
  succeeded: Array<{
    id: number;
    name: string;
    url: string;
    images?: Array<{
      id: number;
      path: string;
      filename: string;
    }>;
  }>;
  failed: Array<{
    name: string;
    error: string;
  }>;
  knowledge_bases_updated: boolean;
}> => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response: AxiosResponse = await api.post(
    `/teacher/categories/${categoryId}/files`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data.data;
};

/**
 * 批量删除类目中的文件
 * @param categoryId 类目ID
 * @param fileIds 文件ID数组
 */
export const deleteCategoryFiles = async (
  categoryId: number,
  fileIds: number[]
): Promise<{
  success: boolean;
  message: string;
  deleted: number[];
  failed: Array<{
    file_id: number;
    error: string;
  }>;
  knowledge_bases_updated: boolean;
}> => {
  const response: AxiosResponse = await api.delete(
    `/teacher/categories/${categoryId}/files`,
    { data: { file_ids: fileIds } }
  );
  return response.data;
};

// ======================== 知识库管理API ========================

/**
 * 获取当前用户的所有知识库
 */
export const getKnowledgeBases = async (): Promise<KnowledgeBase[]> => {
  const response: AxiosResponse = await api.get("/teacher/knowledge_bases");
  return response.data;
};

/**
 * 获取待更新的知识库
 */
export const getPendingUpdateKnowledgeBases = async (): Promise<
  KnowledgeBase[]
> => {
  const response: AxiosResponse = await api.get(
    "/teacher/knowledge_bases/pending_updates"
  );
  return response.data.data;
};

/**
 * 创建知识库
 * @param params 创建参数
 */
export const createKnowledgeBase = async (params: {
  name: string;
  description?: string;
  category_ids: number[];
  base_type: KnowledgeBaseType;
  is_public?: boolean;
}): Promise<KnowledgeBase> => {
  const response: AxiosResponse = await api.post(
    "/teacher/knowledge_bases",
    params
  );
  return response.data;
};

/**
 * 批量更新知识库
 */
export const batchUpdateKnowledgeBases = async (): Promise<{
  updated_count: number;
  failed_count: number;
  failed_updates: Array<{
    knowledge_base_id: number;
    name: string;
    error: string;
  }>;
}> => {
  const response: AxiosResponse = await api.post(
    "/teacher/knowledge_bases/batch_update"
  );
  return response.data;
};

/**
 * 更新单个知识库
 * @param kbId 知识库ID
 */
export const updateKnowledgeBase = async (
  kbId: number
): Promise<{
  success: boolean;
  message: string;
  updated: boolean;
}> => {
  const response: AxiosResponse = await api.post(
    `/teacher/knowledge_bases/${kbId}/update`
  );
  return response.data;
};

/**
 * 删除知识库
 * @param kbId 知识库ID
 */
export const deleteKnowledgeBase = async (
  kbId: number
): Promise<{ message: string }> => {
  const response: AxiosResponse = await api.delete(
    `/teacher/knowledge_bases/${kbId}`
  );
  return response.data;
};

/**
 * 为知识库批量添加类目
 * @param kbId 知识库ID
 * @param categoryIds 类目ID数组
 */
export const batchAddCategoriesToKnowledgeBase = async (
  kbId: number,
  categoryIds: number[]
): Promise<{
  success: boolean;
  message: string;
  added_categories: Array<{
    id: number;
    name: string;
    type: CategoryType;
  }>;
  duplicates: Array<{
    id: number;
    name: string;
  }>;
  type_mismatches: Array<{
    id: number;
    name: string;
    type: CategoryType;
  }>;
}> => {
  const response: AxiosResponse = await api.post(
    `/teacher/knowledge_bases/${kbId}/categories/batch_add`,
    { category_ids: categoryIds }
  );
  return response.data;
};

/**
 * 从知识库批量移除类目
 * @param kbId 知识库ID
 * @param categoryIds 类目ID数组
 */
export const batchRemoveCategoriesFromKnowledgeBase = async (
  kbId: number,
  categoryIds: number[]
): Promise<{
  success: boolean;
  message: string;
  removed_categories: Array<{
    id: number;
    name: string;
  }>;
  not_linked: number[];
}> => {
  const response: AxiosResponse = await api.delete(
    `/teacher/knowledge_bases/${kbId}/categories/batch_remove`,
    { data: { category_ids: categoryIds } }
  );
  return response.data;
};

// ======================== 课程班知识库关联API ========================

/**
 * 为课程班添加知识库
 * @param courseclassId 课程班ID
 * @param knowledgeBaseIds 知识库ID数组
 */
export const addKnowledgeBasesToCourseclass = async (
  courseclassId: number,
  knowledgeBaseIds: number[]
): Promise<{ message: string }> => {
  const response: AxiosResponse = await api.post(
    `/teacher/courseclasses/${courseclassId}/knowledge_bases`,
    { knowledge_base_ids: knowledgeBaseIds }
  );
  return response.data;
};

/**
 * 更新课程班关联的知识库
 * @param courseclassId 课程班ID
 * @param knowledgeBaseIds 知识库ID数组
 */
export const updateCourseclassKnowledgeBases = async (
  courseclassId: number,
  knowledgeBaseIds: number[]
): Promise<{ message: string }> => {
  const response: AxiosResponse = await api.put(
    `/teacher/courseclasses/${courseclassId}/knowledge_bases`,
    { knowledge_base_ids: knowledgeBaseIds }
  );
  return response.data;
};

// ======================== 公共知识库API ========================

/**
 * 搜索公共知识库
 * @param keyword 搜索关键词
 * @param page 页码
 * @param perPage 每页数量
 */
export const searchPublicKnowledgeBases = async (
  keyword: string,
  page = 1,
  perPage = 10
): Promise<{
  results: Array<{
    id: number;
    name: string;
    description?: string;
    is_public: boolean;
    created_at: string;
    updated_at?: string;
    author: {
      id: number;
      username: string;
    };
    categories: Array<{
      id: number;
      name: string;
    }>;
    match_type: string;
    match_score: number;
  }>;
  pagination: {
    total: number;
    pages: number;
    current_page: number;
    per_page: number;
    has_next: boolean;
    has_prev: boolean;
  };
  search_meta: {
    keyword: string;
    total_matches: number;
    name_matches: number;
    desc_matches: number;
  };
}> => {
  const response: AxiosResponse = await api.get(
    "/public/knowledge_bases/search",
    {
      params: {
        keyword,
        page,
        per_page: perPage,
      },
    }
  );
  return response.data.data;
};

/**
 * 深度搜索公共知识库内容
 * @param keyword 搜索关键词
 * @param kbIds 知识库ID列表(可选)
 * @param similarity 相似度阈值(0-1, 默认0.7)
 * @param chunkCount 返回的片段数量(默认5)
 * @param dataType 过滤数据类型(可选)
 */
export const deepSearchPublicKnowledgeBases = async (
  keyword: string,
  kbIds?: number[],
  chunkCount = 5,
  dataType?: string
): Promise<{
  keyword: string;
  matches: number;
  similarity_threshold: number;
  results: Array<{
    knowledge_base: {
      id: number;
      name: string;
      is_public: boolean;
      author: {
        id: number;
        username: string;
      };
    };
    category: string;
    file: string;
    text: string;
    score: number;
    position: number;
  }>;
  model_context: string;
  display_context: string;
}> => {
  const response: AxiosResponse = await api.get(
    "/public/knowledge_bases/deep_search",
    {
      params: {
        keyword,
        kb_ids: kbIds?.join(","),
        similarity,
        chunk_count: chunkCount,
        data_type: dataType,
      },
    }
  );
  return response.data.data;
};

/**
 * 获取课程班推荐知识库
 * @param courseclassId 课程班ID
 * @param limit 返回结果数量(默认5)
 * @param minUsageCount 最小使用次数阈值(默认3)
 * @param keywordWeight 关键词匹配权重(0-1, 默认0.6)
 * @param categoryWeight 类别匹配权重(0-1, 默认0.3)
 * @param usageWeight 使用次数权重(0-1, 默认0.1)
 */
export const getRecommendedKnowledgeBases = async (
  courseclassId: number,
  limit = 5,
  minUsageCount = 3,
  keywordWeight = 0.6,
  categoryWeight = 0.3,
  usageWeight = 0.1
): Promise<{
  courseclass_id: number;
  courseclass_name: string;
  courseclass_keywords: string[];
  current_category_ids: number[];
  recommendation_strategy: {
    keyword_weight: number;
    category_weight: number;
    usage_weight: number;
  };
  recommendations: Array<{
    id: number;
    name: string;
    description?: string;
    usage_count: number;
    author: {
      id: number;
      username: string;
    };
    categories: Array<{
      id: number;
      name: string;
    }>;
    match_reason: string;
    score_details: {
      total_score: number;
      keyword_score: number;
      category_score: number;
      usage_score: number;
    };
  }>;
}> => {
  const response: AxiosResponse = await api.get(
    `/teacher/courseclasses/${courseclassId}/knowledge_bases/recommendations`,
    {
      params: {
        limit,
        min_usage_count: minUsageCount,
        keyword_weight: keywordWeight,
        category_weight: categoryWeight,
        usage_weight: usageWeight,
      },
    }
  );
  return response.data.data;
};

/**
 * 迁移公共知识库为个人知识库
 * @param knowledgeBaseId 公共知识库ID
 */
export const migratePublicKnowledgeBase = async (
  knowledgeBaseId: number
): Promise<{
  new_knowledge_base: {
    id: number;
    name: string;
    path: string;
  };
}> => {
  const response: AxiosResponse = await api.post(
    "/teacher/knowledge_bases/migrate_public",
    {
      knowledge_base_id: knowledgeBaseId,
    }
  );
  return response.data.data;
};

/**
 * 获取公共知识库列表
 */
export const getPublicKnowledgeBases = async (): Promise<
  Array<{
    id: number;
    name: string;
    description?: string;
    is_public: boolean;
    created_at: string;
    updated_at?: string;
    author: {
      id: number;
      username: string;
    };
    categories: Array<{
      id: number;
      name: string;
    }>;
  }>
> => {
  const response: AxiosResponse = await api.get("/public/knowledge_bases");
  return response.data.data;
};

export default {
  // 类目管理
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,

  // 文件管理
  getCategoryFiles,
  uploadFilesToCategory,
  deleteCategoryFiles,

  // 知识库管理
  getKnowledgeBases,
  getPendingUpdateKnowledgeBases,
  createKnowledgeBase,
  batchUpdateKnowledgeBases,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  // 知识库类目批量操作
  batchAddCategoriesToKnowledgeBase,
  batchRemoveCategoriesFromKnowledgeBase,

  // 课程班关联
  addKnowledgeBasesToCourseclass,
  updateCourseclassKnowledgeBases,

  // 公共知识库相关
  searchPublicKnowledgeBases,
  deepSearchPublicKnowledgeBases,
  getRecommendedKnowledgeBases,
  migratePublicKnowledgeBase,
  getPublicKnowledgeBases,
};
