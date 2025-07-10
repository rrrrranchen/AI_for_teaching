// src/api/admin/knowledgeManagement.ts
import api from "@/request";
import type { AxiosResponse } from "axios";
import type {
  Category,
  CategoryFile,
  KnowledgeBase,
  KnowledgeBaseType,
  CategoryType,
} from "@/api/knowledgebase";

// ======================== Knowledge Base Management ========================

interface KnowledgeBaseQueryParams {
  is_system?: boolean;
  base_type?: KnowledgeBaseType;
  author_id?: number;
  name?: string;
  author_name?: string;
  page?: number;
  per_page?: number;
}

interface KnowledgeBaseListResponse {
  success: boolean;
  data: KnowledgeBase[];
  pagination: {
    total: number;
    pages: number;
    current_page: number;
    per_page: number;
    has_next: boolean;
    has_prev: boolean;
  };
  filters: {
    is_system?: boolean;
    base_type?: string;
    author_id?: number;
    name?: string;
    author_name?: string;
  };
}

/**
 * Admin - Get all knowledge bases with filtering and pagination
 */
export const adminGetKnowledgeBases = async (
  params: KnowledgeBaseQueryParams
): Promise<KnowledgeBaseListResponse> => {
  const response: AxiosResponse = await api.post(
    "/admin/knowledge_bases",
    params
  );
  return response.data;
};

interface CreateKnowledgeBaseParams {
  name: string;
  description?: string;
  category_ids: number[];
  base_type: KnowledgeBaseType;
  is_public?: boolean;
}

/**
 * Admin - Create a new knowledge base
 */
export const adminCreateKnowledgeBase = async (
  params: CreateKnowledgeBaseParams
): Promise<KnowledgeBase> => {
  const response: AxiosResponse = await api.post(
    "/admin/knowledge_bases/create",
    params
  );
  return response.data;
};

interface BatchDeleteResponse {
  success: boolean;
  data: {
    deleted_count: number;
    deleted_ids: number[];
    failed_count: number;
    failed_ids: Array<{
      id: number;
      error: string;
    }>;
  };
}

/**
 * Admin - Batch delete knowledge bases
 */
export const adminBatchDeleteKnowledgeBases = async (
  kbIds: number[]
): Promise<BatchDeleteResponse> => {
  const response: AxiosResponse = await api.delete(
    "/admin/knowledge_bases/batch",
    { data: { kb_ids: kbIds } }
  );
  return response.data;
};

interface UpdateKnowledgeBaseParams {
  name?: string;
  description?: string;
  is_public?: boolean;
}

interface UpdateKnowledgeBaseResponse {
  success: boolean;
  message: string;
  updated_fields: string[];
}

/**
 * Admin - Update knowledge base information
 */
export const adminUpdateKnowledgeBase = async (
  kbId: number,
  params: UpdateKnowledgeBaseParams
): Promise<UpdateKnowledgeBaseResponse> => {
  const response: AxiosResponse = await api.put(
    `/admin/knowledge_bases/${kbId}`,
    params
  );
  return response.data;
};

interface BatchAddCategoriesResponse {
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
}

/**
 * Admin - Batch add categories to knowledge base
 */
export const adminBatchAddCategoriesToKnowledgeBase = async (
  kbId: number,
  categoryIds: number[]
): Promise<BatchAddCategoriesResponse> => {
  const response: AxiosResponse = await api.post(
    `/admin/knowledge_bases/${kbId}/categories/batch_add`,
    { category_ids: categoryIds }
  );
  return response.data;
};

interface BatchRemoveCategoriesResponse {
  success: boolean;
  message: string;
  removed_categories: Array<{
    id: number;
    name: string;
  }>;
  not_linked: number[];
}

/**
 * Admin - Batch remove categories from knowledge base
 */
export const adminBatchRemoveCategoriesFromKnowledgeBase = async (
  kbId: number,
  categoryIds: number[]
): Promise<BatchRemoveCategoriesResponse> => {
  const response: AxiosResponse = await api.post(
    `/admin/knowledge_bases/${kbId}/categories/batch_remove`,
    { data: { category_ids: categoryIds } }
  );
  return response.data;
};

interface UpdateSingleKBResponse {
  success: boolean;
  message: string;
  updated: boolean;
  details?: {
    knowledge_base_id: number;
    name: string;
    new_version?: string;
    updated_at?: string;
  };
}

/**
 * Admin - Update single knowledge base content
 */
export const adminUpdateSingleKnowledgeBase = async (
  kbId: number
): Promise<UpdateSingleKBResponse> => {
  const response: AxiosResponse = await api.post(
    `/admin/knowledge_bases/${kbId}/update`
  );
  return response.data;
};

interface BatchUpdateSystemKBResponse {
  success: boolean;
  message: string;
  updated_count: number;
  failed_count: number;
  failed_updates: Array<{
    knowledge_base_id: number;
    name: string;
    error: string;
  }>;
}

/**
 * Admin - Batch update all system knowledge bases that need update
 */
