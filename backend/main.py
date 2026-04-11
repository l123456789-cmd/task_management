from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from database import db
from models import Task
import shutil
import os
import json
import uuid
import time

# 初始化 FastAPI 高性能异步应用接管系统总台挂点拦截器
app = FastAPI()

# 配发全局跨网段允许域访问源头配置 (CORS 防阻隔屏蔽中间件门阀)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保拥有本地环境安全路径下的专门保存大件素材附件源流块存放柜文件夹
os.makedirs("uploads", exist_ok=True)
# 运用 Mount 接驳子集分流法：任何找 `/uploads` 段域的访问都会被拦截并交去本地库寻索文件直吐物理文件流
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 从主站发起应用级别链接去强制握手沟通 SQLite 本地基础库资源中心
db.connect()
db.create_tables([Task], safe=True)

# ================================
# 数据传输洗白与安检过滤拦截盾 (Pydantic 类型重塑防护类结构)
# 将入域的数据做严格属性清洗脱水校验、反向剔除脏 JSON 无效段等动作
# ================================

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    progress: Optional[str] = ""
    status: Optional[str] = "To Do"
    priority: Optional[str] = "Medium"
    deadline: Optional[date] = None
    project_name: Optional[str] = "Default Project"
    task_type: Optional[str] = "新需求"
    assignee: Optional[str] = None
    attachments: Optional[List[str]] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    progress: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[date] = None
    project_name: Optional[str] = None
    task_type: Optional[str] = None
    assignee: Optional[str] = None
    attachments: Optional[List[str]] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    progress: Optional[str]
    status: str
    priority: str
    deadline: Optional[date]
    project_name: str
    task_type: str
    assignee: Optional[str]
    attachments: List[str]

# ================================
# 拦截封装过滤挂钩（ORM 转译）
# ================================
def format_task(t):
    """把原生态 Peewee ORM 模型进行标准对象强转封包，着重平滑掉那个非常麻烦的反序列化 JSON list 问题"""
    atts = []
    if t.attachments:
        try:
            # 还原被转化并硬化固化的持久型 JSON 树结构给接口传给 vue
            atts = json.loads(t.attachments)
        except Exception:
            atts = []
    return {
        "id": t.id, "title": t.title, "description": t.description, "progress": t.progress, "status": t.status, 
        "priority": t.priority, "deadline": t.deadline, "project_name": t.project_name, 
        "task_type": t.task_type, "assignee": t.assignee, "attachments": atts
    }

# ================================
# 标准多项全链操作管控节点路由 (CRUD API)
# ================================

@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks():
    """获取库内全量底座视图任务版图集合流发给前台组建响应墙"""
    return [format_task(t) for t in Task.select()]

@app.post("/api/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate):
    """建构新生命期对象：附件如果出现直接拦截降维强制拉平成 Text 型存封进数据库单字段"""
    data = task.model_dump()
    if data.get("attachments") is not None:
        data["attachments"] = json.dumps(data["attachments"])
    t = Task.create(**data)
    return format_task(t)

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate):
    """更新脏快照任务点：极其复杂的附件废弃跟踪捕杀级清理系统挂接到本引擎底层了"""
    t = Task.get_by_id(task_id)
    update_data = task.model_dump(exclude_unset=True)
    
    # [核心技术点] 这个钩子主要为了做被遗弃野图的清除
    if "attachments" in update_data:
        old_atts = []
        if t.attachments:
            try:
                old_atts = json.loads(t.attachments)
            except Exception:
                pass
        
        new_atts = update_data["attachments"]
        if new_atts is not None:
            # 抽出差值：原先就有的图但在传来新的接口请求中失踪了的，这就是被砍掉废弃准备进行服务器物理消除的目标
            removed_atts = [url for url in old_atts if url not in new_atts]
            for url in removed_atts:
                filename = url.split("/")[-1]
                if filename:
                    file_path = os.path.join("uploads", filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
        update_data["attachments"] = json.dumps(new_atts)
        
    for k, v in update_data.items():
        setattr(t, k, v)
    t.save()
    return format_task(t)

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    """连根拔起并断除关系树钩子指令：除抹除自身模型主键还要联动抹杀它存的所有老图物理介质实体"""
    t = Task.get_by_id(task_id)
    if t.attachments:
        try:
            atts = json.loads(t.attachments)
            for url in atts:
                filename = url.split("/")[-1]
                if filename:
                    file_path = os.path.join("uploads", filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
        except Exception:
            pass
    t.delete_instance()
    return {"message": "deleted"}

class DeleteRequest(BaseModel):
    url: str

@app.delete("/api/upload")
def delete_file(req: DeleteRequest):
    """向前端放开大权的一把单清斩杀令：为了截杀在建任务过程中传一半又不进行落盘新建时产生的废物理附件"""
    filename = req.url.split("/")[-1]
    if not filename:
        return {"error": "Invalid url"}
    file_path = os.path.join("uploads", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"message": "deleted"}

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """基于高性能微架构挂载系统并发拉起本地写源头节点，引入 UUID 防重名覆写屏障隔离机制"""
    urls = []
    for file in files:
        base_name, file_ext = os.path.splitext(file.filename)
        # 利用时间戳组合短效 UUID 来确保并发极高下的绝对唯一性，防止同名文件毁损旧数据
        uniq_filename = f"{base_name}_{int(time.time())}_{uuid.uuid4().hex[:6]}{file_ext}"
        file_location = os.path.join("uploads", uniq_filename)
        
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        # 用相对路径返发从而可以进行普适部署
        urls.append(f"/uploads/{uniq_filename}")
    return {"urls": urls}

# ================================
# 前后置混合生态同源挂盘一体化服务代理核心模块 
# -> 完美规避了开发运维还要装 Nginx 服务器挂靠打包 SPA 文件夹这档破事儿
# ================================
dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
os.makedirs(dist_path, exist_ok=True)
app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
