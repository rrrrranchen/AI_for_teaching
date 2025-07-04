import re
import os
from typing import Optional

def convert_md_to_txt(md_file_path: str, remove_empty_lines: bool = True) -> Optional[str]:
    """
    将Markdown文件转换为格式良好的纯文本文件
    
    参数:
        md_file_path: 输入的Markdown文件路径
        remove_empty_lines: 是否移除多余空行(默认True)
        
    返回:
        生成的TXT文件路径，失败时返回None
        
    功能:
        1. 移除Markdown标记(标题、列表、代码块等)
        2. 保留基本段落结构
        3. 处理表格转换为文本形式
        4. 处理链接和图片描述
        5. 智能处理换行和空格
    """
    # 检查输入文件
    if not os.path.exists(md_file_path):
        print(f"错误: 文件不存在 - {md_file_path}")
        return None
    
    if not md_file_path.lower().endswith('.md'):
        print(f"警告: 文件扩展名不是.md - {md_file_path}")
    
    # 准备输出路径
    base_path = os.path.splitext(md_file_path)[0]
    txt_file_path = f"{base_path}.txt"
    
    try:
        # 读取Markdown内容
        with open(md_file_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()
        
        # 转换处理流程
        txt_content = md_content
        
        # 1. 移除标题标记
        txt_content = re.sub(r'^#+\s*', '', txt_content, flags=re.MULTILINE)
        
        # 2. 处理代码块 (保留内容，移除标记)
        txt_content = re.sub(r'```.*?\n', '', txt_content, flags=re.DOTALL)
        txt_content = re.sub(r'`([^`]+)`', r'\1', txt_content)
        
        # 3. 处理列表 (转换为简单文本行)
        txt_content = re.sub(r'^[\*\-+]\s+', '• ', txt_content, flags=re.MULTILINE)
        txt_content = re.sub(r'^\d+\.\s+', '', txt_content, flags=re.MULTILINE)
        
        # 4. 处理表格 (转换为文本形式)
        txt_content = re.sub(
            r'\|(.+?)\|[\r\n](\|?[-:]+[-|:]*)\|[\r\n]((?:\|.*?\|[\r\n])*)',
            lambda m: convert_md_table_to_text(m.group(1), m.group(3)),
            txt_content
        )
        
        # 5. 处理链接和图片 (保留描述文本)
        txt_content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', txt_content)  # 图片
        txt_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', txt_content)   # 链接
        
        # 6. 移除粗体和斜体标记
        txt_content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', txt_content)
        txt_content = re.sub(r'\*([^\*]+)\*', r'\1', txt_content)
        txt_content = re.sub(r'__([^_]+)__', r'\1', txt_content)
        txt_content = re.sub(r'_([^_]+)_', r'\1', txt_content)
        
        # 7. 处理换行和空格
        txt_content = re.sub(r'\n{3,}', '\n\n', txt_content)  # 多个空行合并为两个
        txt_content = re.sub(r'[ \t]{2,}', ' ', txt_content)  # 多个空格合并为一个
        
        # 可选: 移除所有空行
        if remove_empty_lines:
            txt_content = os.linesep.join(
                [line for line in txt_content.splitlines() if line.strip()]
            )
        
        # 写入转换结果
        with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(txt_content)
            
        return txt_file_path
    
    except UnicodeDecodeError:
        print(f"错误: 文件编码问题 - {md_file_path}")
        return None
    except IOError as e:
        print(f"IO错误: {e}")
        return None
    except Exception as e:
        print(f"转换失败: {e}")
        return None

def convert_md_table_to_text(header: str, rows: str) -> str:
    """
    辅助函数: 将Markdown表格转换为文本格式
    
    示例输入:
        header: "| Name | Age |"
        rows: "| John | 25 |\n| Alice | 30 |"
    
    返回:
        "Name: John, Age: 25\nName: Alice, Age: 30"
    """
    try:
        # 提取表头
        headers = [h.strip() for h in header.split('|') if h.strip()]
        
        # 处理每行数据
        result = []
        for row in rows.split('\n'):
            if not row.strip():
                continue
                
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) != len(headers):
                continue
                
            row_text = ', '.join(f"{h}: {c}" for h, c in zip(headers, cells))
            result.append(row_text)
        
        return '\n'.join(result)
    except Exception:
        return "[表格内容]"