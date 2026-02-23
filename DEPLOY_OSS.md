# 照片墙 OSS 迁移部署文档

本文档指导你将照片墙项目从纯静态托管迁移到阿里云 OSS + 函数计算架构。

## 📋 架构概览

```
                 ┌─────────────────────┐
                 │   用户浏览器         │
                 └──────┬──────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
  ┌─────────┐   ┌──────────────┐  ┌──────────┐
  │  前端   │   │ 管理后台     │  │ GitHub   │
  │(静态页面)│   │ (本地使用)   │  │  Pages   │
  └────┬────┘   └──────┬───────┘  └──────────┘
       │               │
       │          HTTP API
       │               │
       └───────────────┼───────────────┐
                       ▼               │
              ┌──────────────────┐     │
              │ 阿里云函数计算    │     │
              │  - 获取图片列表   │     │
              │  - 上传图片       │     │
              │  - 更新元数据     │     │
              └────────┬─────────┘     │
                       │               │
                       ▼               ▼
              ┌──────────────────────────┐
              │    阿里云 OSS (私有)      │
              │  - 存储图片              │
              │  - 对象元数据            │
              │  - 实时图片处理          │
              └──────────────────────────┘
```

## 🎯 迁移优势

- ✅ **解决仓库大小限制** - 图片存储在 OSS，不占用 Git 仓库
- ✅ **提升访问速度** - OSS CDN 加速，国内访问更快
- ✅ **增强安全性** - 私有 Bucket + 签名 URL
- ✅ **元数据管理** - 每张图片附带日期、位置、备注等信息
- ✅ **可视化管理** - 本地管理后台，方便上传和编辑

## 📁 项目结构

```
Photo_Wall/
├── index.html              # 前端页面
├── script_oss.js          # OSS 版本前端脚本（新）
├── styles.css
├── config.public.json     # 前端公开配置（仅 API 地址）
├── config.private.json    # 本地私有配置（包含密钥，已忽略）
├── config.public.example.json   # 前端公开配置模板
├── config.private.example.json  # 本地私有配置模板
├── upload_to_oss.py       # OSS 上传工具（新）
├── admin/                 # 管理后台（本地使用，已忽略）
│   ├── index.html
│   ├── admin.js
│   └── admin.css
├── fc-api/                # 函数计算 API 代码（新）
│   ├── get_images.py
│   ├── upload_image.py
│   ├── update_metadata.py
│   ├── requirements.txt
│   └── README.md
└── DEPLOY_OSS.md          # 本文档
```

## 🚀 部署步骤

### 第一步：阿里云准备工作

#### 1.1 确认已完成的操作

你已经完成：
- ✅ 创建阿里云账号
- ✅ 开通 OSS 服务
- ✅ 创建 Bucket：`hyycy`（成都区域，私有）
- ✅ 创建 RAM 用户并获取 AccessKey

#### 1.2 开通函数计算服务

