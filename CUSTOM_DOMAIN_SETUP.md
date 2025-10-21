# 自定义域名配置指南

## 📋 目标

为 StockGuru 项目配置自定义域名：`stockguru.520178.xyz`

- **域名**: stockguru.520178.xyz
- **DNS 服务商**: Cloudflare
- **部署平台**: Vercel

---

## 🎯 第一步：在 Vercel 添加自定义域名

### 1.1 登录 Vercel

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择你的 StockGuru 项目

### 1.2 添加域名

1. 点击项目名称进入项目详情
2. 点击顶部导航栏的 **"Settings"**
3. 在左侧菜单选择 **"Domains"**
4. 在输入框中输入：`stockguru.520178.xyz`
5. 点击 **"Add"** 按钮

### 1.3 获取 DNS 配置信息

添加域名后，Vercel 会显示需要配置的 DNS 记录，通常有两种方式：

#### 方式 A：CNAME 记录（推荐）

```
Type: CNAME
Name: stockguru
Value: cname.vercel-dns.com
```

#### 方式 B：A 记录

```
Type: A
Name: stockguru
Value: 76.76.21.21
```

**推荐使用 CNAME 方式**，因为 Vercel 的 IP 可能会变化。

---

## ☁️ 第二步：在 Cloudflare 配置 DNS

### 2.1 登录 Cloudflare

1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 选择你的域名：`520178.xyz`

### 2.2 添加 DNS 记录

1. 点击左侧菜单的 **"DNS"** → **"Records"**
2. 点击 **"Add record"** 按钮

### 2.3 配置 CNAME 记录

填写以下信息：

```
Type: CNAME
Name: stockguru
Target: cname.vercel-dns.com
Proxy status: DNS only (灰色云朵，关闭代理)
TTL: Auto
```

**⚠️ 重要**：
- **Name** 填写：`stockguru`（不是完整域名）
- **Proxy status** 必须设置为 **"DNS only"**（灰色云朵图标）
- 如果开启 Cloudflare 代理（橙色云朵），Vercel 的 SSL 证书可能无法正常工作

### 2.4 保存配置

1. 点击 **"Save"** 按钮
2. 等待 DNS 记录生效（通常 1-5 分钟）

---

## 🔐 第三步：配置 SSL 证书

### 3.1 Vercel 自动配置

Vercel 会自动为你的域名申请 Let's Encrypt SSL 证书，无需手动操作。

### 3.2 等待证书签发

1. 返回 Vercel 的 Domains 页面
2. 查看域名状态，应该显示：
   - ⏳ **"Pending"** - 正在配置中
   - ✅ **"Valid"** - 配置成功

通常需要 1-10 分钟，最长可能需要 24 小时。

### 3.3 Cloudflare SSL 设置（可选）

如果你想使用 Cloudflare 的代理功能：

1. 在 Cloudflare 点击 **"SSL/TLS"** → **"Overview"**
2. 设置加密模式为 **"Full"** 或 **"Full (strict)"**
3. 返回 DNS 记录，将 Proxy status 改为 **"Proxied"**（橙色云朵）

**注意**：使用 Cloudflare 代理可能会影响 Vercel 的某些功能。

---

## ✅ 第四步：验证配置

### 4.1 检查 DNS 解析

使用命令行工具检查 DNS 是否生效：

```bash
# macOS/Linux
dig stockguru.520178.xyz

# 或使用 nslookup
nslookup stockguru.520178.xyz

# 应该看到 CNAME 记录指向 cname.vercel-dns.com
```

