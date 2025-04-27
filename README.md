这是教备通:AI 辅助教学交互系统

后端 python3.9 以上
下载 requirements.txt 里的以来即可

前端部署参考/frontend/README.md

数据库使用 mysql，需要先新建一个空数据库，修改 config.py 里的数据库配置，然后运行后端即可生成所有表。

数据库迁移使用 alembic，需要先创建 alembic.ini 文件，然后执行以下命令：
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
