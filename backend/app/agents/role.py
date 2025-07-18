
import asyncio
import datetime
import json
import random
import re
import fire
from typing import Dict, Any
from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team

from action import 上课模拟, 优化教学设计, 分析课堂报告, 教学优化建议, 教学流程执行, 教学评估设计, 最终优化设计,   编写教学材料, 设计课程大纲, 课堂互动,  课堂观察评估



class 课程设计师(Role):
    """课程设计师角色，负责设计课程大纲"""
    name: str = "李老师"
    profile: str = "课程设计师"
    
    def __init__(self, objective: str, teaching_content: str, knowledge_base: str, **kwargs):
        super().__init__(**kwargs)
        self.objective = objective
        self.teaching_content = teaching_content
        self.knowledge_base = knowledge_base
        self._watch([UserRequirement])
        self.set_actions([设计课程大纲])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        outline = await todo.run(
            teaching_content=self.teaching_content,
            objective=self.objective,
            knowledge_base=self.knowledge_base
        )
        
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
            outline = data["outline"]
            
            # 执行Action
            materials = await self.rc.todo.run(outline=outline)
            
            return Message(
                content=materials,
                role=self.profile,
                cause_by=type(self.rc.todo)
            )
            
        except Exception as e:
            logger.error(f"材料编写失败: {str(e)}")
            return Message(
                content=f"材料编写失败: {str(e)}",
                role=self.profile,
                cause_by=type(self.rc.todo)
            )

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
        materials = self.rc.memory.get_by_action(编写教学材料)[0].content
        assessment = await self.rc.todo.run(materials=materials)
        
        # 获取第二个动作：教学优化建议
        optimization_action = self.actions[1]
        self.set_todo(optimization_action)
        optimization = await self.rc.todo.run(assessment=assessment)
        
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

class 增强优化专家(Role):
    """支持多轮优化的教学设计师"""
    name: str = "优化专家"
    profile: str = "教学设计优化师"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([优化教学设计, 最终优化设计])
        self._watch([教学优化建议, 课堂观察评估])
    
    def _is_triggered_by(self, action_class) -> bool:
        """检查是否由特定动作类触发"""
        if not self.rc.memory:
            return False
            
        last_msg = self.rc.memory.get()[-1]
        cause_by = last_msg.cause_by
        
        if hasattr(cause_by, '__name__'):
            return cause_by.__name__ == action_class.__name__
        return False

    async def _act(self) -> Message:
        if not self.rc.memory:
            return Message(content="无历史消息", role=self.profile)
            
        last_msg = self.rc.memory.get()[-1]
        new_design = ""
        
        if self._is_triggered_by(教学优化建议):  # 第一轮优化
            logger.info(f"{self._setting}: 执行第一轮教学设计优化")
            
            # 获取教学材料
            materials = self.rc.memory.get_by_action(编写教学材料)
            if not materials:
                return Message(content="错误：找不到教学材料", role=self.profile)
            
            # 获取评估建议
            assessment_msgs = self.rc.memory.get_by_action(教学优化建议)
            if not assessment_msgs:
                return Message(content="错误：找不到教学优化建议", role=self.profile)
            
            try:
                assessment_data = json.loads(assessment_msgs[0].content)
                new_design = await self.actions[0].run(
                    design=materials[0].content,
                    evaluation=assessment_data["assessment"],
                    advice=assessment_data["optimization"]
                )
            except Exception as e:
                new_design = f"优化失败: {str(e)}"
        
        elif self._is_triggered_by(课堂观察评估):  # 第二轮优化
            logger.info(f"{self._setting}: 执行基于课堂观察的二次优化")
            
            # 获取课堂观察报告
            observation = self.rc.memory.get_by_action(课堂观察评估)
            if not observation:
                return Message(content="错误：找不到课堂观察报告", role=self.profile)
            
            # 获取当前教学设计
            current_design = self.rc.memory.get_by_action(优化教学设计)
            if not current_design:
                return Message(content="错误：找不到当前教学设计", role=self.profile)
            
            # 执行最终优化
            new_design = await self.actions[1].run(
                design=current_design[-1].content,
                evaluation=observation[0].content,
                advice="基于课堂观察的优化建议"
            )
        else:
            new_design = "未触发优化条件"
            
        return Message(
            content=new_design,
            role=self.profile,
            cause_by=type(self.rc.todo))

