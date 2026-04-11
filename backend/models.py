from peewee import Model, CharField, TextField, DateField
from database import db

class Task(Model):
    """
    任务数据模型 (Peewee ORM)
    用来映射到底层 SQLite 的 tasks.db 中的 Task 表的纯粹虚拟抽象层
    支持无感知数据库底座映射流转
    """
    # 任务主标大字头 (VARCHAR)
    title = CharField()
    # 任务详细描述或系统落地方案，长文本内容不限制字符量
    description = TextField(null=True)
    # 最新进展情况反馈记录核心域，用于被生成的 Markdown 日报进行引擎级优先提取并标亮显示
    progress = TextField(null=True)
    # 当前卡点所处的业务流推进位分类阶段锁定 (To Do / In Progress / Done)
    status = CharField(default="To Do")
    # 任务紧急程度优先级识别卡 (Low / Medium / High)
    priority = CharField(default="Medium")
    # 业务敲板死线 (截止日期)
    deadline = DateField(null=True)
    # 主营项目归属分线名映射，极度重要，专为独立报告的生成大组和视图过滤筛器提供字典基准锚点
    project_name = CharField(default="Default Project")
    # 任务种类细化下延指标分类标签 (新需求 / 缺陷修复 / 优化项 等)
    task_type = CharField(default="新需求")
    # 指配人、经手人全名标记牌
    assignee = CharField(null=True)
    # 万象附件列表总索引槽（包含本地被切片后的静态相对指针路径），由于 SQLite 对 list 的残缺支持故直接在读写口走 JSON 落反序列化
    attachments = TextField(null=True)

    class Meta:
        # 指定将这一整条结构实例模型安全地绑定至刚建立的单例数据库引擎引擎室下
        database = db
