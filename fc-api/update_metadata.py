# -*- coding: utf-8 -*-
"""
阿里云函数计算 - 更新图片元数据 API
功能：
1. 更新 OSS 对象的元数据
2. 支持批量更新
"""

import json
import os
from urllib.parse import quote
import oss2


def handler(event, context):
    """
    事件触发器入口函数 (Compatible with API Gateway / Event Bridge)

    请求方式: POST
    请求体 (JSON):
        {
            "filename": "xxx.jpg",
            "metadata": {
                "date": "2024-01-15",
                "time": "14:30:25",
                "location": "30.123,120.456",
                "camera": "iPhone 12",
                "note": "更新的备注"
            }
        }

    返回:
        JSON: {
            "isBase64Encoded": false,
            "statusCode": 200,
            "headers": {...},
            "body": "..."
        }
    """
    # CORS 头
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        # 解析 event
        try:
            evt = json.loads(event)
        except:
            evt = {}

        # 处理 OPTIONS 请求（CORS 预检）
        if evt.get('httpMethod') == 'OPTIONS':
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": headers,
                "body": ""
            }

        # 读取请求体
        body_str = evt.get('body')
        if evt.get('isBase64Encoded'):
            import base64
            body_bytes = base64.b64decode(body_str)
            body_str = body_bytes.decode('utf-8')
        
        request_data = json.loads(body_str) if body_str else {}

        # 解析参数
        filename = request_data.get('filename')
        metadata = request_data.get('metadata', {})

        if not filename:
             return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"success": False, "error": "缺少必要参数: filename"}, ensure_ascii=False)
            }

        # 从环境变量读取配置
        access_key_id = os.environ.get('OSS_ACCESS_KEY_ID')
        access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET')
        bucket_name = os.environ.get('OSS_BUCKET_NAME')
        endpoint = os.environ.get('OSS_ENDPOINT')
        
        # 确保 endpoint 包含协议头
        if endpoint and not endpoint.startswith('http'):
            endpoint = 'https://' + endpoint
            
        image_prefix = os.environ.get('OSS_IMAGE_PREFIX', 'images/')

        # 初始化 OSS 客户端
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        # 生成 OSS 路径
        oss_key = f"{image_prefix}{filename}"

        # 检查文件是否存在
        if not bucket.object_exists(oss_key):
             return {
                "isBase64Encoded": False,
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"success": False, "error": f"文件不存在: {filename}"}, ensure_ascii=False)
            }

        # 准备新的元数据 (copy_object 需要 x-oss-meta- 前缀)
        
        # 获取现有元数据
        head_res = bucket.head_object(oss_key)
        existing_meta = head_res.headers
        
        # 构造新的 meta headers
        new_headers = {}
        # 保留现有的 x-oss-meta- 开头的自定义元数据
        for k, v in existing_meta.items():
            if k.startswith('x-oss-meta-'):
                new_headers[k] = v
        
        # 更新指定的字段
        if 'date' in metadata: new_headers['x-oss-meta-date'] = encode_oss_meta_value(metadata['date'])
        if 'time' in metadata: new_headers['x-oss-meta-time'] = encode_oss_meta_value(metadata['time'])
        if 'location' in metadata: new_headers['x-oss-meta-location'] = encode_oss_meta_value(metadata['location'])
        if 'camera' in metadata: new_headers['x-oss-meta-camera'] = encode_oss_meta_value(metadata['camera'])
        if 'note' in metadata: new_headers['x-oss-meta-note'] = encode_oss_meta_value(metadata['note'])

        # 使用 copy_object 更新元数据（源和目标相同，即修改自身元数据）
        bucket.copy_object(bucket_name, oss_key, oss_key, headers=new_headers)

        # 返回结果
        result = {
            'success': True,
            'message': '元数据更新成功',
            'filename': filename
        }

        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(result, ensure_ascii=False)
        }

    except Exception as e:
        # 错误处理
        error_result = {
            'success': False,
            'error': str(e)
        }
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps(error_result, ensure_ascii=False)
        }


def encode_oss_meta_value(value):
    """对 OSS 自定义元数据做安全编码，避免中文导致签名不一致"""
    if value is None:
        return ''

    text = str(value).replace('\r', ' ').replace('\n', ' ').strip()
    # 显式使用 UTF-8 编码
    return quote(text, safe='-_.~', encoding='utf-8')
