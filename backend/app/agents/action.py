import json
import re
import fire
from typing import Dict, Any, List

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team

def parse_content(rsp):
    """从markdown格式中解析出内容"""
    pattern = r"```markdown(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    content_text = match.group(1) if match else rsp
    return content_text


class 设计课程大纲(Action):
    """生成课程大纲的行动类"""
    PROMPT_TEMPLATE: str = """
    **角色**：课程设计师
    **输入**：
    - 教学目标：{objective}
    - 核心内容：{teaching_content}
    - 知识库资料：{knowledge_base}（权威教学标准/文献）
    
    **输出要求**：
    1. 教学目标（3-5条可量化目标，标注知识库来源）
    2. 知识图谱（Mermaid结构图，标注节点关系依据）
    3. 课时分配（45分钟模块化设计）
    ```markdown
    # [课程名称]
    ## 1. 教学目标
    ## 2. 知识结构
    ```mermaid
    graph TD
      A[核心概念] -->|依据知识库| B[原理]
    ```
    ## 3. 重难点
    ## 4. 课时安排
    """
    
    name: str = "设计课程大纲"

    async def run(self, teaching_content: str, objective: str, knowledge_base: str):
        prompt = self.PROMPT_TEMPLATE.format(teaching_content=teaching_content, objective=objective, knowledge_base=knowledge_base)
        rsp = await self._aask(prompt)
        content_text = parse_content(rsp)
        return content_text

class 编写教学材料(Action):
    """编写具体教学材料的行动类"""
    PROMPT_TEMPLATE: str = """
    **角色**：教学设计师
    **输入**：
    - 大纲：{outline}
    
    **输出要求**：
    1. 互动环节必须包含：
       - 知识库推荐活动（标注来源）
       - 针对薄弱点的定制练习
    2. 教学流程图：
    ```mermaid
    journey
        section 导入： 知识库启发策略
        section 讲授： 知识库补充资料
        section 互动： 小组讨论/角色扮演
        section 小结： 形成性评估
    ```
    3. 双轨作业设计（基础题/拓展题标注知识库出处）
    """
    name: str = "编写教学材料"

    async def run(self, outline: str):
        prompt = self.PROMPT_TEMPLATE.format(outline=outline)
        rsp = await self._aask(prompt)
        content_text = parse_content(rsp)
        return content_text

class 教学评估设计(Action):
    """设计教学评估方案的行动类"""
    PROMPT_TEMPLATE: str = """
    **角色**：评估专家
    **输入**：
    - 教学材料：{materials}
    
    **输出要求**：
    1. 三维评估矩阵：
    | 维度       | 评估工具          | 知识库依据       |
    |------------|-------------------|------------------|
    | 知识掌握   | 概念图诊断        | [来源]           |
    | 能力应用   | 情境任务          | [来源]           |
    | 学习态度   | 观察量表          | [来源]           |
    
    2. 量化评分细则（标注难度系数来源）
    """
    name: str = "教学评估设计"

    async def run(self, materials: str):
        prompt = self.PROMPT_TEMPLATE.format(materials=materials)
        rsp = await self._aask(prompt)
        content_text = parse_content(rsp)
        return content_text

class 教学优化建议(Action):
    """根据评估结果生成优化建议的行动类"""
    PROMPT_TEMPLATE: str = """
    根据以下评估方案生成具体的教学优化建议：
    {assessment}
    
    要求：
    1. 针对评估发现的每个问题提供改进方案
    2. 建议具体可操作的教学策略调整
    3. 推荐补充教学资源
    4. 提供教师专业发展建议
    
    请用中文回复，并使用```markdown 你的内容 ```格式：
    """
    name: str = "教学优化建议"

    async def run(self, assessment: str):
        prompt = self.PROMPT_TEMPLATE.format(assessment=assessment)
        rsp = await self._aask(prompt)
        return parse_content(rsp)

