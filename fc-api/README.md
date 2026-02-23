# 函数计算 API 部署说明

本目录包含阿里云函数计算的 API 代码，提供照片墙所需的后端服务。

## 📁 文件说明

- `get_images.py` - 获取图片列表API（生成签名URL）
- `upload_image.py` - 上传图片API
- `update_metadata.py` - 更新图片元数据API
- `requirements.txt` - Python 依赖库

## 🚀 部署步骤

### 1. 创建函数计算服务

1. 登录 [阿里云函数计算控制台](https://fc.console.aliyun.com/)
2. 点击 **创建服务**
   - 服务名称：`photo-wall-service`
   - 角色配置：选择 **新建角色**（赋予 OSS 访问权限）

### 2. 创建函数

#### 函数1：获取图片列表

1. 点击 **创建函数**
2. 选择 **从零开始创建**
3. 填写基本信息：
   - 函数名称：`get-images`
   - 运行环境：`Python 3.10`
   - 触发器类型：`HTTP 触发器`
   - 认证方式：`anonymous`（匿名访问）
   - 请求方式：`GET`

4. 上传代码：
   - 将 `get_images.py` 的内容复制到代码编辑器
   - 或使用 ZIP 包上传

5. 配置环境变量：
   ```
   OSS_ACCESS_KEY_ID=你的AccessKeyId
   OSS_ACCESS_KEY_SECRET=你的AccessKeySecret
   OSS_BUCKET_NAME=hyycy
   OSS_ENDPOINT=oss-cn-chengdu.aliyuncs.com
   OSS_IMAGE_PREFIX=images/
   ```

6. 配置函数依赖：
   - 在 **代码包依赖** 中上传 `requirements.txt`
   - 或在控制台安装层依赖

#### 函数2：上传图片

重复上述步骤，创建函数：
- 函数名称：`upload-image`
- 触发器类型：`HTTP 触发器`
- 请求方式：`POST`
- 代码文件：`upload_image.py`
- 环境变量：同上

#### 函数3：更新元数据

- 函数名称：`update-metadata`
- 触发器类型：`HTTP 触发器`
- 请求方式：`POST`
- 代码文件：`update_metadata.py`
- 环境变量：同上

### 3. 获取 API 地址

创建完成后，在函数详情页面找到 **触发器管理**，复制 **公网访问地址**。

例如：
```
https://xxx.cn-chengdu.fc.aliyuncs.com/2016-08-15/proxy/photo-wall-service/get-images/
```

### 4. 更新配置文件

将获取到的 API 地址填入项目根目录的 `config.public.json`：

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

建议：
- 公开配置：`cp config.public.example.json config.public.json`
- 私有配置：`cp config.private.example.json config.private.json`

## 🧪 测试 API

### 测试获取图片列表

```bash
curl "https://YOUR_API_URL/get-images/?limit=10"
```

### 测试上传图片

```bash
curl -X POST https://YOUR_API_URL/upload-image/ \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.jpg",
    "data": "data:image/jpeg;base64,/9j/4AAQ...",
    "metadata": {
      "note": "测试上传"
    }
  }'
```

### 测试更新元数据

```bash
curl -X POST https://YOUR_API_URL/update-metadata/ \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.jpg",
    "metadata": {
      "note": "更新的备注"
    }
  }'
```

## 💰 费用说明

函数计算按调用次数和执行时间收费：
- **免费额度**：100万次调用/月，40万CU-秒/月
- **预估成本**：个人照片墙项目基本在免费额度内

## 🔒 安全建议

1. **不要在代码中硬编码 AccessKey**，使用环境变量
2. 考虑为 HTTP 触发器添加 **自定义域名**
3. 可以启用 **请求签名验证**，防止滥用
4. 定期检查函数调用日志

## 📚 参考文档

- [阿里云函数计算文档](https://help.aliyun.com/product/50980.html)
- [OSS Python SDK](https://help.aliyun.com/document_detail/32026.html)