class 学生画像构建器(Role):
    """根据学生作答记录构建学生画像"""
    name: str = "画像构建器"
    profile: str = "学生画像分析师"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([学生画像构建器])
        self._watch([优化教学设计])
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 构建学生画像")
        todo = self.rc.todo
        
        try:
            # 从环境上下文中获取学生反馈
            feed_back = self.rc.env.context.get("student_feedback", "")
            
            # 构建学生画像
            profiles = await todo.run(feed_back=feed_back)
            
            # 解析为JSON对象
            student_profiles = json.loads(profiles)
            
            # 返回学生画像
            return Message(
                content=json.dumps({"student_profiles": student_profiles}),
                role=self.profile,
                cause_by=type(todo)
            )
        except Exception as e:
            logger.error(f"构建学生画像失败: {str(e)}")
            return Message(
                content=f"构建学生画像失败: {str(e)}",
                role=self.profile,
                cause_by=type(todo))

class 学生智能体(Role):
    """代表单个学生的智能体（增强版）"""
    def __init__(self, profile: str, student_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.profile = profile
        self.student_id = student_data["student_id"]
        
        # 初始化学生状态
        self.student_profile = {
            "student_id": self.student_id,
            "strengths": student_data.get("strengths", []),
            "weaknesses": student_data.get("weaknesses", []),
            "learning_style": student_data.get("learning_style", "通用型"),
            "error_patterns": student_data.get("error_patterns", []),
            "learning_state": "准备学习",
            "engagement": 0,  # 参与度分数
            "last_understanding": 3  # 最近理解程度
        }
        
        self.set_actions([课堂互动])
        self._watch([教学流程执行])
        
    def _is_directly_questioned(self, activity_plan: dict) -> bool:
        """检查是否被教师直接点名提问"""
        if not activity_plan:
            return False
            
        # 检查是否是目标学生
        if self.student_id in activity_plan.get("target_students", []):
            return True
            
        # 检查是否有具体问题指向
        if activity_plan.get("question") and self.student_id in activity_plan["question"]:
            return True
            
        return False
    
    async def _act(self) -> Message:
        todo = self.rc.todo
        last_msg = self.rc.memory.get()[-1] if self.rc.memory else None
        
        # 检查是否有教学活动计划
        if last_msg and last_msg.cause_by == 教学流程执行:
            activity_plan = last_msg.instruct_content
            
            # 直接提问检测
            if self._is_directly_questioned(activity_plan):
                # 执行课堂互动
                response = await todo.run(
                    activity=activity_plan["activity"],
                    context=activity_plan["context"],
                    student_profile=self.student_profile,
                    question=activity_plan.get("question", "")
                )
                
                # 更新理解状态
                self.student_profile["last_understanding"] = response.get("understanding", 3)
                
                # 创建结构化消息
                msg_content = json.dumps({
                    "student_id": self.student_id,
                    "activity": activity_plan["activity"],
                    "response": response,
                    "profile_snapshot": self.student_profile.copy()
                })
                
                return Message(
                    content=msg_content,
                    role=self.profile,
                    cause_by=type(todo)
                )
            
            # 主动参与机会检测
            if self._should_participate_actively(activity_plan):
                # 生成主动参与响应
                response = await todo.run(
                    activity=activity_plan["activity"],
                    context=activity_plan["context"],
                    student_profile=self.student_profile
                )
                
                # 更新参与度
                self.student_profile["engagement"] += 1
                
                return Message(
                    content=json.dumps({
                        "student_id": self.student_id,
                        "activity": "主动参与",
                        "response": response
                    }),
                    role=self.profile,
                    cause_by=type(todo)
                )
        
        return Message(content="", role=self.profile, cause_by=type(todo))
    
    def _should_participate_actively(self, activity_plan: dict) -> bool:
        """决定是否主动参与"""
        # 检查是否涉及强项知识
        context = activity_plan.get("context", "")
        for strength in self.student_profile["strengths"]:
            if strength in context:
                return True
                
        # 检查学习风格
        if self.student_profile["learning_style"] in ["主动型", "社交型"]:
            return random.random() > 0.7  # 70%概率参与
        
        # 检查参与度指标
        if self.student_profile["engagement"] < 2:  # 参与度低时更可能参与
            return True
            
        return False

class 课堂模拟教师(Role):
    """主持课堂模拟的教师角色（增强版）"""
    name: str = "模拟教师"
    profile: str = "课堂主持人"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([教学流程执行])
        self._watch([学生画像构建器])
        self.interaction_log = []
        self.student_profiles = []
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 开始课堂模拟")
        todo = self.rc.todo
        
        try:
            # 获取教学设计和学生画像
            design_msg = self.rc.memory.get_by_action(优化教学设计)
            if not design_msg:
                return Message(content="错误：找不到教学设计", role=self.profile)
            
            design = design_msg[-1].content
            
            # 获取学生画像
            profiles_msg = self.rc.memory.get_by_action(学生画像构建器)
            if not profiles_msg:
                return Message(content="错误：找不到学生画像", role=self.profile)
            
            profiles_data = json.loads(profiles_msg[-1].content)
            self.student_profiles = profiles_data["student_profiles"]
            
            # 执行教学流程计划
            activity_plan = await todo.run(
                design=design,
                student_profiles=self.student_profiles
            )
            
            # 保存计划作为指令内容
            activity_plan_msg = Message(
                content=json.dumps(activity_plan),
                role=self.profile,
                cause_by=type(todo),
                instruct_content=activity_plan
            )
            
            # 收集学生响应（等待1秒模拟响应时间）
            await asyncio.sleep(1)
            
            # 分析响应并生成报告
            report = self._generate_report(activity_plan)
            
            return Message(
                content=report,
                role=self.profile,
                cause_by=type(todo))
        except Exception as e:
            logger.error(f"课堂模拟失败: {str(e)}")
            return Message(
                content=f"课堂模拟失败: {str(e)}",
                role=self.profile,
                cause_by=type(todo))
    
    def _generate_report(self, activity_plan: dict) -> str:
        """生成课堂活动报告"""
        # 收集所有学生响应
        student_responses = []
        for msg in self.rc.memory.get():
            if msg.role.startswith("学生"):
                try:
                    response_data = json.loads(msg.content)
                    student_responses.append(response_data)
                except:
                    pass
        
        # 分析理解程度
        understanding_scores = []
        for r in student_responses:
            if "response" in r and isinstance(r["response"], dict):
                understanding_scores.append(r["response"].get("understanding", 3))
        
        avg_understanding = sum(understanding_scores) / len(understanding_scores) if understanding_scores else 0
        
        # 生成报告
        report = f"""# 课堂活动报告: {activity_plan['activity']}
**时间**: {activity_plan['start_time']}-{activity_plan['start_time']+activity_plan['duration']}分钟
**目标学生**: {", ".join(activity_plan.get('target_students', []))}
**目的**: {activity_plan.get('purpose', '')}

## 学生参与情况
- 平均理解程度: {avg_understanding:.1f}/5
- 收到响应: {len(student_responses)}份
- 参与学生: {", ".join(set(r['student_id'] for r in student_responses))}

## 代表性回答
{self._sample_responses(student_responses)}

## 教学建议
{self._generate_suggestions(activity_plan, avg_understanding)}
"""
        return report
    
    def _sample_responses(self, responses: list) -> str:
        """提取代表性回答"""
        if not responses:
            return "无学生响应"
        
        samples = []
        for r in responses[:3]:  # 取前3个样本
            student_id = r.get("student_id", "未知学生")
            response_text = r.get("response", {}).get("response", "无文本响应") if isinstance(r.get("response"), dict) else "无有效响应"
            samples.append(f"- {student_id}: {response_text[:100]}{'...' if len(response_text)>100 else ''}")
        
        return "\n".join(samples)
    
    def _generate_suggestions(self, activity_plan: dict, understanding: float) -> str:
        """生成教学建议"""
        if understanding < 2.5:
            return ("学生对当前内容理解不足，建议：\n"
                    "1. 提供更多示例演示\n"
                    "2. 分解复杂概念\n"
                    "3. 检查前置知识掌握情况")
        
        if "弱项" in activity_plan.get("purpose", "") and understanding < 3.5:
            return ("针对弱项的教学效果一般，建议：\n"
                    "1. 使用更多视觉辅助工具\n"
                    "2. 提供分步指导\n"
                    "3. 同伴辅导")
        
        return "教学效果良好，可按计划继续推进"

class 课堂分析师(Role):
    """分析课堂模拟报告并生成优化建议"""
    name: str = "分析师"
    profile: str = "课堂分析师"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([课堂观察评估])
        self._watch([教学流程执行])
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 分析课堂报告")
        todo = self.rc.todo
        
        # 获取课堂模拟报告
        report_msgs = self.rc.memory.get_by_action(教学流程执行)
        if not report_msgs:
            return Message(content="错误：找不到课堂报告", role=self.profile)
        
        # 获取学生响应摘要
        responses = []
        for msg in self.rc.memory.get():
            if msg.role.startswith("学生"):
                responses.append(msg.content[:100] + "...")
        
        responses_summary = "\n".join(responses[:3])  # 取前3个响应
        
        # 分析报告
        assessment = await todo.run(
            activity_report=report_msgs[-1].content,
            responses_summary=responses_summary
        )
        
        return Message(
            content=assessment,
            role=self.profile,
            cause_by=type(todo))

