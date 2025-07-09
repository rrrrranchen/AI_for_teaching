// src/api/aichat.ts

export interface ChatMessage {
  query: string;
  class_id: number;
  thinking_mode: boolean;
  // history?: Array<{
  //   role: "user" | "assistant";
  //   content: string;
  // }>;
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

/**
 * 基于班级知识库的AI聊天接口(流式)
 * @param message 聊天消息对象
 * @param onMessage 消息回调函数
 * @param onError 错误回调函数
 * @param onComplete 完成回调函数
 * @returns 返回一个可选的取消函数
 */
export const courseClassChat = (
  message: ChatMessage,
  onMessage: (response: ChatResponse) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): (() => void) | undefined => {
  // 验证必要参数
  if (
    !message.class_id ||
    !message.query ||
    message.thinking_mode === undefined
  ) {
    const error = new Error("缺少必要字段: class_id, query, thinking_mode");
    onError?.(error);
    return;
  }

  // 使用EventSource的替代方案 - 使用fetch API
  const controller = new AbortController();
  const signal = controller.signal;

  // 使用POST请求
  fetch("http://localhost:5000/course_class_chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(message),
    signal,
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

// 备用方案：如果后端不支持GET请求的SSE，可以使用fetch API实现
// export const courseClassChatWithFetch = async (
//   message: ChatMessage,
//   onMessage: (response: ChatResponse) => void,
//   onError?: (error: Error) => void,
//   onComplete?: () => void
// ): Promise<() => void> => {
//   try {
//     const response = await fetch("http://localhost:5000/course_class_chat", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify(message),
//     });

//     if (!response.ok || !response.body) {
//       throw new Error(`请求失败: ${response.status}`);
//     }

//     const reader = response.body.getReader();
//     const decoder = new TextDecoder();
//     let buffer = "";

//     const cancel = () => {
//       reader.cancel();
//     };

//     const processStream = async () => {
//       try {
//         while (true) {
//           const { done, value } = await reader.read();
//           if (done) {
//             onComplete?.();
//             return;
//           }

//           buffer += decoder.decode(value, { stream: true });

//           // 处理可能的多条消息
//           const parts = buffer.split("\n\n");
//           buffer = parts.pop() || "";

//           for (const part of parts) {
//             if (part.startsWith("data: ")) {
//               const data = JSON.parse(part.substring(6)) as ChatResponse;
//               onMessage(data);
//             }
//           }
//         }
//       } catch (error) {
//         onError?.(error as Error);
//       } finally {
//         onComplete?.();
//       }
//     };

//     processStream();
//     return cancel;
//   } catch (error) {
//     onError?.(error as Error);
//     return () => {};
//   }
// };
