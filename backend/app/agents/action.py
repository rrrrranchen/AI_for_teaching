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
        prompt = self.PROMPT_TEMPLATE.format(teaching_content=teaching_content, objective=objective,knowledge_base=knowledge_base)
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

    async def run(self, evaluation: str, design: str,advice: str):
        prompt = self.PROMPT_TEMPLATE.format(evaluation=evaluation, design=design,advice=advice)
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

    async def run(self, evaluation: str, design: str,advice: str):
        prompt = self.PROMPT_TEMPLATE.format(evaluation=evaluation, design=design,advice=advice)
        rsp = await self._aask(prompt)
        content_text = parse_content(rsp)
        return content_text

# 新增动作类：课堂报告分析
class 分析课堂报告(Action):
    """将课堂观察转化为优化建议的行动类"""
    PROMPT_TEMPLATE:str = """
    根据课堂观察报告生成优化建议：
    {observation_report}
    
    当前教学设计版本：
    {current_design}
    
    要求：
    1. 识别3个最需改进的教学环节
    2. 针对每个问题提出具体优化方案
    3. 标注优化优先级（高/中/低）
    4. 提供可量化的改进目标
    5. 用markdown格式输出
    """
    name:str = "分析课堂报告"
    
    async def run(self, observation_report: str, current_design: str):
        prompt = self.PROMPT_TEMPLATE.format(
            observation_report=observation_report,
            current_design=current_design
        )
        rsp = await self._aask(prompt)
        return parse_content(rsp)
    
class 上课模拟(Action):
    """将课堂观察转化为优化建议的行动类"""
    PROMPT_TEMPLATE: str = """
    **角色**：课堂模拟器
    **输入**：
    - 教学设计：{current_design}
    - 学生画像：{feed_back}
    
    **模拟要求**：
    1. 生成典型学生互动场景：
    2. 记录时间节点偏差（对比教案时间分配）
    """
    name:str = "上课模拟"
    
    async def run(self, feed_back: str, current_design: str):
        prompt = self.PROMPT_TEMPLATE.format(
            feed_back=feed_back,
            current_design=current_design
        )
        rsp = await self._aask(prompt)
        return parse_content(rsp)
    
class 课堂观察评估(Action):
    """将课堂观察转化为优化建议的行动类"""
    PROMPT_TEMPLATE: str = """
    **角色**：课堂分析师
    **输入**：
    - 模拟记录：{feed_back}
    
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
        知识点重构 ：a1, 2023-10-01, 3d
        互动改进   ：a2, after a1, 2d
        评估调整   ：a3, after a2, 2d
    ```
    """
    name:str = "课堂观察评估"
    
    async def run(self, feed_back: str):
        prompt = self.PROMPT_TEMPLATE.format(
            feed_back=feed_back
        )
        rsp = await self._aask(prompt)
        return parse_content(rsp)
