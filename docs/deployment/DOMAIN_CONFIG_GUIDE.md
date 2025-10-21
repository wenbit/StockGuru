# 域名配置快速指南

## 🎯 配置目标

```
主域名: www.520178.xyz
子域名: stockguru.520178.xyz → Vercel (StockGuru 项目)
```

---

## 📋 配置步骤（5分钟完成）

### 步骤 1️⃣：Vercel 添加域名

1. 登录 https://vercel.com/dashboard
2. 选择 StockGuru 项目
3. 点击 **Settings** → **Domains**
4. 输入：`stockguru.520178.xyz`
5. 点击 **Add**

✅ Vercel 会显示需要配置的 DNS 记录

---

### 步骤 2️⃣：Cloudflare 添加 DNS 记录

1. 登录 https://dash.cloudflare.com/
2. 选择域名：`520178.xyz`
3. 点击 **DNS** → **Records**
4. 点击 **Add record**

**填写信息**：

```
┌─────────────────────────────────────────┐
│ Type: CNAME                             │
│ Name: stockguru                         │
│ Target: cname.vercel-dns.com            │
│ Proxy status: DNS only (灰色云朵 ☁️)    │
│ TTL: Auto                               │
└─────────────────────────────────────────┘
```

⚠️ **关键点**：
- Name 只填 `stockguru`（不是完整域名）
- Proxy status 必须是灰色云朵（DNS only）
- 不要开启橙色云朵，否则 SSL 可能失败

5. 点击 **Save**

---

### 步骤 3️⃣：等待生效

**时间线**：
- DNS 传播：1-5 分钟
- SSL 证书：5-30 分钟
- 完全生效：最长 24 小时

**检查方法**：

```bash
# 方法 1：命令行检查
dig stockguru.520178.xyz

# 方法 2：在线检查
# 访问 https://dnschecker.org/
# 输入：stockguru.520178.xyz
```

---

### 步骤 4️⃣：验证配置

1. **检查 Vercel 状态**
   - 返回 Vercel Domains 页面
   - 等待状态从 "Pending" 变为 "Valid"

2. **访问网站**
   ```
   https://stockguru.520178.xyz
   ```

3. **检查 SSL 证书**
   - 点击浏览器地址栏的锁图标
   - 确认证书有效

---

## 🎨 域名结构说明

```
520178.xyz (根域名)
├── www.520178.xyz (主站)
└── stockguru.520178.xyz (StockGuru 项目) ← 我们要配置的
```

---

## 📊 Cloudflare DNS 记录示例

配置完成后，你的 DNS 记录应该类似这样：

```
┌──────────┬────────────┬──────────────────────┬────────┬──────┐
│ Type     │ Name       │ Target               │ Proxy  │ TTL  │
├──────────┼────────────┼──────────────────────┼────────┼──────┤
│ A        │ @          │ xxx.xxx.xxx.xxx      │ 🟠     │ Auto │
│ CNAME    │ www        │ 520178.xyz           │ 🟠     │ Auto │
│ CNAME    │ stockguru  │ cname.vercel-dns.com │ ☁️     │ Auto │ ← 新增
└──────────┴────────────┴──────────────────────┴────────┴──────┘

图例：
🟠 = Proxied (橙色云朵)
☁️ = DNS only (灰色云朵)
```

---

## ⚠️ 常见错误

### ❌ 错误 1：Name 填写错误

```
❌ 错误：Name: stockguru.520178.xyz
✅ 正确：Name: stockguru
```

### ❌ 错误 2：Proxy 状态错误

```
❌ 错误：Proxy status: Proxied (橙色云朵 🟠)
✅ 正确：Proxy status: DNS only (灰色云朵 ☁️)
```

### ❌ 错误 3：Target 填写错误

```
❌ 错误：Target: vercel.com
❌ 错误：Target: stockguru.vercel.app
✅ 正确：Target: cname.vercel-dns.com
```

---

## 🔧 故障排查

### 问题 1：DNS 不生效

