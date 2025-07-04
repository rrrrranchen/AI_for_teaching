import api from "@/request";
import type { AxiosResponse } from "axios";

export interface MongoDate {
  $date: string;
}

// 课程班基础类型
export interface Courseclass {
  id: number;
  name: string;
  description: string;
  created_at: MongoDate;
  invite_code: string;
  is_public: boolean; // 新增：是否公开
  image_path?: string; // 新增：图片路径
  teacher_count?: number;
  student_count?: number;
  course_count?: number;
  is_joined?: boolean; // 当前用户是否已加入
  teachers?: Teacher[]; // 存储课程班的老师信息
}

// 老师类型
export interface Teacher {
  id: number;
  username: string;
  avatar?: string;
}

// 学生类型
export interface Student {
  id: number;
  username: string;
  avatar?: string;
}

// 获取课程班学生列表的返回类型
export interface GetStudentsResponse {
  total: number; // 学生总数
  students: Student[]; // 学生列表
}

// 创建课程班参数
export interface CreateCourseclassParams {
  name: string;
  description?: string;
  is_public?: boolean; // 新增：是否公开
  image?: File; // 新增：图片文件
}

// 更新课程班参数
interface UpdateCourseclassParams {
  name?: string;
  description?: string;
  image?: File; // 新增：图片文件
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
// 获取用户的课程班列表
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
// 修改接口定义，使其支持FormData
export const createCourseclass = async (
  formData: FormData // 直接接受 FormData 类型
): Promise<Courseclass> => {
  const response: AxiosResponse<Courseclass> = await api.post(
    "/createcourseclasses",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
};

// 更新课程班信息（仅限老师）
// 更新课程班方法
export const updateCourseclass = async (
  id: number,
  data: FormData
): Promise<Courseclass> => {
  const response: AxiosResponse<Courseclass> = await api.put(
    `/courseclasses/${id}`,
    data,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
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
