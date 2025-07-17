
import datetime
import json
import re
import fire
from typing import Dict, Any
from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team

from action import 上课模拟, 优化教学设计, 分析课堂报告, 教学优化建议, 教学评估设计, 最终优化设计,   编写教学材料, 设计课程大纲,  课堂观察评估



class 课程设计师(Role):
    """课程设计师角色，负责设计课程大纲"""
    name: str = "李老师"
    profile: str = "课程设计师"
    objective: str = "计算机网络tcp原理"
    teaching_content: str = "tcp的详细内容"
    knowledge_base: str = "知识库内容"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([UserRequirement])
        self.set_actions([设计课程大纲])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        objective = self.objective
        teaching_content = self.teaching_content
        knowledge_base= self.knowledge_base
        outline = await todo.run(teaching_content=teaching_content,objective=objective,knowledge_base=knowledge_base)
        content: str = json.dumps({
            "type": "course_outline",
            "teaching_content": self.teaching_content,
            "objective": self.objective,
            "outline": outline
        })
        msg = Message(content=content, role=self.profile, cause_by=type(todo))
        
        return msg
    

class 教学材料编写者(Role):
    """教学材料编写者角色，负责开发具体教学资源"""
    name: str = "王老师"
    profile: str = "教学材料编写者"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([编写教学材料])
        self._watch([设计课程大纲])
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 准备编写教学材料")
        
        # 从历史消息中提取结构化数据
        last_msg = self.rc.memory.get()[-1]
        
        try:
            data = json.loads(last_msg.content)
            outline=data["outline"]
            # 执行Action
            materials = await self.rc.todo.run(
                outline=outline
            )
            
            return Message(
                content=materials,
                role=self.profile,
                cause_by=type(self.rc.todo)
            )
            
        except Exception as e:
            logger.error(f"材料编写失败: {str(e)}")
            raise

class 教学评估专家(Role):
    """教学评估专家角色，负责评估设计和优化建议"""
    name: str = "张教授"
    profile: str = "教学评估专家"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化时设置两个动作
        self.set_actions([教学评估设计, 教学优化建议])
        self._watch([编写教学材料])
        
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 开始评估流程")
        
        # 获取第一个动作：教学评估设计
        assessment_action = self.actions[0]
        self.set_todo(assessment_action)
        assessment = await self.rc.todo.run(
            materials=self.rc.memory.get()[-1].content
        )
        
        # 获取第二个动作：教学优化建议
        optimization_action = self.actions[1]
        self.set_todo(optimization_action)
        optimization = await self.rc.todo.run(
            assessment=assessment
        )
        
        # 合并结果
        full_content = json.dumps({
            "assessment": assessment,
            "optimization": optimization
        })
        
        return Message(
            content=full_content,
            role=self.profile,
            cause_by=type(self.rc.todo)
        )

# 增强版优化专家（支持二次优化）
class 增强优化专家(Role):
    """支持多轮优化的教学设计师"""
    name: str = "优化专家"
    profile: str = "教学设计优化师"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([优化教学设计, 分析课堂报告, 最终优化设计])
        self._watch([教学优化建议, 课堂观察评估])
    
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

    async def _act(self) -> Message:
        last_msg = self.rc.memory.get()[-1]
        cause_by = last_msg.cause_by
        
        # 打印调试信息
        print(f"触发消息: {last_msg.content[:100]}...")
        if hasattr(cause_by, '__name__'):
            print(f"触发类型: {cause_by.__module__}.{cause_by.__name__}")
        else:
            print(f"触发类型: {str(cause_by)}")
        
        new_design = ""
        
        if self._is_triggered_by(教学优化建议):  # 第一轮优化
            print("执行第一轮教学设计优化")
            logger.info(f"{self._setting}: 执行第一轮教学设计优化")
            designs = self.rc.memory.get_by_action(编写教学材料)
            if not designs:
                print("错误：找不到教学材料")
                return Message(content="错误：找不到教学材料", role=self.profile)
            
            assessment_msgs = self.rc.memory.get_by_action(教学优化建议)
            if not assessment_msgs:
                print("错误：找不到教学优化建议")
                return Message(content="错误：找不到教学优化建议", role=self.profile)
            
            try:
                assessment = json.loads(assessment_msgs[0].content)
                new_design = await self.actions[0].run(
                    design=designs[0].content,
                    evaluation=assessment["assessment"],
                    advice=assessment["optimization"]
                )
            except Exception as e:
                print(f"优化失败: {str(e)}")
                new_design = f"优化失败: {str(e)}"
        
        elif self._is_triggered_by(课堂观察评估):  # 第二轮优化
            print("执行基于课堂观察的二次优化")
            logger.info(f"{self._setting}: 执行基于课堂观察的二次优化")
            observation = self.rc.memory.get_by_action(课堂观察评估)[0].content
            current_design = self.rc.memory.get_by_action(优化教学设计)[-1].content
            adviceaction= self.actions[1]
            self.set_todo(adviceaction)
            advice = await self.rc.todo.run(
                observation_report=observation,
                current_design=current_design
            )
            finalaction= self.actions[2]
            self.set_todo(finalaction)
            new_design = await self.rc.todo.run(
                design=current_design,
                evaluation=observation,
                advice=advice
            )
            
        return Message(
            content=new_design,
            role=self.profile,
            cause_by=type(self.rc.todo))

class 上课模拟器(Role):
    """上课模拟器"""
    name: str = "模拟器"
    profile: str = "上课模拟器"
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
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化时设置两个动作
        self.set_actions([上课模拟,课堂观察评估])
        self._watch([优化教学设计])
        
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 开始上课模拟")
        
        # 获取第一个动作：教学评估设计
        teach_action = self.actions[0]
        self.set_todo(teach_action)
        teach = await self.rc.todo.run(
            feed_back=self.feed_back,
            current_design=self.rc.memory.get()[-1].content
        )
        
        # 获取第二个动作：教学优化建议
        assess_action = self.actions[1]
        self.set_todo(assess_action)
        optimization = await self.rc.todo.run(
            feed_back=teach
        )
        
        # 合并结果
        full_content = optimization
        
        return Message(
            content=full_content,
            role=self.profile,
            cause_by=type(self.rc.todo)
        )
