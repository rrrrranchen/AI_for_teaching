// src/api.ts
import api from "@/request";
import type { AxiosResponse } from "axios";

// ======================== 类型定义 ========================
export interface ForumAttachment {
  attachment_id: number;
  file_path: string;
  uploader_id: number;
  created_at: string;
}

export interface ForumPost {
  id: number;
  title: string;
  content: string;
  author_id: number;
  author_name: string;
  author_avatar: string;
  created_at: {
    $date: string;
  };
  updated_at?: {
    $date: string;
  };
  view_count: number;
  like_count: number;
  favorite_count: number;
  is_pinned: boolean;
  teaching_design_versions: number[];
  attachments: number[];
  tags?: string[];
  is_liked: boolean;
  is_favorited: boolean;
  first_image?: string;
}

export interface ForumComment {
  id: number;
  content: string;
  author_id: number;
  author_name: string;
  author_avatar: string;
  post_id: number;
  parent_id?: number;
  created_at: {
    $date: string;
  };
  replies?: ForumComment[];
}

export interface ForumFavorite {
  id: number;
  post_id: number;
  post_title: string;
  author_id: number;
  created_at: string;
}

export interface ForumUsers {
  id: number;
  post_id: number;
  post_title: string;
  author_id: number;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  pages: number;
  current_page: number;
}
export interface ForumTag {
  id: number;
  name: string;
}

// 推荐教学设计类型
export interface RecommendedTeachingDesign {
  design_id: number;
  title: string;
  course_id: number;
  creator_id: number;
  author_name: string;
  author_avatar?: string;
  version_content: string;
  recommend_time?: string;
  first_image?: string;
}

// ======================== API 接口 ========================
export const forumApi = {
  // 上传附件
  async uploadAttachments(files: File[]): Promise<ForumAttachment[]> {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const response: AxiosResponse<{ results: ForumAttachment[] }> =
      await api.post("/attachments", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
    return response.data.results;
  },

  // 创建帖子
  async createPost(params: {
    title: string;
    content: string;
    tags?: string[];
    teaching_design_version_ids?: number[];
    attachment_ids?: number[];
  }): Promise<ForumPost> {
    const response: AxiosResponse<ForumPost> = await api.post("/posts", params);
    return response.data;
  },

  // 获取帖子列表
  async getPosts(
    sortBy:
      | "composite"
      | "created_at"
      | "like_count"
      | "favorite_count"
      | "view_count" = "composite"
  ): Promise<ForumPost[]> {
    const response: AxiosResponse<ForumPost[]> = await api.get("/posts", {
      params: { sort_by: sortBy },
    });
    return response.data;
  },

  // 获取帖子详情
  async getPostDetail(postId: number): Promise<ForumPost> {
    const response: AxiosResponse<ForumPost> = await api.get(
      `/posts/${postId}`
    );
    return response.data;
  },

  // 删除帖子
  async deletePost(postId: number): Promise<void> {
    await api.delete(`/posts/${postId}`);
  },

  // 更新帖子
  async updatePost(
    postId: number,
    params: {
      title?: string;
      content?: string;
      teaching_design_version_ids?: number[];
      attachment_ids?: number[];
    }
  ): Promise<ForumPost> {
    const response: AxiosResponse<ForumPost> = await api.put(
      `/posts/${postId}`,
      params
    );
    return response.data;
  },

  // 点赞帖子
  async likePost(postId: number): Promise<void> {
    await api.post(`/posts/${postId}/like`);
  },

  // 取消点赞
  async unlikePost(postId: number): Promise<void> {
    await api.delete(`/posts/${postId}/like`);
  },

  // 收藏帖子
  async favoritePost(postId: number): Promise<void> {
    await api.post(`/posts/${postId}/favorite`);
  },

  // 取消收藏
  async unfavoritePost(postId: number): Promise<void> {
    await api.delete(`/posts/${postId}/favorite`);
  },

  // 获取评论
  async getComments(postId: number): Promise<ForumComment[]> {
    const response: AxiosResponse<ForumComment[]> = await api.get(
      `/posts/${postId}/comments`
    );
    return response.data;
  },

  // 添加评论
  async addComment(
    postId: number,
    params: {
      content: string;
      parent_id?: number;
    }
  ): Promise<ForumComment> {
    const response: AxiosResponse<ForumComment> = await api.post(
      `/posts/${postId}/comments`,
      params
    );
    return response.data;
  },

  // 删除评论
  async deleteComment(commentId: number): Promise<void> {
    await api.delete(`/comments/${commentId}`);
  },

  // 获取附件列表
  async getAttachments(postId: number): Promise<ForumAttachment[]> {
    const response: AxiosResponse<ForumAttachment[]> = await api.get(
      `/posts/${postId}/attachments`
    );
    return response.data;
  },

  //获取用户帖子
  async getUserPosts(): Promise<ForumPost[]> {
    const response: AxiosResponse<ForumPost[]> = await api.get("/users/posts");
    return response.data;
  },

  // 获取用户收藏
  async getUserFavorites(): Promise<ForumPost[]> {
    const response: AxiosResponse<ForumPost[]> = await api.get(
      "/users/favorites"
    );
    return response.data;
  },

  // 搜索帖子
  async searchPosts(keyword: string): Promise<ForumPost[]> {
    const response: AxiosResponse<ForumPost[]> = await api.get(
      "/posts/search",
      {
        params: { keyword },
      }
    );
    return response.data;
  },

  // 获取所有标签
  async getAllTags(): Promise<ForumTag[]> {
    const response: AxiosResponse<ForumTag[]> = await api.get("/get_alltags");
    return response.data;
  },

  // 获取推荐教学设计
  async getRecommendedDesigns(): Promise<RecommendedTeachingDesign[]> {
    const response: AxiosResponse<RecommendedTeachingDesign[]> = await api.get(
      "/recommended_designs"
    );
    return response.data;
  },
};

export default forumApi;
