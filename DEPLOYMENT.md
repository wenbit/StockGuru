# StockGuru 部署指南

**版本**: v1.0  
**更新时间**: 2025-10-15

---

## 📋 目录

1. [GitHub 部署](#github-部署)
2. [本地部署](#本地部署)
3. [云服务器部署](#云服务器部署)
4. [Docker 部署](#docker-部署)
5. [环境变量配置](#环境变量配置)

---

## GitHub 部署

### 1. 创建 GitHub 仓库

**方法1: 使用 GitHub 网页**

1. 访问 https://github.com/new
2. 填写仓库信息：
   - Repository name: `StockGuru`
   - Description: `股票短线复盘助手 - 基于动量分析的量化筛选工具`
   - Public/Private: 选择公开或私有
3. 不要初始化 README（项目已有）
4. 点击 "Create repository"

**方法2: 使用 GitHub CLI**

```bash
# 安装 GitHub CLI (如果未安装)
brew install gh  # macOS
# 或访问 https://cli.github.com/

# 登录
gh auth login

# 创建仓库
gh repo create StockGuru --public --source=. --remote=origin
```

### 2. 推送代码到 GitHub

```bash
# 添加远程仓库（如果还没有）
git remote add origin https://github.com/YOUR_USERNAME/StockGuru.git

# 推送代码
git push -u origin main

# 如果分支名是 master，使用：
# git push -u origin master
```

### 3. 配置 GitHub Pages（可选）

如果要部署前端到 GitHub Pages：

```bash
# 在 frontend 目录
cd frontend

# 修改 next.config.mjs
# 添加 basePath 和 assetPrefix

# 构建
npm run build
npm run export

# 推送到 gh-pages 分支
git subtree push --prefix frontend/out origin gh-pages
```

---

## 本地部署

### 前置要求

- Node.js 18+ 
- Python 3.10+
- npm 或 yarn

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/StockGuru.git
cd StockGuru
```

### 2. 安装后端依赖

```bash
cd stockguru-web/backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

```.env
# Supabase 配置
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO
```

### 4. 启动后端

```bash
# 在 stockguru-web/backend 目录
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 安装前端依赖

```bash
# 新开一个终端
cd frontend

# 安装依赖
npm install
# 或
yarn install
```

### 6. 启动前端

```bash
# 在 frontend 目录
npm run dev
# 或
yarn dev
```

### 7. 访问应用

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

---

## 云服务器部署

### 推荐平台

- **Vercel** (前端) - 免费，自动部署
- **Railway** (后端) - 免费额度，简单部署
- **Render** (后端) - 免费额度，支持Docker
- **阿里云/腾讯云** (全栈) - 完全控制

### 方案1: Vercel (前端) + Railway (后端)

#### 部署前端到 Vercel

1. 访问 https://vercel.com
2. 导入 GitHub 仓库
3. 配置构建设置：
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: .next
   ```
4. 添加环境变量：
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```
5. 点击 Deploy

#### 部署后端到 Railway

1. 访问 https://railway.app
2. 新建项目，选择 "Deploy from GitHub repo"
3. 选择 StockGuru 仓库
4. 配置：
   ```
   Root Directory: stockguru-web/backend
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. 添加环境变量：
   ```
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   PORT=8000
   ```
6. 部署

### 方案2: Docker 部署

#### 创建 Dockerfile (后端)

```dockerfile
# stockguru-web/backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 创建 Dockerfile (前端)

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制应用代码
COPY . .

# 构建
RUN npm run build

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "start"]
```

#### 创建 docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./stockguru-web/backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped
```

#### 使用 Docker Compose 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 环境变量配置

### 后端环境变量

创建 `stockguru-web/backend/.env`:

```env
# Supabase 数据库
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# CORS 配置
CORS_ORIGINS=["http://localhost:3000", "https://your-domain.com"]

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/stockguru.log

# 数据源配置
DATA_SOURCE=pywencai
CACHE_ENABLED=true
CACHE_TTL=3600
```

### 前端环境变量

创建 `frontend/.env.local`:

```env
# API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# 其他配置
NEXT_PUBLIC_APP_NAME=StockGuru
NEXT_PUBLIC_APP_VERSION=1.0.0
```

---

## 生产环境优化

### 1. 后端优化

```bash
# 使用 gunicorn 运行（生产环境）
pip install gunicorn

# 启动命令
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### 2. 前端优化

```bash
# 构建生产版本
cd frontend
npm run build

# 使用 PM2 运行
npm install -g pm2
pm2 start npm --name "stockguru-frontend" -- start
pm2 save
pm2 startup
```

### 3. Nginx 反向代理

```nginx
# /etc/nginx/sites-available/stockguru
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4. SSL 证书（Let's Encrypt）

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 监控和维护

### 1. 日志管理

```bash
# 查看后端日志
tail -f logs/stockguru.log

# 查看前端日志
pm2 logs stockguru-frontend

# 查看Docker日志
docker-compose logs -f
```

### 2. 性能监控

```bash
# 安装监控工具
npm install -g pm2

# 监控进程
pm2 monit

# 查看状态
pm2 status
```

### 3. 数据库备份

```bash
# Supabase 自动备份
# 在 Supabase Dashboard 中配置

# 手动导出数据
# 使用 Supabase CLI 或 Dashboard
```

---

## 故障排查

### 常见问题

**1. 端口被占用**
```bash
# 查找占用端口的进程
lsof -i :8000
lsof -i :3000

# 杀死进程
kill -9 PID
```

**2. 依赖安装失败**
```bash
# 清除缓存
npm cache clean --force
pip cache purge

# 重新安装
npm install
pip install -r requirements.txt
```

**3. 数据库连接失败**
```bash
# 检查环境变量
echo $SUPABASE_URL
echo $SUPABASE_KEY

# 测试连接
curl -X GET $SUPABASE_URL/rest/v1/ \
  -H "apikey: $SUPABASE_KEY"
```

---

## 安全建议

1. **不要提交敏感信息**
   - 使用 `.env` 文件
   - 添加到 `.gitignore`
   - 使用环境变量

2. **定期更新依赖**
   ```bash
   npm audit fix
   pip list --outdated
   ```

3. **使用 HTTPS**
   - 配置 SSL 证书
   - 强制 HTTPS 重定向

4. **限制 API 访问**
   - 配置 CORS
   - 添加速率限制
   - 使用 API 密钥

---

## 📚 相关文档

- [README.md](README.md) - 项目介绍
- [Git提交说明.md](Git提交说明.md) - Git 使用说明
- [docs/FAQ.md](docs/FAQ.md) - 常见问题
- [docs/guides/](docs/guides/) - 使用指南

---

*最后更新: 2025-10-15 04:42*
