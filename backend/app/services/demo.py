import random
from sparkai.llm.llm import ChatSparkLLM
from sparkai.core.messages import ChatMessage

# 定义嵌套的评估方案
class Assessment:
    def __init__(self, criteria, question_bank, assessresult=None, recommend_rate=None):
        self.criteria = criteria
        self.question_bank = question_bank
        self.assessresult = assessresult
        self.recommend_rate = recommend_rate

# 定义互动环节
class InteractionFlow:
    def __init__(self, type, description, trigger_time):
        self.type = type
        self.description = description
        self.trigger_time = trigger_time

# 定义时间计划
class TimePlan:
    def __init__(self, phase, duration, content):
        self.phase = phase
        self.duration = duration
        self.content = content

# 定义内容结构
class Content:
    def __init__(self, objectives, total_time, resources, key_point, time_plan, interaction_flows, assessment):
        self.objectives = objectives
        self.total_time = total_time
        self.resources = resources
        self.key_point = key_point
        self.time_plan = time_plan
        self.interaction_flows = interaction_flows
        self.assessment = assessment
    

def mock_ai_interface(content, num_questions=5):
    """
    模拟 AI 接口，根据 content 返回题目集合
    :param content: 教师自主输入的内容以及相关课程描述
    :param num_questions: 需要生成的题目数量，默认为5
    :return: 题目集合，包含多个题目信息
    """
    questions = []
    
    for i in range(num_questions):
        # 模拟 AI 接口返回的题目信息
        question = {
            "id": i + 1,  # 题目编号
            "type": random.choice(['choice', 'fill', 'short_answer']),  # 题目类型
            "content": f"题目内容（{i + 1}）：{content}",  # 题目内容
            "correct_answer": f"正确答案（{i + 1}）",  # 正确答案
            "difficulty": random.randint(1, 5)  # 题目难度
        }
        questions.append(question)
    
    return questions

#实现根据习题作答情况和课程描述实现教学方案设计（参数：course_description,预习题目作答情况:content，教学目标：purpose，预设互动环节：interaction，课堂时间：time)
def generate_teaching_design(course_description, content, purpose, interaction, time):
    # 构建关键点
    key_point = ["Key concept 1", "Key concept 2"]  # 示例关键点

    # 构建时间计划
    time_plan = [
        TimePlan(phase="Introduction", duration=15, content="Introduction to the topic"),
        TimePlan(phase="Main Content", duration=60, content="Detailed explanation"),
        TimePlan(phase="Conclusion", duration=15, content="Summary and Q&A")
    ]

    # 构建互动环节
    interaction_flows = [
        InteractionFlow(type="Discussion", description="Group discussion on the topic", trigger_time=30),
        InteractionFlow(type="Activity", description="Hands-on activity", trigger_time=75)
    ]

    # 构建评估方案
    assessment = Assessment(
        criteria=["Objective 1", "Objective 2"],
        question_bank=[1, 2, 3],  # 示例题目 ID
        assessresult="Good",
        recommend_rate=80
    )

    # 构建内容结构
    content = Content(
        key_point=key_point,
        time_plan=time_plan,
        interaction_flows=interaction_flows,
        assessment=assessment
    )

    # 生成总结果汇总
    total_result = (
        f"Course Description: {course_description}\n"
        f"Objectives: {', '.join(purpose)}\n"
        f"Key Points: {', '.join(content.key_point)}\n"
        f"Total Time: {time} minutes\n"
        f"Time Plan: {', '.join([f'{tp.phase} ({tp.duration} mins)' for tp in content.time_plan])}\n"
        f"Interaction Flows: {', '.join([f'{ifl.type} ({ifl.description})' for ifl in content.interaction_flows])}\n"
        f"Assessment: {', '.join(content.assessment.criteria)}\n"
        f"Assessment Result: {content.assessment.assessresult}\n"
        f"Recommend Rate: {content.assessment.recommend_rate}%"
    )

    # 返回教学方案设计
    return {
       
        "content": {
            "key_point": content.key_point,   #关键知识点
            "time_plan": [
                {"phase": tp.phase, "duration": tp.duration, "content": tp.content} for tp in content.time_plan
            ],
            "interaction_flows": [
                {"type": ifl.type, "description": ifl.description, "trigger_time": ifl.trigger_time} for ifl in content.interaction_flows
            ],
            "assessment": {
                "criteria": content.assessment.criteria,    #评估标准（主要用于给教师展示这套方案为什么合理等）
                "assessresult": content.assessment.assessresult,      #评估结果
                "recommend_rate": content.assessment.recommend_rate     #推荐指数
            }
        },
        
    }

#实现将mongodb所暂存的数据整合成具有设定格式的word文档中并返回（如果有这个接口的话，没有的话后端可以用python-docx库)


#实现根据教师描述以及教案设计实现课后复习习题功能（参数：teacher_descripiton,teachingplan）

#ppt，word文档，图片，视频等资源生成可以存储在后端文件夹中，调用函数后将资源存储并返回相对的url即可