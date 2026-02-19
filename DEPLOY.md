# 乐龄健康 - 云端部署指南

## 一、服务器选择

推荐以下云服务器（任选其一）：

| 平台 | 推荐配置 | 预估费用 |
|------|---------|---------|
| 阿里云 ECS | 1核2G, 40G SSD | ~50元/月 |
| 腾讯云 CVM | 1核2G, 40G SSD | ~50元/月 |
| 华为云 ECS | 1核2G, 40G SSD | ~50元/月 |

> 轻量应用服务器通常更便宜，适合本项目

## 二、服务器环境配置

### 1. 安装 Node.js

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# 安装 Node.js 18+
nvm install 18
nvm use 18
```

### 2. 安装 PM2（进程守护）

```bash
npm install -g pm2
```

### 3. 安装 Nginx（反向代理）

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y nginx

# CentOS
sudo yum install -y nginx
```

## 三、部署项目

### 1. 上传代码

```bash
# 方式一：git clone
git clone <你的仓库地址> /home/app/health-news
cd /home/app/health-news

# 方式二：直接上传
scp -r ./* root@你的服务器IP:/home/app/health-news/
```

### 2. 安装依赖

```bash
cd /home/app/health-news
npm install --production
```

### 3. 配置环境变量

```bash
cp .env.example .env
nano .env
```

填入实际的 API 密钥：

```
PORT=3000
BAIDU_TRANSLATE_APPID=你的AppID
BAIDU_TRANSLATE_SECRET=你的密钥
WECHAT_APPID=你的公众号AppID
WECHAT_SECRET=你的公众号AppSecret
```

### 4. 使用 PM2 启动

```bash
# 启动服务
pm2 start server/index.js --name health-news

# 设置开机自启
pm2 startup
pm2 save

# 查看日志
pm2 logs health-news

# 重启
pm2 restart health-news
```

## 四、Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/health-news
```

写入：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/health-news /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 五、百度翻译 API 配置

1. 访问 https://fanyi-api.baidu.com/ 注册账号
2. 创建"通用翻译"应用（标准版免费）
3. 获取 AppID 和密钥，填入 `.env` 文件
4. 免费额度：标准版每月5万字符（足够日常使用）

## 六、微信公众号配置

### 1. 获取 AppID 和 AppSecret

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入「设置与开发」→「基本配置」
3. 复制 AppID 和 AppSecret，填入 `.env`

### 2. 设置 IP 白名单

1. 在「基本配置」页面，点击「IP白名单」
2. 添加你的云服务器公网 IP

### 3. 推送说明

- **订阅号**：每天可群发1次消息
- **服务号**（认证）：每月4次群发
- 系统默认每天 **08:00** 自动推送当日精选文章
- 也可通过管理接口手动触发：`POST /api/admin/wechat-push`

## 七、首次运行采集

部署完成后，手动触发一次全量采集：

```bash
# 方式一：运行脚本
cd /home/app/health-news
node server/scripts/run-aggregation.js

# 方式二：通过API
curl -X POST http://localhost:3000/api/admin/aggregate
```

## 八、常用运维命令

```bash
# 查看服务状态
pm2 status

# 查看实时日志
pm2 logs health-news --lines 100

# 重启服务
pm2 restart health-news

# 手动触发微信推送
curl -X POST http://localhost:3000/api/admin/wechat-push

# 手动触发内容转换
curl -X POST http://localhost:3000/api/admin/transform
```

## 九、定时任务说明

系统启动后自动运行以下定时任务：

| 任务 | 时间 | 说明 |
|------|------|------|
| 新闻采集+转换 | 每天 06:00, 18:00 | 自动采集并翻译新文章 |
| 微信推送 | 每天 08:00 | 推送当日精选到公众号 |

时间可在 `server/config.js` 中修改 `schedule` 字段。
