# 部署指南

本文档涵盖三种部署场景的详细步骤。

---

## 一、本地电脑部署（开发/体验）

适合在自己的 Windows / macOS / Linux 电脑上快速运行和体验。

### 前提条件

- 安装 [Node.js](https://nodejs.org/) v18 或更高版本
- 安装 Git

### 步骤

```bash
# 1. 克隆代码
git clone https://github.com/mhonwei/primarycode.git
cd primarycode

# 2. 安装依赖
npm install

# 3. 启动服务
npm start
```

看到如下输出说明启动成功：

```
==================================================
  健康资讯聚合平台 v1.0.0
==================================================
  服务地址: http://0.0.0.0:3000
==================================================
```

### 访问方式

- **电脑浏览器**: 打开 http://localhost:3000
- **手机浏览器**（同一 Wi-Fi 下）:
  1. 在电脑上查看本机 IP 地址：
     - Windows: 命令行运行 `ipconfig`，找到 "IPv4 地址"
     - macOS/Linux: 终端运行 `ifconfig` 或 `ip addr`
  2. 在手机浏览器输入 `http://你的电脑IP:3000`
  3. 例如电脑 IP 是 192.168.1.100，手机访问 `http://192.168.1.100:3000`

### 首次采集数据

服务启动后数据库是空的，需要触发一次采集：

```bash
# 方法1: 通过命令行
npm run aggregate

# 方法2: 通过 API 接口（浏览器或 curl）
curl -X POST http://localhost:3000/api/admin/aggregate
```

之后定时任务会在每天 06:00 和 18:00 自动采集。

### 添加到手机桌面（PWA 方式）

在手机浏览器中打开页面后：
- **iPhone Safari**: 点击"分享"按钮 → "添加到主屏幕"
- **Android Chrome**: 点击右上角菜单 → "添加到主屏幕"

这样就像一个独立 App 一样从桌面打开了。

---

## 二、服务器部署（公网访问）

适合长期运行、让家人朋友也能访问的正式部署。

### 方案 A: 云服务器 + Docker（推荐）

> 推荐使用阿里云/腾讯云轻量服务器，最低配 2核2G 即可，约 50-100 元/月

```bash
# 1. 在服务器上安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker

# 2. 克隆代码
git clone https://github.com/mhonwei/primarycode.git
cd primarycode

# 3. 一键启动
docker compose up -d

# 4. 查看运行状态
docker compose logs -f
```

服务运行在 `http://服务器IP:3000`。

### 方案 B: 云服务器 + PM2

```bash
# 1. 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 2. 安装 PM2（进程守护）
sudo npm install -g pm2

# 3. 克隆代码并安装
git clone https://github.com/mhonwei/primarycode.git
cd primarycode
npm install

# 4. 用 PM2 启动（后台运行 + 开机自启）
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 配置域名和 HTTPS（推荐）

有域名后使用 Nginx 反向代理 + Let's Encrypt 免费证书：

```bash
# 安装 Nginx
sudo apt install nginx certbot python3-certbot-nginx

# 创建 Nginx 配置
sudo tee /etc/nginx/sites-available/health-news <<'EOF'
server {
    listen 80;
    server_name your-domain.com;   # 替换为你的域名

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 启用配置
sudo ln -s /etc/nginx/sites-available/health-news /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 自动申请 HTTPS 证书
sudo certbot --nginx -d your-domain.com
```

完成后通过 `https://your-domain.com` 访问。

### 方案 C: 免费平台部署

无需自己买服务器，适合小规模使用：

**Railway（推荐）:**
1. 注册 [Railway](https://railway.app)
2. 关联 GitHub 仓库
3. 自动识别 Node.js 项目并部署
4. 免费额度每月 $5，足够个人使用

**Render:**
1. 注册 [Render](https://render.com)
2. 新建 Web Service → 关联 GitHub 仓库
3. Build Command: `npm install`
4. Start Command: `npm start`

---

## 三、微信小程序部署

### 前提条件

1. 注册[微信小程序账号](https://mp.weixin.qq.com/)（个人即可）
2. 安装[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
3. 后端服务已部署到公网（见上面的方案二），且有 HTTPS 域名

### 步骤

```
1. 修改 API 地址
   打开 miniprogram/app.js，将 apiBaseUrl 改为你的实际服务器地址:
   apiBaseUrl: 'https://your-domain.com/api'

2. 打开微信开发者工具
   → 导入项目 → 选择 miniprogram/ 目录
   → 填入你的小程序 AppID

3. 配置合法域名
   登录小程序管理后台 → 开发管理 → 开发设置 → 服务器域名
   → request 合法域名中添加: https://your-domain.com

4. 本地预览/调试
   在开发者工具中点击"预览"，用手机微信扫码即可体验

5. 提交审核
   开发者工具中点击"上传" → 小程序管理后台"提交审核"
   → 审核通过后发布
```

### 小程序 tabBar 图标

当前配置引用了 `assets/icons/` 下的图标文件。
正式发布前需要准备 8 个图标文件（81x81 px，PNG 格式）：

```
miniprogram/assets/icons/
├── home.png              # 首页（未选中）
├── home-active.png       # 首页（选中）
├── category.png          # 分类（未选中）
├── category-active.png   # 分类（选中）
├── trending.png          # 热门（未选中）
├── trending-active.png   # 热门（选中）
├── profile.png           # 我的（未选中）
└── profile-active.png    # 我的（选中）
```

可以用 [iconfont.cn](https://www.iconfont.cn/) 免费下载图标。

---

## 四、环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 3000 | 服务端口 |
| `HOST` | 0.0.0.0 | 监听地址 |
| `DB_PATH` | ./data/health_news.db | 数据库文件路径 |
| `CRON_SCHEDULE` | 0 6,18 * * * | 采集定时任务（cron 表达式） |

自定义示例：
```bash
# 改为每 4 小时采集一次，使用 8080 端口
PORT=8080 CRON_SCHEDULE="0 */4 * * *" npm start
```

---

## 五、常见问题

**Q: 手机和电脑不在同一个网络怎么办？**
A: 本地部署仅限同一 Wi-Fi 访问。如需远程访问，需要部署到云服务器（方案二）。

**Q: 采集不到数据怎么办？**
A: 部分 RSS 源可能需要科学上网。可以在 `server/config.js` 中替换为国内可访问的源。

**Q: 如何添加国内的中文健康资讯源？**
A: 编辑 `server/config.js` 的 `rssSources` 数组，添加新的 RSS 源即可，例如：
```js
{
  name: '丁香医生',
  url: 'https://dxy.com/rss',  // 示例，需要确认实际 RSS 地址
  category: 'wellness',
  language: 'zh',
}
```

**Q: 数据库会不会越来越大？**
A: 系统会自动清理 90 天前且无人点赞/分享的旧文章。可在 `config.js` 中调整 `retentionDays`。