class 优化教学设计(Action):
    """根据评估建议优化教学设计的行动类"""
    PROMPT_TEMPLATE: str = """
    **角色**：教学设计师

    **输入**：
    - 原设计：{design}
    - 评估报告：{evaluation}
    - 优化建议：{advice}
    
    **重点**：
    - 根据优化建议和评估报告对原设计进行修正
    - 教学设计需要符合教师上课的实训性要求
    - 课堂总时间为90分钟
    
    **输出要求**：
    - 给定mermaid图加以展示流程
    - 只需要输出优化后的完整教学设计，不需要输出除了教学设计以外的任何其他内容，优化后的教学设计需要在3000字以上
    - 请用中文回复，并使用```markdown 你的内容 ```格式：
    """
    name: str = "优化教学设计"

    async def run(self, evaluation: str, design: str, advice: str):
        prompt = self.PROMPT_TEMPLATE.format(evaluation=evaluation, design=design, advice=advice)
        rsp = await self._aask(prompt)
        content_text = parse_content(rsp)
        return content_text

class 最终优化设计(Action):
    """根据评估建议优化教学设计的行动类"""
    PROMPT_TEMPLATE: str = """
    **角色**：教学设计师

    **输入**：
    - 原设计：{design}
    - 评估报告：{evaluation}
    - 优化建议：{advice}
    
    **重点**：
    - 根据优化建议和评估报告对原设计进行修正
    - 教学设计需要符合教师上课的实训性要求
    - 课堂总时间为90分钟
    
    **输出要求**：
    - 给定mermaid图加以展示流程
    - 只需要输出优化后的完整教学设计，不需要输出除了教学设计以外的任何其他内容，优化后的教学设计需要在3000字以上
    - 请用中文回复，并使用```markdown 你的内容 ```格式：
    """
    name: str = "最终优化设计"

    async def run(self, evaluation: str, design: str, advice: str):
        prompt = self.PROMPT_TEMPLATE.format(evaluation=evaluation, design=design, advice=advice)
        rsp = await self._aask(prompt)
        content_text = parse_content(rsp)
        return content_text

class 学生画像构建器(Action):
    """根据学生作答记录构建学生画像"""
    PROMPT_TEMPLATE: str = """
    根据学生作答记录构建学生画像：
    {feed_back}
    
    要求：
    1. 分析每个学生的知识掌握情况（强项/弱项）
    2. 识别常见错误模式
    3. 预测潜在学习障碍
    4. 生成学生画像JSON格式
    
    输出格式：
    [
      {{
        "student_id": "S001",
        "strengths": ["TCP原理", "三次握手"],
        "weaknesses": ["拥塞控制", "滑动窗口"],
        "learning_style": "视觉型",
        "error_patterns": ["混淆TCP/UDP应用场景"],
        "intervention_needed": true
      }},
      ...
    ]
    """
    name: str = "学生画像构建器"

    async def run(self, feed_back: str):
        prompt = self.PROMPT_TEMPLATE.format(feed_back=feed_back)
        rsp = await self._aask(prompt)
        return parse_content(rsp)

class 课堂互动(Action):
    """学生智能体的课堂互动行为（增强版）"""
    PROMPT_TEMPLATE: str = """
    **角色**：学生{student_id}
    **学习风格**：{learning_style}学习者
    **知识掌握**：
    - 强项：{strengths}
    - 弱项：{weaknesses}
    **当前学习状态**：{learning_state}
    
    **教学场景**：{context}
    **教师活动**：{activity}
    {question_section}
    
    **请以学生身份完成以下任务**：
    1. 根据你的知识掌握情况和学习风格回应
    2. 如果问题涉及弱项，可请求进一步解释
    3. 评估对当前内容的理解程度（1-5分）
    4. 提出与当前主题相关的深入问题
    5. 更新学习状态描述
    
    **输出格式**：
    {{
        "response": "你的回答内容",
        "question": "提出的问题（可选）",
        "understanding": 3, // 理解程度评分
        "new_state": "更新后的学习状态描述"
    }}
    """
    name: str = "课堂互动"

    async def run(self, activity: str, context: str, student_profile: dict, question: str = None):
        # 从学生画像中提取状态，如果没有则初始化
        learning_state = student_profile.get("learning_state", "专注听讲")
        
        # 添加问题部分（如果有）
        question_section = f"**教师提问**：{question}" if question else ""
        
        prompt = self.PROMPT_TEMPLATE.format(
            student_id=student_profile["student_id"],
            learning_style=student_profile["learning_style"],
            strengths=", ".join(student_profile["strengths"]),
            weaknesses=", ".join(student_profile["weaknesses"]),
            learning_state=learning_state,
            context=context,
            activity=activity,
            question_section=question_section
        )
        
        rsp = await self._aask(prompt)
        
        try:
            # 解析结构化响应
            response_data = json.loads(rsp)
            
            # 更新学习状态
            student_profile["learning_state"] = response_data.get("new_state", learning_state)
            student_profile["last_understanding"] = response_data.get("understanding", 3)
            
            return response_data
        except json.JSONDecodeError:
            logger.warning(f"学生响应解析失败: {rsp}")
            return {
                "response": rsp,
                "question": "",
                "understanding": 3,
                "new_state": learning_state
            }

