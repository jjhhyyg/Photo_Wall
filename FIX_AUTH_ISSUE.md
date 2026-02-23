# 函数计算认证问题修复指南

## 问题描述

测试 API 时出现以下错误：
```json
{
    "Code": "MissingRequiredHeader",
    "Message": "required HTTP header Date was not specified"
}
```

这表明函数计算 HTTP 触发器配置了签名认证，但是前端和测试脚本没有提供签名。

---

## 🔧 解决方案

### 方案 1：修改为匿名访问（推荐）

对于个人照片墙项目，最简单的方法是将函数计算配置为匿名访问。

#### 步骤：

1. **登录阿里云函数计算控制台**
   - 访问：https://fc.console.aliyun.com/

2. **找到你的服务**
   - 点击左侧 **服务及函数**
   - 找到 `photo-wall-service`（或你的服务名）

3. **修改每个函数的触发器**

   对以下 3 个函数分别操作：
   - `get-images`
   - `upload-image`
   - `update-metadata`

   **操作步骤**：

   a. 点击函数名进入函数详情

   b. 点击 **触发器管理** 标签

   c. 找到 HTTP 触发器，点击 **编辑**

   d. 修改配置：
   ```
   认证方式：anonymous（匿名）
   请求方式：GET, POST（根据函数选择）
   ```

   e. 点击 **确定** 保存

4. **验证修改**

   修改完成后，重新运行测试：
   ```bash
   ./test_api.sh
   ```

---

### 方案 2：使用签名认证（推荐用于生产环境）

如果你需要保持签名认证（更安全），需要修改前端和测试脚本以添加签名。

#### 步骤 1：创建带签名的测试脚本

创建文件 `test_api_with_auth.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带签名认证的函数计算 API 测试工具
"""

import json
import requests
from datetime import datetime
from urllib.parse import urlparse
import hashlib
import hmac
import base64

def sign_request(method, url, access_key_id, access_key_secret):
    """
    生成函数计算 HTTP 触发器的签名
    """
    parsed_url = urlparse(url)

    # 获取当前时间（GMT 格式）
    date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    # 构造签名字符串
    string_to_sign = f"{method}\\n\\n\\n{date}\\n{parsed_url.path}"

    # 计算签名
    h = hmac.new(
        access_key_secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    )
    signature = base64.b64encode(h.digest()).decode('utf-8')

    # 返回请求头
    return {
        'Date': date,
        'Authorization': f'FC {access_key_id}:{signature}',
        'Content-Type': 'application/json'
    }

def test_get_images(config):
    """测试获取图片列表 API"""
    url = config['aliyun']['fc']['get_images_url']
    access_key_id = config['aliyun']['access_key_id']
    access_key_secret = config['aliyun']['access_key_secret']

    headers = sign_request('GET', url, access_key_id, access_key_secret)

    response = requests.get(f"{url}?limit=5", headers=headers)

    print("\\n🧪 测试 1: 获取图片列表 API")
    print("-" * 60)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    return response.json().get('success', False)

def test_update_metadata(config, filename):
    """测试更新元数据 API"""
    url = config['aliyun']['fc']['update_metadata_url']
    access_key_id = config['aliyun']['access_key_id']
    access_key_secret = config['aliyun']['access_key_secret']

    headers = sign_request('POST', url, access_key_id, access_key_secret)

    data = {
        'filename': filename,
        'metadata': {
            'note': f'签名测试 - {datetime.now()}'
        }
    }

    response = requests.post(url, headers=headers, json=data)

    print("\\n🧪 测试 2: 更新元数据 API")
    print("-" * 60)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    return response.json().get('success', False)

def main():
    print("=" * 60)
    print("  带签名认证的 API 测试工具")
    print("=" * 60)

    # 加载配置
    try:
        with open('config.private.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ 配置文件 config.private.json 不存在！")
        return

    # 检查配置
    if 'YOUR_' in config['aliyun']['access_key_id']:
        print("❌ 请先在 config.private.json 中配置 AccessKey！")
        return

    print("\\n📝 配置信息:")
    print(f"   AccessKey ID: {config['aliyun']['access_key_id'][:10]}...")
    print(f"   API 地址: {config['aliyun']['fc']['get_images_url']}")

    # 运行测试
    success_count = 0

    # 测试 1
    if test_get_images(config):
        print("✅ 测试 1 通过")
        success_count += 1
    else:
        print("❌ 测试 1 失败")

    # 测试 2（需要先获取一张图片的文件名）
    # 暂时跳过

    print("\\n" + "=" * 60)
    print(f"测试完成！通过: {success_count}/1")
    print("=" * 60)

if __name__ == '__main__':
    try:
        import requests
    except ImportError:
        print("❌ 缺少 requests 库，正在安装...")
        import subprocess
        subprocess.check_call(['pip3', 'install', 'requests'])
        import requests

    main()
```

保存后运行：
```bash
chmod +x test_api_with_auth.py
python3 test_api_with_auth.py
```

#### 步骤 2：修改前端代码添加签名

如果使用签名认证，前端也需要修改。但这会比较复杂，因为：
- ❌ 前端无法安全存储 AccessKey Secret
- ❌ 需要额外的后端服务来生成签名

**所以强烈建议使用方案 1（匿名访问）。**

---

## 🎯 推荐方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **匿名访问** | ✅ 配置简单<br>✅ 前端直接调用<br>✅ 测试方便 | ⚠️ 任何人都可以调用 API | 个人项目<br>私有部署 |
| **签名认证** | ✅ 更安全<br>✅ 防止滥用 | ❌ 配置复杂<br>❌ 前端需要后端支持 | 生产环境<br>公开服务 |

---

## 🔒 如果选择匿名访问，如何提升安全性？

即使使用匿名访问，也可以通过以下方式提升安全性：

1. **OSS Bucket 设置为私有**
   - ✅ 已经在 DEPLOY_OSS.md 中说明
   - 图片只能通过签名 URL 访问
   - 签名 URL 有时效性（默认 1 小时）

2. **函数计算设置访问控制**
   - 在函数计算控制台设置 IP 白名单
   - 限制每秒请求数（QPS）
   - 启用访问日志监控

3. **前端设置 Referer 限制**
   - 在 OSS 控制台设置防盗链
   - 只允许特定域名访问

4. **使用 CDN**
   - 阿里云 CDN 可以提供额外的安全防护
   - 防 DDoS 攻击
   - 限制访问频率

---

## ✅ 修复检查清单

修改为匿名访问后，请检查：

- [ ] 3 个函数的 HTTP 触发器都改为 `anonymous`
- [ ] 运行 `./test_api.sh` 测试通过
- [ ] 前端页面能正常加载图片
- [ ] 管理后台能正常上传图片

---

## 🆘 如果还有问题

### 1. 检查函数计算日志

在函数计算控制台：
- 点击函数 → **调用日志**
- 查看详细的错误信息

### 2. 测试 API 连通性

```bash
# 测试是否能访问（不看返回内容）
curl -I "https://YOUR_API_URL"

# 应该看到 HTTP/1.1 200 OK 或类似状态码
```

### 3. 检查 CORS 配置

如果浏览器报 CORS 错误，确认函数代码中设置了 CORS 头：
```python
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}
```

---

**建议：先按照方案 1 修改为匿名访问，测试通过后再考虑是否需要签名认证。**
