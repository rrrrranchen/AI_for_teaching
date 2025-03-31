import api from "@/request";
import type { AxiosResponse } from "axios";

// 课程基础类型
export interface Course {
  id: number;
  name: string;
  description: string;
  created_at: string;
  courseclass_id?: number;
}

// 创建课程参数
interface CreateCourseParams {
  name: string;
  description?: string;
  courseclass_id: number;
}

// 更新课程参数
interface UpdateCourseParams {
  name?: string;
  description?: string;
}

// 获取课程班的课程列表
export const getCoursesByCourseclass = async (
  courseclassId: number
): Promise<Course[]> => {
  const response: AxiosResponse<Course[]> = await api.get(
    `/courseclasses/${courseclassId}/courses`
  );
  return response.data;
};

// 为课程班添加课程
export const addCourseToCourseclass = async (
  courseclassId: number,
  data: CreateCourseParams
): Promise<Course> => {
  const response: AxiosResponse<Course> = await api.post(
    `/courseclasses/${courseclassId}/add_courses`,
    data
  );
  return response.data;
};

// 获取单个课程详情（仅限老师）
export const getCourseDetail = async (id: number): Promise<Course> => {
  const response: AxiosResponse<Course> = await api.get(`/courses/${id}`);
  return response.data;
};

// 更新课程信息（仅限老师）
export const updateCourse = async (
  id: number,
  data: UpdateCourseParams
): Promise<Course> => {
  const response: AxiosResponse<Course> = await api.put(`/courses/${id}`, data);
  return response.data;
};

// 删除课程（仅限老师）
export const deleteCourse = async (id: number): Promise<void> => {
  await api.delete(`/courses/${id}`);
};
