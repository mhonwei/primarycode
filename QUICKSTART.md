# AI案例智库系统 - 快速开始

## 5分钟快速启动

### 方式一：使用启动脚本（推荐）

#### Linux/Mac
```bash
./start.sh
```

#### Windows
```batch
start.bat
```

### 方式二：手动启动

#### 1. 启动后端（终端1）

```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### 2. 启动前端（终端2）

```bash
cd frontend
npm install
npm start
```

#### 3. 访问系统

打开浏览器访问: http://localhost:3000

---

## 快速测试

### 1. 搜索测试

```bash
cd backend
python test_system.py
```

### 2. 手动测试

1. 在搜索框输入: **深度学习在医疗影像的应用**
2. 选择搜索范围: **全部**
3. 点击"开始搜索"
4. 查看搜索结果
5. 点击"基于这些结果生成教学案例"
6. 设置案例参数：
   - 案例类型: **问题导向型**
   - 难度: **中级**
   - 侧重点: **技术原理**
   - 受众: **本科生**
7. 点击"生成案例"
8. 查看生成的案例
9. 选择格式导出（Markdown/HTML/JSON）

---

## 系统要求

- Python 3.9+
- Node.js 16+
- 4GB+ RAM
- 稳定的网络连接

---

## 常见问题

**Q: 端口被占用怎么办？**

A: 修改端口配置：
- 后端: 在 `backend/app.py` 修改 `port=5000`
- 前端: 在 `frontend/package.json` 修改 `PORT=3000`

**Q: 依赖安装失败？**

A: 尝试：
```bash
# Python
pip install -r requirements.txt --no-cache-dir

# Node.js
npm install --force
```

**Q: 搜索无结果？**

A:
- 检查网络连接
- 尝试更换关键词
- 查看后端日志

---

## 下一步

- 阅读 [USAGE.md](USAGE.md) 了解详细使用方法
- 阅读 [DEPLOY.md](DEPLOY.md) 了解生产环境部署
- 阅读 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 了解项目结构

---

## 技术支持

- GitHub Issues: 提交问题和建议
- 文档: 查看完整文档
- Email: 联系项目维护者

---

**开始探索AI案例智库系统吧！** 🚀