export const adminBatchUpdateSystemKnowledgeBases =
  async (): Promise<BatchUpdateSystemKBResponse> => {
    const response: AxiosResponse = await api.post(
      "/admin/knowledge_bases/system/batch_update"
    );
    return response.data;
  };

// ======================== Category Management ========================

interface CategoryQueryParams {
  name?: string;
  type?: CategoryType;
  is_system?: boolean;
  author_id?: number;
  page?: number;
  per_page?: number;
}

interface CategoryListResponse {
  success: boolean;
  data: Category[];
  pagination: {
    total: number;
    pages: number;
    current_page: number;
    per_page: number;
    has_next: boolean;
    has_prev: boolean;
  };
  search_params: {
    name?: string;
    type?: string;
    is_system?: boolean;
    author_id?: number;
  };
}

/**
 * Admin - Search categories with filters
 */
export const adminSearchCategories = async (
  params: CategoryQueryParams
): Promise<CategoryListResponse> => {
  const response: AxiosResponse = await api.get("/admin/categories/search", {
    params,
  });
  return response.data;
};

interface CreateCategoryParams {
  name: string;
  description?: string;
  category_type: CategoryType;
  is_public?: boolean;
}

/**
 * Admin - Create a new system category
 */
export const adminCreateCategory = async (
  params: CreateCategoryParams
): Promise<Category> => {
  const response: AxiosResponse = await api.post("/admin/categories", params);
  return response.data.category;
};

interface UpdateCategoryParams {
  name?: string;
  description?: string;
  is_public?: boolean;
}

interface UpdateCategoryResponse {
  success: boolean;
  message: string;
  updated_fields: string[];
  category: Category;
}

/**
 * Admin - Update category information
 */
export const adminUpdateCategory = async (
  categoryId: number,
  params: UpdateCategoryParams
): Promise<UpdateCategoryResponse> => {
  const response: AxiosResponse = await api.put(
    `/admin/categories/${categoryId}`,
    params
  );
  return response.data;
};

interface DeleteCategoryResponse {
  success: boolean;
  message: string;
  deleted_files_count: number;
  affected_knowledge_bases: number[];
  was_system_category: boolean;
}

/**
 * Admin - Delete a category
 */
export const adminDeleteCategory = async (
  categoryId: number
): Promise<DeleteCategoryResponse> => {
  const response: AxiosResponse = await api.delete(
    `/admin/categories/${categoryId}`
  );
  return response.data;
};

// ======================== Category File Management ========================

interface CategoryFilesResponse {
  success: boolean;
  data: {
    files: CategoryFile[];
    category_info: {
      id: number;
      name: string;
      type: CategoryType;
      is_system: boolean;
    };
    pagination: {
      total: number;
      pages: number;
      current_page: number;
      per_page: number;
      has_next: boolean;
      has_prev: boolean;
    };
  };
}

/**
 * Admin - Get files in a category
 */
export const adminGetCategoryFiles = async (
  categoryId: number,
  page = 1,
  perPage = 20,
  fileType?: "structural" | "non_structural"
): Promise<CategoryFilesResponse> => {
  const response: AxiosResponse = await api.get(
    `/admin/categories/${categoryId}/files`,
    {
      params: {
        page,
        per_page: perPage,
        type: fileType,
      },
    }
  );
  return response.data;
};

interface UploadFilesResponse {
  success: boolean;
  message: string;
  data: {
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
    is_system_category: boolean;
  };
}

/**
 * Admin - Upload files to category
 */
export const adminUploadFilesToCategory = async (
  categoryId: number,
  files: File[]
): Promise<UploadFilesResponse> => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response: AxiosResponse = await api.post(
    `/admin/categories/${categoryId}/files`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
};

interface DeleteFilesResponse {
  success: boolean;
  message: string;
  deleted: number[];
  failed: Array<{
    file_id: number;
    error: string;
  }>;
  knowledge_bases_updated: boolean;
  is_system_category: boolean;
}

/**
 * Admin - Batch delete files from category
 */
export const adminDeleteCategoryFiles = async (
  categoryId: number,
  fileIds: number[]
): Promise<DeleteFilesResponse> => {
  const response: AxiosResponse = await api.delete(
    `/admin/categories/${categoryId}/files`,
    { data: { file_ids: fileIds } }
  );
  return response.data;
};

export default {
  // Knowledge Base Management
  adminGetKnowledgeBases,
  adminCreateKnowledgeBase,
  adminBatchDeleteKnowledgeBases,
  adminUpdateKnowledgeBase,
  adminBatchAddCategoriesToKnowledgeBase,
  adminBatchRemoveCategoriesFromKnowledgeBase,
  adminUpdateSingleKnowledgeBase,
  adminBatchUpdateSystemKnowledgeBases,

  // Category Management
  adminSearchCategories,
  adminCreateCategory,
  adminUpdateCategory,
  adminDeleteCategory,

  // File Management
  adminGetCategoryFiles,
  adminUploadFilesToCategory,
  adminDeleteCategoryFiles,
};