**症状**：访问域名显示 "无法访问此网站"

**解决**：
1. 检查 Cloudflare DNS 记录是否正确
2. 等待 5-10 分钟让 DNS 传播
3. 清除本地 DNS 缓存：
   ```bash
   # macOS
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

### 问题 2：SSL 证书错误

**症状**：浏览器显示 "您的连接不是私密连接"

**解决**：
1. 确认 Proxy status 是灰色云朵（DNS only）
2. 在 Vercel 删除域名后重新添加
3. 等待 10-30 分钟让 Vercel 签发证书

### 问题 3：Vercel 显示 "Invalid Configuration"

**症状**：Vercel Domains 页面显示红色错误

**解决**：
1. 检查 DNS 记录的 Target 是否为 `cname.vercel-dns.com`
2. 确认没有其他冲突的 DNS 记录
3. 删除域名后重新添加

---

## ✅ 配置检查清单

### Cloudflare 配置

- [ ] 登录 Cloudflare Dashboard
- [ ] 选择域名 `520178.xyz`
- [ ] 添加 CNAME 记录
  - [ ] Type: `CNAME`
  - [ ] Name: `stockguru`
  - [ ] Target: `cname.vercel-dns.com`
  - [ ] Proxy: `DNS only` (灰色云朵)
- [ ] 保存记录

### Vercel 配置

- [ ] 登录 Vercel Dashboard
- [ ] 选择 StockGuru 项目
- [ ] 添加域名 `stockguru.520178.xyz`
- [ ] 等待状态变为 "Valid"

### 验证测试

- [ ] DNS 解析正确
- [ ] 网站可以访问
- [ ] SSL 证书有效
- [ ] 所有功能正常

---

## 📱 配置截图参考

### Cloudflare DNS 配置

```
Add record
┌─────────────────────────────────────────────────────────┐
│ Type *                                                  │
│ ┌─────────┐                                            │
│ │ CNAME   │                                            │
│ └─────────┘                                            │
│                                                         │
│ Name (required) *                                       │
│ ┌─────────────────────────────────────────────────┐   │
│ │ stockguru                                       │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Target (required) *                                     │
│ ┌─────────────────────────────────────────────────┐   │
│ │ cname.vercel-dns.com                            │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Proxy status                                            │
│ ☁️ DNS only  🟠 Proxied                               │
│    ^^^^^^^                                              │
│    选这个                                               │
│                                                         │
│ TTL                                                     │
│ ┌──────┐                                               │
│ │ Auto │                                               │
│ └──────┘                                               │
│                                                         │
│              [Cancel]  [Save]                          │
└─────────────────────────────────────────────────────────┘
```

### Vercel Domains 配置

```
Domains
┌─────────────────────────────────────────────────────────┐
│ Add Domain                                              │
│ ┌─────────────────────────────────────────────────┐   │
│ │ stockguru.520178.xyz                            │   │
│ └─────────────────────────────────────────────────┘   │
│                                        [Add]            │
└─────────────────────────────────────────────────────────┘

Your Domains
┌─────────────────────────────────────────────────────────┐
│ Domain                      Status    SSL               │
│ ─────────────────────────────────────────────────       │
│ stockguru.520178.xyz        Valid     ✓                │
│ stockguru.vercel.app        Valid     ✓                │
└─────────────────────────────────────────────────────────┘
```

---

## 🎉 配置完成

完成后，你的项目将可以通过以下地址访问：

- ✅ **https://stockguru.520178.xyz** (自定义域名)
- ✅ **https://stockguru.vercel.app** (Vercel 默认域名)

---

## 📞 需要帮助？

如果配置过程中遇到问题：

1. 查看详细文档：`CUSTOM_DOMAIN_SETUP.md`
2. 检查 Vercel 日志
3. 使用在线工具检查 DNS：https://dnschecker.org/
4. 检查 SSL 证书：https://www.ssllabs.com/ssltest/

---

**配置时间**: 约 5 分钟  
**生效时间**: 10-30 分钟  
**状态**: 📝 待配置
