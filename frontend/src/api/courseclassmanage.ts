import api from "@/request";
import type { AxiosResponse } from "axios";

// 课程班基础类型
export interface CourseClass {
  id: number;
  name: string;
  description: string;
  created_at: string;
  invite_code: string;
  image_path?: string;
  teacher_count: number;
  student_count: number;
  course_count: number;
  teachers: Array<{ id: number; name: string }>;
  courses: Array<{ id: number; name: string }>;
}

// 排行榜课程班类型
export interface RankedCourseClass extends CourseClass {
  rank: number;
  recommend_index: number;
  stars: number;
  avg_accuracy: number;
  activity_ratio: number;
}

// 查询课程班参数
export interface QueryCourseClassesParams {
  name?: string;
  teacher_id?: number;
  student_id?: number;
  course_id?: number;
  invite_code?: string;
}

// 更新课程班参数
export interface UpdateCourseClassParams {
  name?: string;
  description?: string;
  image?: File; // 图片文件
}

// 批量删除参数
export interface DeleteCourseClassesParams {
  courseclass_ids: number[];
}

/**
 * 管理员课程班管理API
 */
export const adminCourseClassApi = {
  /**
   * 查询课程班列表
   * @param params 查询参数
   */
  async queryCourseClasses(
    params: QueryCourseClassesParams
  ): Promise<CourseClass[]> {
    const response: AxiosResponse<CourseClass[]> = await api.get(
      "/admin/query_courseclasses",
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
   * 更新课程班信息
   * @param courseclassId 课程班ID
   * @param data 更新数据
   */
  async updateCourseClass(
    courseclassId: number,
    data: FormData
  ): Promise<CourseClass> {
    const response: AxiosResponse<CourseClass> = await api.put(
      `/admin/update_courseclass/${courseclassId}`,
      data,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * 批量删除课程班
   * @param courseclassIds 课程班ID数组
   */
  async deleteCourseClasses(
    courseclassIds: number[]
  ): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await api.delete(
      "/admin/delete_courseclasses",
      { data: { courseclass_ids: courseclassIds } }
    );
    return response.data;
  },

  /**
   * 获取公开课程班排行榜
   */
  async getPublicCourseClassRanking(): Promise<RankedCourseClass[]> {
    const response: AxiosResponse<RankedCourseClass[]> = await api.get(
      "/public_courseclass_ranking"
    );
    return response.data;
  },
};

export default adminCourseClassApi;
