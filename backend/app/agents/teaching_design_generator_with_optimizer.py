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

from action import 优化教学设计, 最终优化设计, 设计课程大纲
from role import 上课模拟器, 增强优化专家, 教学材料编写者, 教学评估专家, 课程设计师
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
    objective: str = "计算机网络tcp原理",
    teaching_content: str = "tcp的详细内容",
    feed_back: str = """
    [
  {
    "student_id": "S001",
    "questions": [
      {
        "question": "什么是OSI七层模型？",
        "answer": "OSI七层模型是国际标准化组织提出的网络通信参考模型，自上而下依次为应用层、表示层、会话层、传输层、网络层、数据链路层和物理层。"
      },
      {
        "question": "TCP与UDP的主要区别是什么？",
        "answer": "TCP是面向连接的可靠传输协议，提供流量控制和拥塞控制；UDP是无连接的不可靠传输协议，开销小、延迟低，适用于实时应用。"
      }
    ]
  },
  {
    "student_id": "S002",
    "questions": [
      {
        "question": "IP地址分为几类？",
        "answer": "IPv4地址传统上分为五类：A类（1.0.0.0–126.255.255.255）、B类（128.0.0.0–191.255.255.255）、C类（192.0.0.0–223.255.255.255）、D类组播（224.0.0.0–239.255.255.255）和E类保留（240.0.0.0–255.255.255.255）。"
      },
      {
        "question": "什么是子网掩码？",
        "answer": "子网掩码用于划分网络位和主机位，通过与IP地址按位与运算得到网络地址，从而实现子网划分与路由选择。"
      }
    ]
  },
  {
    "student_id": "S003",
    "questions": [
      {
        "question": "HTTP与HTTPS的区别？",
        "answer": "HTTP以明文传输数据，不安全；HTTPS在HTTP基础上加入SSL/TLS加密层，提供身份验证、数据加密和完整性保护，默认端口443。"
      },
      {
        "question": "三次握手过程？",
        "answer": "1) 客户端发送SYN=1,seq=x；2) 服务端回复SYN=1,ACK=1,seq=y,ack=x+1；3) 客户端发送ACK=1,seq=x+1,ack=y+1。完成连接建立。"
      }
    ]
  },
  {
    "student_id": "S004",
    "questions": [
      {
        "question": "DNS的作用是什么？",
        "answer": "DNS（域名系统）将人类可读的域名解析为机器可读的IP地址，实现域名到IP地址的映射，便于用户访问互联网资源。"
      },
      {
        "question": "什么是NAT？",
        "answer": "网络地址转换（NAT）在私有网络与公网之间进行IP地址转换，允许多个内部主机共享一个或少量的公网IP地址，提升地址利用率并增强安全性。"
      }
    ]
  }
]
    """,
    knowledge: str= "知识库检索结果",
    investment: float = 5.0,
    n_round: int = 100,
    add_human: bool = False,
):
    """主函数，运行完整教学模拟系统"""
    team = Team()
    team.hire([
        课程设计师(teaching_content=teaching_content, objective=objective, knowledge=knowledge),
        教学材料编写者(),
        教学评估专家(),
        增强优化专家(),  # 这是我们要找的角色
        上课模拟器(feed_back=feed_back)
    ])
    
    team.invest(investment)
    team.run_project(f"{objective}课程开发与模拟")
    await team.run(n_round=n_round)
    
    # 调试：打印所有角色profile
    print("所有角色列表:")
    for role in team.env.get_roles().values():
        print(f"- {role.profile}")
    
    # 正确查找增强优化专家（注意profile名称）
    optimizer = None
    for role in team.env.get_roles().values():
        if role.profile == "增强优化专家":  # 与增强优化专家类中的定义一致
            optimizer = role
            print(f"\n找到优化专家: {role.profile}")
            break
    
    if not optimizer:
        return "错误：未找到教学设计优化师角色"
    optimizer_msgs = []
    # 打印优化专家的所有消息
    print("\n优化专家的消息历史:")
    for i, msg in enumerate(optimizer.rc.memory.get()):
        cause_by=msg.cause_by
        if hasattr(cause_by, '__name__'):
            cause_by_name = f"{cause_by.__module__}.{cause_by.__name__}"
        else:
            cause_by_name = str(cause_by)
        target_name = f"{最终优化设计.__module__}.{最终优化设计.__name__}"
        if target_name==cause_by_name:

            optimizer_msgs.append(msg)
            print("找到了！！！！！！！！！！！！！！！！！")
        print(f"消息 {i}: {cause_by} - {msg.content[:50]}...")
    
    # 获取所有优化教学设计动作产生的消息
    
    
    print(f"\n找到的优化消息数量: {len(optimizer_msgs)}")
    for i, msg in enumerate(optimizer_msgs):
        print(f"优化消息 {i+1} 内容片段: {msg.content[:100]}...")
    
    # 返回结果
    if len(optimizer_msgs) >= 2:
        print("\n返回第二次优化结果")
        return optimizer_msgs[1].content
    elif optimizer_msgs:
        print("\n返回最后一次优化结果")
        return optimizer_msgs[-1].content
    else:
        print("\n无优化结果，可能原因:")
        print("- n_round设置太小（当前为{n_round}，建议≥3）")
        print("- 团队协作流程未完整执行")
        print("- 消息过滤条件不匹配")
        return "尚未产生任何优化教学设计结果"
    

  
if __name__ == "__main__":
    fire.Fire(main)