"""
文件名: teaching_design_generator_with_optimizer.py
描述: 包含优化专家的中文教学设计生成系统
"""
import json
import re
import fire
from typing import Dict, Any

import metagpt
from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team

from action import 优化教学设计, 学生画像构建器, 教学评估设计, 最终优化设计, 编写教学材料, 设计课程大纲
from role import 上课模拟器, 增强优化专家, 学生智能体, 教学材料编写者, 教学评估专家, 课堂分析师, 课堂模拟教师, 课程设计师
def _is_triggered_by(self, action_class):
        """检查是否由特定动作类触发"""
        last_msg = self.rc.memory.get()[-1]
        cause_by = last_msg.cause_by
        
        # 获取类名的字符串表示（包含模块路径）
        if hasattr(cause_by, '__name__'):
            cause_by_name = f"{cause_by.__module__}.{cause_by.__name__}"
        else:
            cause_by_name = str(cause_by)
        
        # 获取目标动作类的字符串表示
        target_name = f"{action_class.__module__}.{action_class.__name__}"
        
        return cause_by_name == target_name

async def main(
    objective: str = "计算机网络TCP原理",
    teaching_content: str = "TCP协议的详细工作机制，包括三次握手、流量控制、拥塞控制等",
    student_feedback: str = """
[
  {
    "student_id": "S001",
    "questions": [
      {
        "question": "TCP三次握手的主要目的是什么？",
        "answer": "TCP三次握手的主要目的是确保通信双方都能发送和接收数据，同步序列号，并交换TCP窗口大小信息。"
      },
      {
        "question": "TCP和UDP的主要区别是什么？",
        "answer": "TCP是面向连接的可靠传输协议，提供流量控制和拥塞控制；UDP是无连接的不可靠传输协议，开销小、延迟低，适用于实时应用。"
      }
    ]
  },
  {
    "student_id": "S002",
    "questions": [
      {
        "question": "TCP流量控制是如何实现的？",
        "answer": "TCP通过滑动窗口机制实现流量控制，接收方通过通告窗口大小告知发送方自己还能接收多少数据。"
      },
      {
        "question": "什么是TCP拥塞控制？",
        "answer": "TCP拥塞控制是防止网络过度拥塞的机制，主要包括慢启动、拥塞避免、快速重传和快速恢复等算法。"
      }
    ]
  },
  {
    "student_id": "S003",
    "questions": [
      {
        "question": "TCP如何保证数据的可靠传输？",
        "answer": "TCP通过序列号、确认应答、超时重传、流量控制和拥塞控制等机制保证数据的可靠传输。"
      },
      {
        "question": "TCP头部中的标志位有哪些？",
        "answer": "TCP头部中的标志位包括URG、ACK、PSH、RST、SYN和FIN，分别表示紧急指针有效、确认号有效、推送数据、重置连接、同步序列号和结束连接。"
      }
    ]
  }
]
    """,
    knowledge_base: str = "《计算机网络：自顶向下方法》、《TCP/IP详解》等权威教材",
    investment: float = 10.0,
    n_round: int = 10
):
    """主函数，运行完整教学模拟系统"""
    # 创建团队
    team = Team()
    
    # 设置上下文（学生反馈数据）
    team.env.context = {
        "student_feedback": student_feedback
    }
    
    # 招聘核心角色
    team.hire([
        课程设计师(
            objective=objective,
            teaching_content=teaching_content,
            knowledge_base=knowledge_base
        ),
        教学材料编写者(),
        教学评估专家(),
        增强优化专家(),
        学生画像构建器(),
        课堂模拟教师(),
        课堂分析师()
    ])
    
    # 创建学生智能体（基于反馈数据）
    try:
        feedback_data = json.loads(student_feedback)
        for student in feedback_data:
            student_id = student["student_id"]
            team.hire(学生智能体(
                name=f"学生{student_id}",
                profile=f"学生{student_id}",
                student_data={
                    "student_id": student_id,
                    "strengths": [],
                    "weaknesses": [],
                    "learning_style": "通用型"
                }
            ))
    except Exception as e:
        logger.error(f"创建学生智能体失败: {str(e)}")
    
    # 投资并运行项目
    team.invest(investment)
    team.run_project(f"{objective}课程开发与模拟")
    
    # 运行团队协作
    await team.run(n_round=n_round)
    
    # 收集最终结果
    results = {
        "course_outline": "",
        "teaching_materials": "",
        "assessment": "",
        "optimized_design": "",
        "final_design": "",
        "class_simulation": ""
    }
    
    # 提取各阶段成果
    for role in team.env.roles.values():
        for msg in role.rc.memory.get():
            if isinstance(role, 课程设计师) and isinstance(msg.cause_by, 设计课程大纲):
                results["course_outline"] = msg.content
            elif isinstance(role, 教学材料编写者) and isinstance(msg.cause_by, 编写教学材料):
                results["teaching_materials"] = msg.content
            elif isinstance(role, 教学评估专家) and isinstance(msg.cause_by, 教学评估设计):
                results["assessment"] = msg.content
            elif isinstance(role, 增强优化专家) and isinstance(msg.cause_by, 优化教学设计):
                results["optimized_design"] = msg.content
            elif isinstance(role, 增强优化专家) and isinstance(msg.cause_by, 最终优化设计):
                results["final_design"] = msg.content
            elif isinstance(role, 课堂模拟教师) and isinstance(msg.cause_by, 教学流程执行):
                results["class_simulation"] = msg.content
    
    # 返回最终优化结果
    if results["final_design"]:
        return results["final_design"]
    elif results["optimized_design"]:
        return results["optimized_design"]
    else:
        return json.dumps(results, ensure_ascii=False, indent=2)
    




if __name__ == "__main__":
    fire.Fire(main)