import api from "@/request";
import type { AxiosResponse } from "axios";

// 课程班基础类型
export interface Courseclass {
  id: number;
  name: string;
  description: string;
  created_at: string;
  invite_code: string;
  teacher_count?: number;
  student_count?: number;
  course_count?: number;
  is_joined?: boolean; // 当前用户是否已加入
  teachers?: Teacher[]; // 新增：存储课程班的老师信息
}

// 老师类型
export interface Teacher {
  id: number;
  username: string;
}

// 学生类型
export interface Student {
  id: number;
  username: string;
}

// 获取课程班学生列表的返回类型
export interface GetStudentsResponse {
  total: number; // 学生总数
  students: Student[]; // 学生列表
}

// 创建课程班参数
interface CreateCourseclassParams {
  name: string;
  description?: string;
}

// 加入课程班参数
interface JoinCourseclassParams {
  invite_code: string;
}

// 退出课程班参数
interface LeaveCourseclassParams {
  courseclass_id: number;
}

// 公用部分
//
//
//
// 获取老师创建的课程班列表
export const getAllCourseclasses = async (): Promise<Courseclass[]> => {
  const response: AxiosResponse<Courseclass[]> = await api.get(
    "/courseclasses"
  );
  return response.data;
};

// 获取单个课程班详情，包括邀请码
export const getCourseclassDetail = async (
  id: number
): Promise<Courseclass> => {
  const response: AxiosResponse<Courseclass> = await api.get(
    `/courseclasses/${id}`
  );
  return response.data;
};

// 查询课程班的学生
export const getStudentsByCourseclass = async (
  courseclassId: number
): Promise<GetStudentsResponse> => {
  const response: AxiosResponse<GetStudentsResponse> = await api.get(
    `/courseclasses/${courseclassId}/students`
  );
  return response.data;
};

// 搜索课程班
export const searchCourseclasses = async (
  query: string
): Promise<Courseclass[]> => {
  const response: AxiosResponse<Courseclass[]> = await api.get(
    "/search_courseclasses",
    { params: { query } }
  );
  return response.data;
};

// 老师部分
//
//
//
// 创建课程班，后端会自动生成邀请码
export const createCourseclass = async (
  data: CreateCourseclassParams
): Promise<Courseclass> => {
  const response: AxiosResponse<Courseclass> = await api.post(
    "/createcourseclasses",
    data
  );
  return response.data;
};
// 更新课程班信息（仅限老师）
export const updateCourseclass = async (
  id: number,
  data: Partial<CreateCourseclassParams>
): Promise<Courseclass> => {
  const response: AxiosResponse<Courseclass> = await api.put(
    `/courseclasses/${id}`,
    data
  );
  return response.data;
};

// 删除课程班（仅限老师）
export const deleteCourseclass = async (id: number): Promise<void> => {
  await api.delete(`/deletecourseclasses/${id}`);
};

// 学生部分
//
//
//
// 通过邀请码加入课程班
export const joinCourseclassByCode = async (
  data: JoinCourseclassParams
): Promise<Courseclass> => {
  const response: AxiosResponse<Courseclass> = await api.post(
    "/student_join_courseclass",
    data
  );
  return response.data;
};
// 退出课程班
export const leaveCourseclass = async (
  data: LeaveCourseclassParams
): Promise<void> => {
  await api.post("/student_leave_courseclass", data);
};

// // 添加课程参数
// interface ManageCoursesParams {
//   course_ids: number[];
// }
// // 为课程班添加课程
// export const addCoursesToClass = async (
//   courseclassId: number,
//   data: ManageCoursesParams
// ): Promise<void> => {
//   await api.post(`/courseclasses/${courseclassId}/add_courses`, data);
// };

// // 从课程班移除课程
// export const removeCoursesFromClass = async (
//   courseclassId: number,
//   data: ManageCoursesParams
// ): Promise<void> => {
//   await api.post(`/courseclasses/${courseclassId}/remove_courses`, data);
// };
