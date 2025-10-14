# 🚀 StockGuru Web 版快速启动指南

## 5分钟快速开始

### 第一步：配置 Supabase（2分钟）

1. 访问 https://supabase.com 并登录
2. 点击 "New Project"
3. 填写项目信息并创建
4. 等待项目初始化完成
5. 进入项目后，点击左侧 "SQL Editor"
6. 复制 `database/schema.sql` 的内容并执行
7. 点击左侧 "Settings" → "API"
8. 复制以下信息：
   - Project URL
   - anon/public key
   - 

### 第二步：启动后端（2分钟）

```bash
# 1. 进入后端目录
cd stockguru-web/backend

# 2. 创建环境变量文件
cp .env.example .env

# 3. 编辑 .env，填入 Supabase 信息
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_KEY=eyJxxx...

# 4. 检查 Python 版本（需要 3.11 或 3.12，不支持 3.13）
python --version

# 5. 如果是 Python 3.13，切换到 3.12
# 方法1: 使用 pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# 方法2: 使用系统 Python 3.12
# python3.12 -m venv venv
# source venv/bin/activate

# 6. 安装依赖
pip install -r requirements.txt

# 7. 启动服务
uvicorn app.main:app --reload
```

✅ 访问 http://localhost:8000/docs 查看 API 文档

### 第三步：创建前端（1分钟）

```bash
# 1. 回到项目根目录
cd ..

# 2. 创建 Next.js 项目
npx create-next-app@latest frontend --typescript --tailwind --app

# 3. 进入前端目录
cd frontend

# 4. 安装依赖
npm install @supabase/supabase-js

# 5. 创建环境变量
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=你的Supabase URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=你的Supabase Key
EOF

# 6. 启动开发服务器
npm run dev
```

✅ 访问 http://localhost:3000

---

## 验证安装

### 测试后端
```bash
curl http://localhost:8000/health
# 应该返回: {"status":"healthy"}
```

### 测试前端
浏览器访问 http://localhost:3000，应该能看到 Next.js 默认页面

### 测试数据库
访问 Supabase Dashboard → Table Editor，应该能看到创建的表

---

## 下一步

1. 参考 `frontend-examples/` 中的示例代码开发前端页面
2. 完善后端 API 实现（参考 `PROJECT-STATUS.md`）
3. 测试完整的筛选流程

---

## 常见问题

### Q: pip install 失败？
A: 确保 Python 版本 >= 3.11，或使用虚拟环境

### Q: npm install 慢？
A: 使用国内镜像：`npm config set registry https://registry.npmmirror.com`

### Q: Supabase 连接失败？
A: 检查 URL 和 Key 是否正确，确保没有多余的空格

---

**遇到问题？查看 SETUP.md 或 PROJECT-STATUS.md 获取更多帮助**
