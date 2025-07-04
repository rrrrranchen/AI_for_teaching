import api from "@/request";
import type { AxiosResponse } from "axios";

export interface PPTTemplate {
  id: number;
  name: string;
  url: string;
  image_url: string;
}

export const pptTemplateApi = {
  /**
   * 获取所有PPT模板
   */
  async getTemplates(): Promise<PPTTemplate[]> {
    const response: AxiosResponse<PPTTemplate[]> = await api.get(
      "/ppt_templates"
    );
    return response.data;
  },

  /**
   * 创建PPT模板
   * @param formData 包含文件和图片的FormData
   */
  async createTemplate(formData: FormData): Promise<PPTTemplate> {
    const response: AxiosResponse<PPTTemplate> = await api.post(
      "/ppt_templates",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * 获取单个模板详情
   * @param id 模板ID
   */
  async getTemplate(id: number): Promise<PPTTemplate> {
    const response: AxiosResponse<PPTTemplate> = await api.get(
      `/ppt_templates/${id}`
    );
    return response.data;
  },

  /**
   * 删除模板
   * @param id 模板ID
   */
  async deleteTemplate(id: number): Promise<void> {
    await api.delete(`/ppt_templates/${id}`);
  },
};

export default pptTemplateApi;
