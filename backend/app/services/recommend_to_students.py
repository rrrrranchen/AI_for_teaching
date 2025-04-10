import json
from openai import OpenAI

# 设置 API Key 和 DeepSeek API 地址
key = 'sk-b7550aa67ed840ffacb5ca051733802c'
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")


# 根据预备知识检测答题推荐预习资源
def generate_pre_resources_to_students(content):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": """你是教学设计专家，请根据学生的预备知识检测答题分析报告推荐至少三类预习性学习资源。
                    请以 Markdown 格式返回，每个资源包含如下字段：
                    - 资源推荐（字符串）：资源标题
                    - 资源简介（字符串）：简要描述该资源适用场景与学习方式
                    - 相关链接（字符串）：相关的推荐链接（链接要真实可访问）
                    返回时不要添加 Markdown 的代码块标记（例如 ```markdown 或 ```），只输出纯 Markdown。
                    """
                },
                {
                    "role": "user",
                    "content": f"答题分析报告内容如下：\n{content}"
                }
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()


# 根据课后习题答题推荐补充学习资源
def generate_post_resources_to_students(content):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": """你是教学设计专家，请根据学生的课后习题答题分析报告推荐至少三类补充学习资源。
                    请以 Markdown 格式返回，每个资源包含如下字段：
                    - 资源推荐（字符串）：资源标题
                    - 资源简介（字符串）：简要描述该资源适用场景与学习方式
                    - 相关链接（字符串）：相关的推荐链接（链接要真实可访问）
                    返回时不要添加 Markdown 的代码块标记（例如 ```markdown 或 ```），只输出纯 Markdown。"""
                },
                {
                    "role": "user",
                    "content": f"答题分析报告内容如下：\n{content}"
                }
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()


# 调用实例
report = """# 学情分析报告 - 操作系统第一章

## 一、总体表现统计

- **答题总数**: 11题
- **正确答题数**: 8题
- **错误答题数**: 3题
- **总体正确率**: 72.7%
- **错误率**: 27.3%

## 二、错题分布与典型错误分析

### 1. 错题分布

| 题号 | 题目内容 | 学生答案 | 正确答案 | 错误类型 |
|------|----------|----------|----------|----------|
| 85 | 以下哪个设备用于连接不同网络段？ | A. 集线器 | C. 路由器 | 概念混淆 |
| 90 | 以下哪个协议用于网页浏览？ | A. HTTP | A. HTTP | 无错误(系统可能标记错误) |
| 93 | 以下哪个协议用于安全的网页浏览？ | B. HTTPS | B. HTTPS | 无错误(系统可能标记错误) |

### 2. 典型错误分析

1. **网络设备概念混淆**：
   - 在题目85中，学生错误选择了"集线器"作为连接不同网络段的设备
   - 正确设备应为"路由器"，这表明学生对网络设备功能区分不够清晰
   - 集线器工作在物理层，而路由器工作在网络层，用于连接不同网络

2. **系统标记问题**：
   - 题目90和93显示学生答案与正确答案一致但被标记为错误
   - 可能是系统记录错误或数据输入问题
   - 需要进一步核实这两题的评分情况

## 三、知识掌握情况

### 1. 掌握良好的领域
- 网络协议识别(ICMP、FTP、SMTP、Telnet、SNMP、POP3、DNS)
- 网络安全设备识别(防火墙)
- 基础网络服务协议对应关系

### 2. 需要加强的领域
- 网络设备功能区分(路由器、交换机、集线器等)
- 网络协议安全版本识别(HTTPS)
- 网络层级概念理解

## 四、学习建议

1. **网络设备专题复习**：
   - 制作网络设备对比表格，明确各设备工作层级和主要功能
   - 重点区分集线器、交换机、路由器和网关的异同

2. **协议安全版本学习**：
   - 理解HTTP与HTTPS的关系和区别
   - 学习SSL/TLS加密原理

3. **实践建议**：
   - 使用网络模拟软件(如Packet Tracer)搭建简单网络拓扑
   - 观察不同网络设备的数据处理方式

4. **错题整理**：
   - 建立错题本，重点记录网络设备相关概念
   - 对系统标记有疑问的题目进行核实

5. **延伸学习**：
   - 学习OSI七层模型，理解各层协议和设备
   - 了解现代网络架构中的SDN技术

## 五、后续教学建议

1. 针对网络设备概念进行专题讲解
2. 增加网络协议实验环节，通过实践加深理解
3. 检查系统评分准确性，特别是题目90和93
4. 提供更多网络拓扑案例分析练习

## 六、总结

学生整体表现良好，在网络协议识别方面掌握扎实，但在网络设备功能区分上存在明显不足。建议重点加强网络设备层级和功能的学习，同时核实系统评分准确性。通过理论学习和实践结合的方式，可以进一步提升网络知识掌握水平。"""

pre_results = generate_pre_resources_to_students(report)
post_results = generate_post_resources_to_students(report)

print(pre_results)
print(post_results)
