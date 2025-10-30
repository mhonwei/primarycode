# AI案例智库系统 - 部署指南

## 目录

1. [本地开发部署](#本地开发部署)
2. [生产环境部署](#生产环境部署)
3. [Docker部署](#docker部署)
4. [云平台部署](#云平台部署)
5. [性能优化](#性能优化)
6. [监控和维护](#监控和维护)

---

## 本地开发部署

### 快速开始

#### Linux/Mac

```bash
# 克隆或下载项目
cd ai-case-library

# 运行启动脚本
./start.sh
```

#### Windows

```batch
# 克隆或下载项目
cd ai-case-library

# 运行启动脚本
start.bat
```

### 手动部署

#### 1. 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 启动后端服务
python app.py
```

后端服务运行在: http://localhost:5000

#### 2. 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

前端应用运行在: http://localhost:3000

### 测试系统

```bash
cd backend
python test_system.py
```

---

## 生产环境部署

### 后端生产部署

#### 1. 使用Gunicorn

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务（4个工作进程）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 2. 使用uWSGI

```bash
# 安装uWSGI
pip install uwsgi

# 创建uwsgi.ini配置文件
[uwsgi]
module = app:app
master = true
processes = 4
socket = 0.0.0.0:5000
chmod-socket = 660
vacuum = true
die-on-term = true
```

```bash
# 启动uWSGI
uwsgi --ini uwsgi.ini
```

#### 3. Nginx反向代理

创建Nginx配置文件 `/etc/nginx/sites-available/ai-case-library`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        root /path/to/frontend/build;
        try_files $uri /index.html;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/ai-case-library /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 前端生产部署

#### 1. 构建生产版本

```bash
cd frontend

# 构建
npm run build
```

#### 2. 使用Nginx托管

将构建好的文件复制到Nginx目录：

```bash
sudo cp -r build/* /var/www/ai-case-library/
```

#### 3. 使用PM2管理进程

```bash
# 安装PM2
npm install -g pm2

# 使用serve托管静态文件
npm install -g serve

# 启动
pm2 start "serve -s build -l 3000" --name ai-case-frontend
```

---

## Docker部署

### 创建Dockerfile

#### 后端Dockerfile

创建 `backend/Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### 前端Dockerfile

创建 `frontend/Dockerfile`:

```dockerfile
FROM node:16 as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 使用Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

启动服务：

```bash
docker-compose up -d
```

查看日志：

```bash
docker-compose logs -f
```

停止服务：

```bash
docker-compose down
```

---

## 云平台部署

### AWS部署

#### 1. EC2实例

```bash
# 连接到EC2实例
ssh -i your-key.pem ubuntu@your-ec2-ip

# 安装依赖
sudo apt update
sudo apt install python3-pip nodejs npm nginx

# 克隆项目
git clone your-repo-url
cd ai-case-library

# 按照生产环境部署步骤操作
```

#### 2. Elastic Beanstalk

创建 `.ebextensions/python.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: backend/app:app
```

部署：

```bash
eb init
eb create ai-case-library-env
eb deploy
```

### Azure部署

#### App Service

```bash
# 安装Azure CLI
az login

# 创建资源组
az group create --name ai-case-library-rg --location eastus

# 创建App Service计划
az appservice plan create --name ai-case-library-plan \
    --resource-group ai-case-library-rg --sku B1 --is-linux

# 创建Web应用
az webapp create --resource-group ai-case-library-rg \
    --plan ai-case-library-plan --name ai-case-library \
    --runtime "PYTHON|3.9"

# 部署代码
az webapp deployment source config-zip \
    --resource-group ai-case-library-rg \
    --name ai-case-library --src backend.zip
```

### Google Cloud Platform

#### App Engine

创建 `app.yaml`:

```yaml
runtime: python39

instance_class: F2

handlers:
- url: /.*
  script: auto

env_variables:
  FLASK_ENV: 'production'
```

部署：

```bash
gcloud app deploy
```

---

## 性能优化

### 后端优化

#### 1. 启用缓存

安装Redis：

```bash
pip install redis
```

在代码中使用缓存：

```python
import redis
from functools import wraps

cache = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached = cache.get(key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            cache.setex(key, timeout, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### 2. 数据库优化

如果使用数据库，添加索引和查询优化：

```python
# 添加索引
db.create_index('cases', 'keyword')
db.create_index('cases', 'created_at')

# 使用连接池
from sqlalchemy.pool import QueuePool
engine = create_engine('postgresql://...', poolclass=QueuePool)
```

#### 3. 异步处理

使用Celery处理耗时任务：

```bash
pip install celery
```

```python
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def generate_case_async(params):
    # 异步生成案例
    pass
```

### 前端优化

#### 1. 代码分割

```javascript
// 使用React.lazy懒加载组件
const CaseViewer = React.lazy(() => import('./components/CaseViewer'));
```

#### 2. 压缩和优化

```bash
# 构建时自动压缩
npm run build

# 使用webpack-bundle-analyzer分析包大小
npm install --save-dev webpack-bundle-analyzer
```

#### 3. CDN加速

使用CDN托管静态资源：

```html
<!-- 使用CDN版本的库 -->
<script src="https://cdn.jsdelivr.net/npm/react@18/umd/react.production.min.js"></script>
```

---

## 监控和维护

### 日志管理

#### 1. 后端日志

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

#### 2. 前端错误跟踪

使用Sentry：

```bash
npm install @sentry/react
```

```javascript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production"
});
```

### 性能监控

#### 1. 后端监控

使用Prometheus + Grafana：

```bash
pip install prometheus-flask-exporter
```

```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

#### 2. 前端监控

使用Google Analytics或自定义监控：

```javascript
// 记录页面访问
analytics.track('page_view', {
  path: window.location.pathname
});

// 记录用户行为
analytics.track('search', {
  keyword: keyword,
  results_count: results.length
});
```

### 健康检查

#### 1. 后端健康检查

已内置在 `/api/health` 端点

#### 2. 定期健康检查脚本

```bash
#!/bin/bash
# health_check.sh

BACKEND_URL="http://localhost:5000/api/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL)

if [ $response -eq 200 ]; then
    echo "✅ 服务正常"
else
    echo "❌ 服务异常 (HTTP $response)"
    # 发送告警
    # ./send_alert.sh
fi
```

设置定时任务：

```bash
# 添加到crontab，每5分钟检查一次
*/5 * * * * /path/to/health_check.sh
```

### 备份策略

#### 1. 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/ai-case-library"
DATE=$(date +%Y%m%d)

# 备份数据库（如果使用）
# mysqldump -u user -p database > $BACKUP_DIR/db_$DATE.sql

# 备份生成的案例
tar -czf $BACKUP_DIR/cases_$DATE.tar.gz /path/to/cases

# 删除30天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

#### 2. 自动备份

```bash
# 添加到crontab，每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

### 更新和维护

#### 1. 依赖更新

```bash
# 后端依赖
pip list --outdated
pip install --upgrade package-name

# 前端依赖
npm outdated
npm update
```

#### 2. 安全更新

```bash
# 检查安全漏洞
pip-audit  # Python
npm audit  # Node.js

# 修复漏洞
pip-audit --fix
npm audit fix
```

---

## 故障排查

### 常见问题

#### 1. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :5000
lsof -i :3000

# 杀死进程
kill -9 PID
```

#### 2. 依赖安装失败

```bash
# 清理缓存
pip cache purge
npm cache clean --force

# 重新安装
pip install -r requirements.txt --no-cache-dir
npm install --force
```

#### 3. 内存不足

```bash
# 增加swap空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 安全建议

1. **使用HTTPS**: 在生产环境使用SSL/TLS证书
2. **环境变量**: 敏感信息存储在环境变量中
3. **访问控制**: 添加身份验证和授权
4. **速率限制**: 防止API滥用
5. **输入验证**: 验证所有用户输入
6. **定期更新**: 保持依赖库最新

---

## 技术支持

如有部署问题，请：

1. 查看日志文件
2. 运行测试脚本
3. 查阅本文档
4. 提交GitHub Issue

---

**祝部署顺利！**
