# 项目数据模型结构说明

## 目录结构

```
/backend/app/
    ├── models/                # 数据模型目录
    │   ├── __init__.py        # 模型包初始化文件
    │   ├── user.py            # 用户数据模型
    │   ├── question.py        # 题目数据模型
    │   └── relationship.py   # 多对多关系中间表
    └── 
```

## 模型规范

1. **单一文件原则**
   每个Python文件(`.py`)只包含一个数据模型类，文件名应与模型名称保持一致

2. **关系中间表**
   所有多对多(many-to-many)关系的中间表统一存放在 `/backend/app/relationship.py` 文件中