class 教学流程执行(Action):
    """执行课堂教学流程并与学生互动（增强版）"""
    PROMPT_TEMPLATE: str = """
    **角色**：课堂主持人
    **教学设计**：{design}
    
    **当前课堂进度**：{current_progress}
    **剩余时间**：{remaining_time}分钟
    **学生状态摘要**：
    {student_profiles_summary}
    
    **下一步教学决策**：
    1. 选择教学环节：{available_activities}
    2. 设计互动策略（提问/小组讨论/练习等）
    3. 选择目标学生（基于画像优化学习体验）
    4. 预估活动时长（5-15分钟）
    
    **输出要求**：
    {{
        "activity": "活动描述",
        "target_students": ["S001", "S002"], // 针对的学生ID
        "duration": 5, // 预计分钟
        "purpose": "活动目的",
        "context": "场景说明",
        "question": "具体问题（可选）"
    }}
    """
    name: str = "教学流程执行"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_elapsed = 0
        self.total_time = 90  # 90分钟课堂
        self.current_activity = None

    async def run(self, design: str, student_profiles: List[Dict]):
        # 创建学生画像摘要
        profiles_summary = "\n".join([
            f"- {p['student_id']}: {p['learning_style']}学习者 | "
            f"状态: {p.get('learning_state', '未知')} | "
            f"理解度: {p.get('last_understanding', 'N/A')}"
            for p in student_profiles
        ])
        
        # 可用教学活动
        activities = [
            "概念讲解", "示例演示", "小组讨论", 
            "实践练习", "问答互动", "知识点总结",
            "案例分析", "快速测验"
        ]
        
        prompt = self.PROMPT_TEMPLATE.format(
            design=design,
            student_profiles_summary=profiles_summary,
            current_progress=f"{self.time_elapsed}/{self.total_time}分钟",
            remaining_time=self.total_time - self.time_elapsed,
            available_activities=", ".join(activities)
        )
        
        rsp = await self._aask(prompt)
        
        try:
            activity_plan = json.loads(rsp)
            activity_plan["start_time"] = self.time_elapsed
            self.current_activity = activity_plan["activity"]
            
            # 更新已用时间
            self.time_elapsed += activity_plan.get("duration", 5)
            if self.time_elapsed > self.total_time:
                self.time_elapsed = self.total_time
                
            return activity_plan
        except json.JSONDecodeError:
            logger.error("教学活动计划解析失败，使用默认计划")
            return {
                "activity": "问答互动",
                "target_students": [p["student_id"] for p in student_profiles[:2]],
                "duration": 5,
                "purpose": "检查理解程度",
                "context": "教师提问环节"
            }

class 课堂观察评估(Action):
    """分析课堂模拟报告并生成优化建议"""
    PROMPT_TEMPLATE: str = """
    **角色**：课堂分析师
    **输入**：
    - 课堂活动报告：{activity_report}
    - 学生响应摘要：{responses_summary}
    
    **输出要求**：
    1. 关键问题TOP3（按优先级排序）：
    | 问题类型 | 具体表现       | 知识库改进方案       |
    |----------|----------------|----------------------|
    | 概念理解 | 70%混淆拥塞控制| [来源]可视化策略    |
    | ...      | ...            | ...                  |
    
    2. 生成优化路线图：
    ```mermaid
    gantt
        title 教学优化计划
        知识点重构 ：a1, after a0, 3d
        互动改进   ：a2, after a1, 2d
        评估调整   ：a3, after a2, 2d
    ```
    
    3. 具体优化建议（针对当前教学设计）
    """
    name: str = "课堂观察评估"
    
    async def run(self, activity_report: str, responses_summary: str):
        prompt = self.PROMPT_TEMPLATE.format(
            activity_report=activity_report,
            responses_summary=responses_summary
        )
        rsp = await self._aask(prompt)
        return parse_content(rsp)