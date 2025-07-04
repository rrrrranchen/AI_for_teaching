import api from "@/request";
import type { AxiosResponse } from "axios";

// 用户基础类型
export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  signature?: string;
  avatar?: string;
  created_at: string;
}

// 查询用户参数
export interface QueryUsersParams {
  role?: string; // 角色筛选参数
  username?: string; // 用户名筛选参数
}

// 添加用户参数
export interface AddUserParams {
  username: string;
  password: string;
  role: string;
  email: string;
  signature?: string;
}

// 更新用户参数
export interface UpdateUserParams {
  username?: string;
  email?: string;
  role?: string;
  signature?: string;
  password?: string;
}

// 批量删除用户参数
export interface DeleteUsersParams {
  user_ids: number[];
}

/**
 * 管理员API - 用户管理
 */
export const adminApi = {
  /**
   * 查询用户列表
   * @param params 查询参数
   */
  async queryUsers(params: QueryUsersParams): Promise<User[]> {
    const response: AxiosResponse<User[]> = await api.get(
      "/admin/query_users",
      {
        params,
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    return response.data;
  },

  /**
   * 添加用户
   * @param userData 用户数据
   */
  async addUser(userData: AddUserParams): Promise<User> {
    const response: AxiosResponse<User> = await api.post(
      "/admin/add_user",
      userData
    );
    return response.data;
  },

  /**
   * 更新用户信息
   * @param userId 用户ID
   * @param userData 更新数据
   */
  async updateUser(userId: number, userData: UpdateUserParams): Promise<User> {
    const response: AxiosResponse<User> = await api.put(
      `/admin/update_user/${userId}`,
      userData
    );
    return response.data;
  },

  /**
   * 批量删除用户
   * @param userIds 用户ID数组
   */
  async deleteUsers(userIds: number[]): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await api.delete(
      "/admin/delete_users",
      { data: { user_ids: userIds } }
    );
    return response.data;
  },
};

export default adminApi;