在线工具：
- [DNS Checker](https://dnschecker.org/)
- 输入：`stockguru.520178.xyz`
- 检查全球 DNS 传播状态

### 4.2 访问网站

在浏览器中访问：

```
https://stockguru.520178.xyz
```

如果配置成功，应该能看到你的 StockGuru 应用。

### 4.3 检查 SSL 证书

1. 在浏览器地址栏点击锁图标
2. 查看证书信息
3. 确认证书由 Let's Encrypt 签发
4. 确认域名匹配

---

## 🔧 第五步：更新项目配置（可选）

### 5.1 更新 CORS 配置

如果后端有 CORS 限制，需要添加新域名：

编辑 `stockguru-web/backend/app/main.py`：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stockguru.520178.xyz",  # 新增自定义域名
        "https://stockguru.vercel.app",  # 保留 Vercel 默认域名
        "http://localhost:3000",         # 本地开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.2 更新环境变量（如果需要）

如果前端代码中硬编码了域名，需要更新：

```bash
# Vercel 环境变量
NEXT_PUBLIC_SITE_URL=https://stockguru.520178.xyz
```

---

## 🚨 常见问题

### 1. DNS 记录不生效

**症状**：
- 访问域名显示 "DNS_PROBE_FINISHED_NXDOMAIN"
- 或显示 "This site can't be reached"

**解决方法**：
1. 检查 Cloudflare DNS 记录是否正确
2. 确认 Name 字段只填 `stockguru`，不是完整域名
3. 等待 DNS 传播（最长 24 小时）
4. 清除本地 DNS 缓存：
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Windows
   ipconfig /flushdns
   ```

### 2. SSL 证书错误

**症状**：
- 浏览器显示 "Your connection is not private"
- 或 "NET::ERR_CERT_COMMON_NAME_INVALID"

**解决方法**：
1. 确认 Cloudflare Proxy status 设置为 **"DNS only"**（灰色云朵）
2. 在 Vercel 删除域名后重新添加
3. 等待 Vercel 重新签发证书（最长 24 小时）
4. 检查 Cloudflare SSL 模式设置为 "Full" 或 "Full (strict)"

### 3. Vercel 显示 "Invalid Configuration"

**症状**：
- Vercel Domains 页面显示红色错误

**解决方法**：
1. 检查 DNS 记录的 Target 是否正确：`cname.vercel-dns.com`
2. 确认域名没有其他冲突的 DNS 记录
3. 删除域名后重新添加

### 4. 网站可以访问但样式丢失

**症状**：
- 页面能打开但没有样式
- 控制台显示资源加载失败

**解决方法**：
1. 检查 CORS 配置
2. 清除浏览器缓存
3. 在 Vercel 重新部署项目

### 5. Cloudflare 代理导致问题

**症状**：
- 开启橙色云朵后网站无法访问
- 或出现 525/526 错误

**解决方法**：
1. 暂时关闭 Cloudflare 代理（灰色云朵）
2. 等待 Vercel SSL 证书配置完成
3. 如需使用代理，确保 Cloudflare SSL 模式为 "Full (strict)"

---

## 📊 配置检查清单

### Cloudflare DNS 配置

- [ ] 登录 Cloudflare Dashboard
- [ ] 选择域名 520178.xyz
- [ ] 添加 CNAME 记录
  - [ ] Type: CNAME
  - [ ] Name: stockguru
  - [ ] Target: cname.vercel-dns.com
  - [ ] Proxy status: DNS only（灰色云朵）
- [ ] 保存记录

### Vercel 域名配置

- [ ] 登录 Vercel Dashboard
- [ ] 选择 StockGuru 项目
- [ ] 进入 Settings → Domains
- [ ] 添加域名：stockguru.520178.xyz
- [ ] 等待状态变为 "Valid"
- [ ] 检查 SSL 证书状态

### 验证测试

- [ ] DNS 解析正确（dig/nslookup）
- [ ] 网站可以访问（https://stockguru.520178.xyz）
- [ ] SSL 证书有效（浏览器锁图标）
- [ ] 所有功能正常工作
- [ ] 后端 API 调用正常

---

## 🎯 完整配置示例

### Cloudflare DNS 记录

```
Type    Name        Target                  Proxy   TTL
CNAME   stockguru   cname.vercel-dns.com    DNS     Auto
```

### Vercel Domains 配置

```
Domain                      Status    SSL
stockguru.520178.xyz        Valid     ✓
stockguru.vercel.app        Valid     ✓
```

---

## 📝 配置时间线

1. **0-5 分钟**：在 Vercel 添加域名
2. **5-10 分钟**：在 Cloudflare 配置 DNS
3. **10-30 分钟**：等待 DNS 传播
4. **30-60 分钟**：Vercel 签发 SSL 证书
5. **完成**：域名可以正常访问

**总耗时**：通常 30-60 分钟，最长可能需要 24 小时

---

## 🔗 相关资源

### 官方文档

- **Vercel 自定义域名**: https://vercel.com/docs/concepts/projects/domains
- **Cloudflare DNS**: https://developers.cloudflare.com/dns/
- **SSL/TLS 配置**: https://developers.cloudflare.com/ssl/

### 在线工具

- **DNS 检查**: https://dnschecker.org/
- **SSL 检查**: https://www.ssllabs.com/ssltest/
- **Whois 查询**: https://who.is/

---

## 💡 最佳实践

### 1. 保留 Vercel 默认域名

不要删除 `stockguru.vercel.app`，作为备用域名使用。

### 2. 使用 HTTPS

始终使用 HTTPS 访问，Vercel 会自动重定向 HTTP 到 HTTPS。

### 3. 监控 SSL 证书

SSL 证书有效期 90 天，Vercel 会自动续期，但建议定期检查。

### 4. 配置多个域名（可选）

可以同时配置多个域名指向同一个项目：
- stockguru.520178.xyz（主域名）
- www.stockguru.520178.xyz（WWW 子域名）
- stockguru.vercel.app（Vercel 默认域名）

### 5. 使用 Cloudflare 功能（可选）

配置成功后，可以启用 Cloudflare 的功能：
- CDN 加速
- DDoS 防护
- 页面规则
- 缓存优化

---

## ✅ 配置完成

完成以上步骤后，你的 StockGuru 项目将可以通过以下地址访问：

- ✅ https://stockguru.520178.xyz（自定义域名）
- ✅ https://stockguru.vercel.app（Vercel 默认域名）

---

**配置日期**: 2025-10-21  
**域名**: stockguru.520178.xyz  
**状态**: 📝 待配置
