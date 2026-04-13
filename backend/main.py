from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from database import db
from models import Task, ScheduledEmail
import shutil
import os
import json
import uuid
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import markdown
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

load_dotenv()

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
db.create_tables([Task, ScheduledEmail], safe=True)

scheduler = BackgroundScheduler()

def job_send_email(email_id: int):
    # This function is executed by APScheduler
    try:
        record = ScheduledEmail.get_by_id(email_id)
        if record.status != "Pending":
            return
        
        sender = os.getenv("SMTP_USER")
        password = os.getenv("SMTP_PASS")
        if not sender or not password:
            raise Exception("SMTP credentials not configured in .env file.")
            
        msg = MIMEMultipart("alternative")
        msg["Subject"] = record.subject
        msg["From"] = sender
        msg["To"] = record.recipient
        if record.cc:
            msg["Cc"] = record.cc
            
        # 组装 SMTP 允许投递的全体多收件人列表阵列
        to_addrs = [x.strip() for x in record.recipient.split(",") if x.strip()]
        if record.cc:
            to_addrs += [x.strip() for x in record.cc.split(",") if x.strip()]
        
        # 将我们源生的 Markdown 报告转化为精美的 HTML 表格供领导们在邮箱中审阅
        html_content = markdown.markdown(record.content, extensions=['tables', 'fenced_code'])
        part = MIMEText(html_content, "html", "utf-8")
        msg.attach(part)
        
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_addrs, msg.as_string())
        server.quit()
        
        record.status = "Sent"
        record.save()
    except Exception as e:
        record = ScheduledEmail.get_by_id(email_id)
        record.status = "Failed"
        record.error_msg = str(e)
        record.save()

@app.on_event("startup")
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
    # 挂载所有尚未发送（可能因为服务器宕机漏发）的未来定时任务
    pendings = ScheduledEmail.select().where(ScheduledEmail.status == "Pending", ScheduledEmail.send_time.is_null(False))
    for p in pendings:
        now = datetime.now(p.send_time.tzinfo) if getattr(p.send_time, 'tzinfo', None) else datetime.now()
        if p.send_time > now:
            scheduler.add_job(job_send_email, 'date', run_date=p.send_time, args=[p.id], id=str(p.id), replace_existing=True)
        else:
            # 已经过期的强行发送
            scheduler.add_job(job_send_email, 'date', run_date=now, args=[p.id], id=str(p.id), replace_existing=True)

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

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

class EmailRequest(BaseModel):
    recipient: str
    cc: Optional[str] = None
    subject: str
    content: str
    send_time: Optional[datetime] = None
    
class ScheduledEmailResponse(BaseModel):
    id: int
    recipient: str
    cc: Optional[str]
    subject: str
    send_time: Optional[datetime]
    status: str
    error_msg: Optional[str]

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
# 自动化分发控制核 - 邮件引擎端点
# ================================

@app.post("/api/emails/schedule")
def schedule_email(req: EmailRequest):
    record = ScheduledEmail.create(
        recipient=req.recipient,
        cc=req.cc,
        subject=req.subject,
        content=req.content,
        send_time=req.send_time
    )
    if req.send_time:
        now = datetime.now(req.send_time.tzinfo) if getattr(req.send_time, 'tzinfo', None) else datetime.now()
        if req.send_time > now:
            scheduler.add_job(job_send_email, 'date', run_date=req.send_time, args=[record.id], id=str(record.id), replace_existing=True)
            return {"message": "Email scheduled", "id": record.id}
            
    # 即刻发送，投递给异步后台任务，或挂载极速任务
    now_naive = datetime.now()
    scheduler.add_job(job_send_email, 'date', run_date=now_naive, args=[record.id], id=str(record.id), replace_existing=True)
    return {"message": "Email queued for immediate sending", "id": record.id}

@app.get("/api/emails/scheduled", response_model=List[ScheduledEmailResponse])
def get_scheduled_emails():
    # 提取所有未被发送过滤和归档的定时任务
    records = ScheduledEmail.select().where(ScheduledEmail.status != 'Sent').order_by(ScheduledEmail.id.desc())
    return [
        {
            "id": r.id, 
            "recipient": r.recipient, 
            "cc": r.cc,
            "subject": r.subject, 
            "send_time": r.send_time, 
            "status": r.status, 
            "error_msg": r.error_msg
        } for r in records
    ]

@app.delete("/api/emails/scheduled/{email_id}")
def cancel_scheduled_email(email_id: int):
    record = ScheduledEmail.get_by_id(email_id)
    if record.status == "Pending":
        try:
            scheduler.remove_job(str(record.id))
        except JobLookupError:
            pass
        record.status = "Cancelled"
        record.save()
    return {"message": "Task cancelled"}

# ================================
# 前后置混合生态同源挂盘一体化服务代理核心模块 
# -> 完美规避了开发运维还要装 Nginx 服务器挂靠打包 SPA 文件夹这档破事儿
# ================================
dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
os.makedirs(dist_path, exist_ok=True)
app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
