# Nginx 服务端深度部署与配置指南

对于使用公网服务器（如阿里云、腾讯云等）部署，或希望在企业内网接入标准化 Web 服务架构（包含 80 / 443 端口映射、高并发处理等流线端点）的场景，建议搭配 **Nginx** 来反向代理我们的 Task Flow Backend。

---

## 1. 为什么推荐加一层 Nginx
- **端口伪装与隐身**：允许最终用户通过默认网页端（无特殊端口如 `http://xxxxx.com`）自由访问，无需暴露 `:8000`。
- **SSL 加密 (HTTPS 盾牌)**：只有通过 Nginx / Apache 才可以为我们的前后端数据铺设企业级 SSL/TLS 证书机制，阻断黑客与内鬼抓包劫持数据。
- **并发与承载器**：在短时间内数百个附件被跨流并行获取时，Nginx 在资源下发的并发性能极大好过于纯 Python/Uvicorn。

## 2. 操作落座核心步骤

### 2.1 依赖安装：
在您的 Linux 系统中执行包管理器引擎安装：
- **Ubuntu/Debian 体系**：`sudo apt update && sudo apt install nginx`
- **CentOS/RedHat 体系**：`sudo yum install epel-release && sudo yum install nginx`

### 2.2 启动守护核心应用：
请确保您当前已经在您的服务器中正常使用 `./deploy_linux.sh` 或者 `nohup python -m uvicorn main:app --port 8000 &` 持续化唤醒了系统的运转台。(您可以借助 `screen` 或 `supervisor` 进行防断网掉线托管)。

### 2.3 植入配置文件并启动反向桥：
系统根目录给您提供了一份标准的 `nginx_template.conf`。
1. 使用编辑器调开这篇配置文本，修改成您的实际内网网关IP或者向服务商申请来的域名：
    ```text
    server_name www.yourdomain.com;
    ```
2. 将此文件转移安置到 Nginx 的解析池（例如 Ubuntu 下通常是在 `/etc/nginx/conf.d/taskflow.conf` ）。
3. 使用命令重载防火池与核心守门员即可放行请求：
    ```bash
    sudo nginx -t  # 验证配置文件是否合规合法
    sudo systemctl restart nginx
    ```

**🌟 恭喜！您现在可以通过域名或是纯 IP 协议跨网无感知进行 Task Flow 的大军团流转协作了！**
