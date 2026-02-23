# 快速测试指南

本文档提供快速测试照片墙所有功能的方法。

## 🚀 快速开始

### 1. 配置检查（必须先做！）

运行配置检查脚本，确保所有配置正确：

```bash
./check_config.sh
```

该脚本会检查：

- ✅ 配置文件是否存在
- ✅ JSON 格式是否正确
- ✅ API 地址是否配置
- ✅ Python 依赖是否安装

**如果发现问题**，脚本会给出修复建议。

---

### 2. 启动本地服务

运行启动脚本，选择要测试的服务：

```bash
./start_test.sh
```

**选项说明**：

```
1. 前端照片墙（端口 8000）
   → 在浏览器访问: http://localhost:8000

2. 管理后台（端口 8001）
   → 在浏览器访问: http://localhost:8001

3. 同时启动前端和管理后台
   → 前端: http://localhost:8000
   → 管理后台: http://localhost:8001

4. 运行 API 测试
   → 测试函数计算 API 是否正常

5. 运行 Python 上传工具
   → 批量上传图片到 OSS
```

---

### 3. API 测试

测试函数计算 API 是否正常：

```bash
./test_api.sh
```

**测试选项**：

```
1. 测试获取图片列表 API
   → 验证能否从 OSS 获取图片列表

2. 测试上传图片 API
   → 验证能否上传图片到 OSS

3. 测试更新元数据 API
   → 验证能否更新图片元数据

4. 运行全部测试
   → 自动运行所有 API 测试
```

---

## 📋 完整测试流程

### 推荐测试顺序

```bash
# 1. 检查配置
./check_config.sh

# 2. 测试 API（确保后端正常）
./test_api.sh
# 选择 "4" 运行全部测试

# 3. 测试上传工具（可选）
./start_test.sh
# 选择 "5" 运行 Python 上传工具

# 4. 测试前端
./start_test.sh
# 选择 "1" 启动前端
# 在浏览器中打开 http://localhost:8000

# 5. 测试管理后台
./start_test.sh
# 选择 "2" 启动管理后台
# 在浏览器中打开 http://localhost:8001
```

---

## 🔍 详细测试指南

如果需要更详细的测试步骤和问题排查，请参考：

**[TEST_GUIDE.md](TEST_GUIDE.md)** - 完整的功能测试文档

包含：

- ✅ 详细的测试步骤
- ✅ 预期结果说明
- ✅ 常见问题排查
- ✅ 测试检查清单
- ✅ 测试报告模板

---

## 🛠️ 常用命令

### 配置相关

```bash
# 复制配置模板
cp config.public.example.json config.public.json
cp config.private.example.json config.private.json

# 检查 JSON 格式
python3 -m json.tool config.public.json
python3 -m json.tool config.private.json

# 查看配置内容
cat config.public.json
cat config.private.json
```

### 依赖安装

```bash
# 安装 Python 依赖
pip3 install oss2 tqdm pillow

# 检查依赖是否安装
pip3 list | grep -E "oss2|tqdm|Pillow"
```

### 手动启动服务

```bash
# 启动前端（端口 8000）
python3 -m http.server 8000

# 启动管理后台（端口 8001）
cd admin && python3 -m http.server 8001
```

### API 测试（手动）

```bash
# 替换为你的实际 API 地址

# 获取图片列表
curl "https://YOUR_API_URL?limit=10"

# 测试 API 是否可访问
curl -I "https://YOUR_API_URL"
```

---

## ✅ 测试检查清单

### 第一步：配置检查

- [x] 运行 `./check_config.sh`
- [x] 所有检查项通过
- [x] 配置文件中的占位符已替换

### 第二步：API 测试

- [x] 运行 `./test_api.sh`
- [x] 获取图片列表成功
- [ ] 上传图片成功（可选）
- [ ] 更新元数据成功

### 第三步：前端测试

- [ ] 运行 `./start_test.sh`（选项 1）
- [ ] 页面正常加载
- [ ] 图片列表显示正常
- [ ] 滚动加载正常
- [ ] 图片弹窗正常

### 第四步：管理后台测试

- [ ] 运行 `./start_test.sh`（选项 2）
- [ ] 页面正常加载
- [ ] 图片列表显示正常
- [ ] 上传功能正常
- [ ] 搜索功能正常
- [ ] 编辑元数据正常

### 第五步：Python 工具测试（可选）

- [ ] 运行 `./start_test.sh`（选项 5）
- [ ] 连接 OSS 成功
- [ ] 批量上传成功
- [ ] EXIF 提取正常

---

## 🐛 常见问题

### 问题 1：权限不足

**症状**：

```
bash: ./check_config.sh: Permission denied
```

**解决方法**：

```bash
chmod +x check_config.sh
chmod +x start_test.sh
chmod +x test_api.sh
```

---

### 问题 2：端口被占用

**症状**：

```
OSError: [Errno 48] Address already in use
```

**解决方法**：

```bash
# 查找占用端口的进程
lsof -i :8000

# 关闭进程
kill -9 <PID>

# 或者使用其他端口
python3 -m http.server 8080
```

---

### 问题 3：Python 依赖缺失

**症状**：

```
ModuleNotFoundError: No module named 'oss2'
```

**解决方法**：

```bash
pip3 install oss2 tqdm pillow
```

---

### 问题 4：API 返回 403

**症状**：

```json
{
  "error": "Access denied"
}
```

**解决方法**：

1. 检查函数计算的环境变量配置
2. 检查 OSS Bucket 权限
3. 检查 RAM 用户权限
4. 确认 AccessKey 是否正确

---

### 问题 5：配置文件格式错误

**症状**：

```
json.decoder.JSONDecodeError
```

**解决方法**：

```bash
# 使用工具验证 JSON 格式
python3 -m json.tool config.public.json

# 或在线验证
# 访问 https://jsonlint.com/
```

---

## 📚 相关文档

- **[TEST_GUIDE.md](TEST_GUIDE.md)** - 完整功能测试指南
- **[DEPLOY_OSS.md](DEPLOY_OSS.md)** - OSS 部署文档
- **[README.md](README.md)** - 项目说明文档

---

## 💡 提示

1. **首次测试建议顺序**：配置检查 → API 测试 → 前端测试 → 管理后台测试

2. **每次修改配置后**，重新运行 `./check_config.sh` 确认配置正确

3. **API 测试失败时**，先检查函数计算控制台的日志

4. **前端无法加载图片时**，打开浏览器开发者工具（F12）查看错误信息

5. **上传失败时**，检查图片大小（建议 < 10MB）和格式

---

**祝测试顺利！** 🎉

如有问题，请查看 [TEST_GUIDE.md](TEST_GUIDE.md) 中的详细排查步骤。
