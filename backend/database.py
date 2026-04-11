from peewee import SqliteDatabase
import os

# 初始化 SQLite 本地数据库，命名为 tasks.db
# Peewee ORM 会自动在这个数据库文件中建立我们的任务追踪表格
# SQLite 提供零配置、轻量级的本地存取特性跨域挂载，非常适合中小型甚至部分企业级业务线核心
db = SqliteDatabase('tasks.db')