1. 访问 [函数计算控制台](https://fc.console.aliyun.com/)
2. 点击 **立即开通**（如果还没开通）
3. 选择 **按量付费**（有免费额度）

### 第二步：部署函数计算 API

#### 2.1 创建服务

1. 进入函数计算控制台
2. 点击左侧 **服务及函数**
3. 点击 **创建服务**
   - 服务名称：`photo-wall-service`
   - 角色配置：**新建角色** → 赋予 `AliyunOSSFullAccess` 权限

#### 2.2 创建函数1：获取图片列表

1. 在服务中点击 **创建函数**
2. 选择 **从零开始创建**
3. 配置信息：
   - 函数名称：`get-images`
   - 运行环境：`Python 3.10`
   - 触发器类型：`HTTP 触发器`
   - 认证方式：`anonymous`（匿名）
   - 请求方式：`GET, POST`

4. 在代码编辑器中：
   - 复制 `fc-api/get_images.py` 的内容
   - 粘贴到代码编辑器

5. 配置环境变量（在**函数配置**中）：
   ```
   OSS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
   OSS_ACCESS_KEY_SECRET=YOUR_ACCESS_KEY_SECRET
   OSS_BUCKET_NAME=YOUR_BUCKET_NAME
   OSS_ENDPOINT=oss-cn-chengdu.aliyuncs.com
   OSS_IMAGE_PREFIX=images/
   ```

6. 配置依赖层：
   - 方法1：创建层（推荐）
     - 在本地执行：`pip install oss2 Pillow -t layer/python`
     - 打包：`cd layer && zip -r layer.zip .`
     - 上传层到函数计算
   - 方法2：在函数配置中添加 `requirements.txt`

7. 保存并部署

8. **记录触发器 URL**，类似：
   ```
   https://xxx.cn-chengdu.fc.aliyuncs.com/2016-08-15/proxy/photo-wall-service/get-images/
   ```

#### 2.3 创建函数2：上传图片

重复上述步骤，创建：
- 函数名称：`upload-image`
- 代码文件：`fc-api/upload_image.py`
- 环境变量：同上
- 请求方式：`POST`

#### 2.4 创建函数3：更新元数据

- 函数名称：`update-metadata`
- 代码文件：`fc-api/update_metadata.py`
- 环境变量：同上
- 请求方式：`POST`

#### 2.5 测试 API

在函数详情页面点击 **测试函数**，或使用 curl：

```bash
# 测试获取图片列表
curl "https://YOUR_API_URL/get-images/?limit=10"
```

### 第三步：更新配置文件

将函数计算 API 地址填入 `config.public.json`：

```json
{
  "aliyun": {
    "fc": {
         "get_images_url": "https://YOUR_GET_IMAGES.fcapp.run",
         "upload_image_url": "https://YOUR_UPLOAD_IMAGE.fcapp.run",
         "update_metadata_url": "https://YOUR_UPDATE_METADATA.fcapp.run"
    }
  }
}
```

私有配置使用 `config.private.json`（可由 `config.private.example.json` 复制），用于本地上传脚本和管理后台：

```bash
cp config.private.example.json config.private.json
```

### 第四步：上传现有图片到 OSS

#### 4.1 安装 Python 依赖

```bash
pip install oss2 tqdm pillow
```

#### 4.2 运行上传脚本

```bash
python upload_to_oss.py
```

选项说明：
- **选项1**：批量上传（自动提取 EXIF 信息）
- **选项2**：交互式上传（可为每张图片添加备注）
- **选项3**：查看已上传的图片

### 第五步：更新前端代码

#### 5.1 修改 index.html

将 `script.js` 的引用改为 `script_oss.js`：

```html
<!-- 原来的 -->
<script src="script.js"></script>

<!-- 改为 -->
<script src="script_oss.js"></script>
```

#### 5.2 测试前端

在本地打开 `index.html` 或使用本地服务器：

```bash
# 使用 Python 启动本地服务器
python -m http.server 8000

# 访问 http://localhost:8000
```

### 第六步：使用管理后台

#### 6.1 打开管理后台

```bash
# 在浏览器中打开
open admin/index.html

# 或使用本地服务器
cd admin
python -m http.server 8001
# 访问 http://localhost:8001
```

#### 6.2 管理后台功能

- **上传图片**：拖拽或点击上传，自动提取 EXIF 信息
- **编辑元数据**：点击图片的"编辑"按钮
- **搜索**：在搜索框输入备注关键词
- **排序**：按拍摄日期升序/降序

### 第七步：部署到 GitHub Pages

#### 7.1 删除旧的图片文件

```bash
# 保留 images 文件夹，但删除里面的图片
# 图片已经上传到 OSS，不需要在仓库中保留
```

#### 7.2 提交更新

```bash
git add .
git commit -m "迁移到阿里云 OSS + 函数计算架构"
git push
```

#### 7.3 配置 GitHub Pages

1. 进入仓库设置 → Pages
2. 选择 `main` 分支
3. 等待部署完成

## 🔧 常见问题

### Q1：如何添加新照片？

**方法1：使用管理后台（推荐）**
1. 打开 `admin/index.html`
2. 拖拽图片到上传区域
3. 自动提取 EXIF 并上传

**方法2：使用命令行工具**
```bash
python upload_to_oss.py
```

### Q2：如何修改照片元数据？

1. 打开管理后台
2. 找到要编辑的照片
3. 点击"编辑"按钮
4. 修改元数据并保存

### Q3：函数计算 API 调用失败？

检查：
1. 函数计算的环境变量是否正确配置
2. OSS Bucket 权限是否设置为私有
3. RAM 用户是否有 OSS 访问权限
4. 函数计算是否启用 HTTP 触发器

### Q4：签名 URL 过期了怎么办？

签名 URL 默认 1 小时有效期。前端每次加载时会重新获取签名 URL，所以不用担心过期问题。

### Q5：如何备份数据？

使用 OSS 的自动备份功能：
1. 进入 OSS 控制台
2. 选择 Bucket → 冗余或版本控制
3. 开启版本控制或跨区域复制

## 💰 费用估算

基于个人照片墙（1000 张图片，每月 500 次访问）：

| 服务 | 用量 | 费用 |
|------|------|------|
| OSS 存储 | 5GB | ¥1/月 |
| OSS 流量 | 10GB | ¥1/月 |
| 函数计算 | 500 次调用 | 免费（在免费额度内） |
| **总计** | | **约 ¥2/月** |

## 🔒 安全建议

1. ✅ **不要提交 config.private.json** - 已在 `.gitignore` 中忽略
2. ✅ **定期更换 AccessKey** - 在 RAM 控制台操作
3. ✅ **管理后台仅本地使用** - 不要部署到公网
4. ✅ **启用 OSS 访问日志** - 监控异常访问
5. ✅ **设置 OSS 防盗链** - 限制 Referer

## 📚 参考资料

- [阿里云 OSS 文档](https://help.aliyun.com/product/31815.html)
- [阿里云函数计算文档](https://help.aliyun.com/product/50980.html)
- [OSS 图片处理文档](https://help.aliyun.com/document_detail/44688.html)

## ✅ 迁移检查清单

部署前确认：
- [ ] OSS Bucket 已创建并设置为私有
- [ ] RAM 用户已创建并获取 AccessKey
- [ ] 函数计算服务已开通
- [ ] 3 个函数已创建并测试通过
- [ ] `config.public.json` 已正确配置
- [ ] `config.private.json` 已正确配置
- [ ] 图片已上传到 OSS
- [ ] 前端已切换到 `script_oss.js`
- [ ] 本地测试通过
- [ ] 管理后台可以正常使用

---

**🎉 恭喜！你已经完成了从纯静态到 Serverless 架构的迁移！**

现在你的照片墙：
- 不受 GitHub 仓库大小限制
- 访问速度更快（OSS CDN）
- 数据更安全（私有 Bucket + 签名 URL）
- 管理更方便（可视化后台）
- 成本更低（按需付费）

如有问题，请查看 `fc-api/README.md` 或提交 Issue。
