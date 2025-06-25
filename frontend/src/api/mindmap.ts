import api from "@/request";
import type { AxiosResponse } from "axios";

// ======================== 类型定义 ========================
export interface QuestionStat {
  id: number;
  course_id: number;
  type: "choice" | "fill" | "short_answer";
  content: string;
  correct_answer: string;
  difficulty: string;
  timing: string;
  is_public: boolean;
  statistics?: {
    options?: Array<{
      option: string;
      count: number;
      percentage: number;
      is_correct: boolean;
    }>;
    correct?: {
      count: number;
      percentage: number;
    };
    top_errors?: Array<{
      answer: string;
      count: number;
      percentage: number;
    }>;
    other_errors?: {
      count: number;
      percentage: number;
    };
    score_ranges?: Array<{
      range: string;
      count: number;
      percentage: number;
    }>;
  };
}

export interface LeafQuestion {
  knowledge_point_id: number;
  knowledge_point_name: string;
  knowledge_point_content: string;
  questions: QuestionStat[];
}

export interface AIAnalysisResponse {
  knowledge_point_id: number;
  knowledge_point_name: string;
  analysis_report: string;
  timestamp: string;
}

export interface UpdateKnowledgePointParams {
  node_name?: string;
  node_content?: string;
  parent_node_id?: number;
}

export interface UpdateKnowledgePointResponse {
  message: string;
  knowledge_point_id: number;
  node_name: string;
  node_content: string;
  parent_node_id: number | null;
  is_leaf: boolean;
}

// ======================== API方法 ========================
export const mindmapApi = {
  /**
   * 获取知识点关联题目及统计信息
   * @param knowledgePointId 知识点ID
   */
  async getKnowledgeQuestions(
    knowledgePointId: number
  ): Promise<{ leaf_questions: LeafQuestion[] }> {
    const response: AxiosResponse = await api.get(
      `/knowledge/${knowledgePointId}/questions`
    );
    return response.data;
  },

  /**
   * 生成知识点AI分析报告
   * @param knowledgePointId 知识点ID
   */
  async generateAIAnalysis(
    knowledgePointId: number
  ): Promise<AIAnalysisResponse> {
    const response: AxiosResponse = await api.post(
      `/knowledge/${knowledgePointId}/ai_analysis`
    );
    return response.data;
  },

  /**
   * 获取知识点AI分析报告
   * @param knowledgePointId 知识点ID
   */
  async getAIAnalysis(knowledgePointId: number): Promise<AIAnalysisResponse> {
    const response: AxiosResponse = await api.get(
      `/knowledge/${knowledgePointId}/ai_analysis`
    );
    return response.data;
  },

  /**
   * 更新知识点信息
   * @param knowledgePointId 知识点ID
   * @param params 更新参数
   */
  async updateKnowledgePoint(
    knowledgePointId: number,
    params: UpdateKnowledgePointParams
  ): Promise<UpdateKnowledgePointResponse> {
    const response: AxiosResponse = await api.put(
      `/knowledge/${knowledgePointId}/update`,
      params
    );
    return response.data;
  },
};

export default mindmapApi;
