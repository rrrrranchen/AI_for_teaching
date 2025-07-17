// src/api/aichat.ts

export interface ChatMessage {
  query: string;
  thinking_mode: boolean;
  history?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  class_id: number; //问题需要
  // similarity_threshold?: number;
  // chunk_cnt?: number;
  // api_key?: string;
  // data_type_filter?: string | null;
}

export interface ChatResponse {
  status: "chunks" | "reasoning" | "content" | "end" | "error";
  content: any;
  sources?: {
    message: string;
    source_count: number;
    sources: Array<{
      knowledge_base: {
        id: number | null;
        name: string;
      };
      category: {
        id: number | null;
        name: string;
      };
      file: {
        id: number | null;
        name: string;
      };
      chunks: Array<{
        position: number;
        text: string;
        similarity: number;
        metadata: Record<string, any>;
      }>;
    }>;
  };
}

export interface Conversation {
  id: number;
  name: string;
  created_at: string;
  courseclass_id: number;
}

export interface ConversationDetail extends Conversation {
  messages: Array<{
    id: number;
    role: "user" | "assistant";
    content: string;
    thinkingMode?: boolean;
    thinkingContent?: string;
    sources?: ChatResponse["sources"];
  }>;
}

/**
 * 创建新的会话
 * @param courseclassId 班级ID
 * @returns 返回新创建的会话信息
 */
export const createConversation = async (
  courseclassId: number
): Promise<{
  success: boolean;
  chat_id: number;
  name: string;
  created_at: string;
}> => {
  const response = await fetch(
    `http://localhost:5000/create_conversation/${courseclassId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error(`创建会话失败: ${response.status}`);
  }

  return response.json();
};

/**
 * 获取班级的所有会话列表
 * @param courseclassId 班级ID
 * @returns 返回会话列表
 */
export const getCourseClassConversations = async (
  courseclassId: number
): Promise<Conversation[]> => {
  const response = await fetch(
    `http://localhost:5000/course_class_conversations/${courseclassId}`,
    {
      method: "GET",
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error(`获取会话列表失败: ${response.status}`);
  }

  return response.json();
};

/**
 * 获取会话详情
 * @param chatHistoryId 会话ID
 * @returns 返回会话详情
 */
export const getConversationDetail = async (
  chatHistoryId: number
): Promise<ConversationDetail> => {
  const response = await fetch(
    `http://localhost:5000/conversation_detail/${chatHistoryId}`,
    {
      method: "GET",
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error(`获取会话详情失败: ${response.status}`);
  }

  return response.json();
};

/**
 * 更新会话名称
 * @param chatHistoryId 会话ID
 * @param newName 新名称
 * @returns 返回更新结果
 */
export const updateConversationName = async (
  chatHistoryId: number,
  newName: string
): Promise<{
  success: boolean;
  new_name: string;
  chat_id: number;
}> => {
  const response = await fetch(
    `http://localhost:5000/update_conversation_name/${chatHistoryId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ new_name: newName }),
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error(`更新会话名称失败: ${response.status}`);
  }

  return response.json();
};

/**
 * 基于会话的AI聊天接口(流式)
 * @param chatHistoryId 会话ID
 * @param message 聊天消息对象
 * @param onMessage 消息回调函数
 * @param onError 错误回调函数
 * @param onComplete 完成回调函数
 * @returns 返回一个可选的取消函数
 */
export const courseClassChat = (
  chatHistoryId: number,
  message: ChatMessage,
  onMessage: (response: ChatResponse) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): (() => void) | undefined => {
  // 验证必要参数
  if (!message.query || message.thinking_mode === undefined) {
    const error = new Error("缺少必要字段: query, thinking_mode");
    onError?.(error);
    return;
  }

  // 使用fetch API实现流式请求
  const controller = new AbortController();
  const signal = controller.signal;

  fetch(`http://localhost:5000/course_class_chat/${chatHistoryId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(message),
    signal,
    credentials: "include",
  })
    .then((response) => {
      if (!response.ok || !response.body) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const processStream = async () => {
        try {
          // eslint-disable-next-line no-constant-condition
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              onComplete?.();
              return;
            }

            buffer += decoder.decode(value, { stream: true });

            // 处理可能的多条消息
            const parts = buffer.split("\n\n");
            buffer = parts.pop() || "";

            for (const part of parts) {
              if (part.startsWith("data: ")) {
                const data = JSON.parse(part.substring(6)) as ChatResponse;
                onMessage(data);
              }
            }
          }
        } catch (error) {
          onError?.(error as Error);
        } finally {
          onComplete?.();
        }
      };

      processStream();
    })
    .catch((error) => {
      onError?.(error);
      onComplete?.();
    });

  // 返回取消函数
  return () => {
    controller.abort();
  };
};

/**
 * 题目专用的AI聊天接口(流式)
 * @param questionId 题目ID
 * @param message 聊天消息对象
 * @param onMessage 消息回调函数
 * @param onError 错误回调函数
 * @param onComplete 完成回调函数
 * @returns 返回一个可选的取消函数
 */
export const questionClassChat = (
  questionId: number,
  message: ChatMessage,
  onMessage: (response: ChatResponse) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): (() => void) | undefined => {
  // 验证必要参数
  if (
    !message.query ||
    message.thinking_mode === undefined ||
    !message.class_id
  ) {
    const error = new Error("缺少必要字段: query, thinking_mode, class_id");
    onError?.(error);
    return;
  }

  // 使用fetch API实现流式请求
  const controller = new AbortController();
  const signal = controller.signal;

  fetch(`http://localhost:5000/question_chat/${questionId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...message,
      include_answer_analysis: true, // 默认包含题目分析
    }),
    signal,
    credentials: "include",
  })
    .then((response) => {
      if (!response.ok || !response.body) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullResponse = "";

      const processStream = async () => {
        try {
          // eslint-disable-next-line no-constant-condition
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              onComplete?.();
              return;
            }

            buffer += decoder.decode(value, { stream: true });

            // 处理可能的多条消息
            const parts = buffer.split("\n\n");
            buffer = parts.pop() || "";

            for (const part of parts) {
              if (part.startsWith("data: ")) {
                const data = JSON.parse(part.substring(6)) as ChatResponse;
                if (data.status === "content") {
                  fullResponse += data.content;
                }
                onMessage(data);
              }
            }
          }
        } catch (error) {
          onError?.(error as Error);
        } finally {
          onComplete?.();
        }
      };

      processStream();
    })
    .catch((error) => {
      onError?.(error);
      onComplete?.();
    });

  // 返回取消函数
  return () => {
    controller.abort();
  };
};
