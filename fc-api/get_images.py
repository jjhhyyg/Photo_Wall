# -*- coding: utf-8 -*-
"""
阿里云函数计算 - 获取图片列表 API
功能：
1. 列出 OSS 中的所有图片
2. 读取图片的元数据
3. 生成带签名的 URL（支持图片处理参数）
4. 返回 JSON 格式的图片列表
"""

import json
import os
from datetime import datetime, timedelta
from urllib.parse import unquote
import oss2


def handler(event, context):
    """
    事件触发器入口函数 (Compatible with API Gateway / Event Bridge)

    请求参数 (event 中解析):
        - queryParameters: {
            "limit": "100",
            "offset": "0",
            "sort": "date_desc"
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

        # 从环境变量读取配置
        access_key_id = os.environ.get('OSS_ACCESS_KEY_ID')
        access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET')
        bucket_name = os.environ.get('OSS_BUCKET_NAME')
        
        # 获取配置的 Endpoint (建议配置为内网 Endpoint 以节省流量费用)
        endpoint = os.environ.get('OSS_ENDPOINT')
        image_prefix = os.environ.get('OSS_IMAGE_PREFIX', 'images/')

        # 确保 endpoint 包含协议头 (oss2 需要)
        if not endpoint.startswith('http'):
            endpoint = 'https://' + endpoint

        # 初始化 OSS 客户端 (用于连接 OSS 获取列表)
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        # 构造公网访问 URL 的基础地址
        # 格式: https://{bucket}.oss-cn-chengdu.aliyuncs.com
        # 去掉内网标识，得到公网域名
        public_endpoint_domain = os.environ.get('OSS_ENDPOINT').replace('-internal', '')
        # 去掉可能的 http/https 协议头
        if '://' in public_endpoint_domain:
            public_endpoint_domain = public_endpoint_domain.split('://')[-1]
        # 构造完整的公网访问基础 URL
        public_base_url = f"https://{bucket_name}.{public_endpoint_domain}"

        # 解析请求参数 (适配 API 网关透传的结构)
        # API 网关通常将参数放在 queryParameters 字段
        query_params = evt.get('queryParameters', {})
        
        # 如果是 HTTP 触发器以事件模式调用，可能直接在 body 或 queryStringParameters 中
        if not query_params:
             query_params = evt.get('queryStringParameters', {})

        limit = int(query_params.get('limit', 100))
        offset = int(query_params.get('offset', 0))
        sort_by = query_params.get('sort', 'date_desc')

        # 获取所有图片对象
        images = []
        for obj in oss2.ObjectIterator(bucket, prefix=image_prefix):
            # 跳过文件夹
            if obj.key.endswith('/'):
                continue

            # 获取对象元数据（使用 head_object 获取完整元数据，包括自定义元数据）
            meta = bucket.head_object(obj.key)
            headers_dict = meta.headers

            # 提取元数据
            metadata = {
                'date': decode_oss_meta_value(headers_dict.get('x-oss-meta-date', '')),
                'time': decode_oss_meta_value(headers_dict.get('x-oss-meta-time', '')),
                'location': decode_oss_meta_value(headers_dict.get('x-oss-meta-location', '')),
                'camera': decode_oss_meta_value(headers_dict.get('x-oss-meta-camera', '')),
                'note': decode_oss_meta_value(headers_dict.get('x-oss-meta-note', '')),
                'upload_time': decode_oss_meta_value(headers_dict.get('x-oss-meta-upload-time', ''))
            }

            # 生成公共读 URL（不使用签名，要求 Bucket 配置为公共读）
            # 格式: https://{bucket_name}.oss-cn-chengdu.aliyuncs.com/{object_key}
            # 例如: https://hyycy.oss-cn-chengdu.aliyuncs.com/images/xxx.jpg
            url = f"{public_base_url}/{obj.key}"

            # 生成缩略图 URL（添加 OSS 图片处理参数）
            thumbnail_params = 'image/resize,w_360,h_360,m_fill/quality,q_90'
            thumbnail_url = f"{url}?x-oss-process={thumbnail_params}"

            images.append({
                'filename': obj.key.replace(image_prefix, ''),
                'url': url,
                'thumbnail_url': thumbnail_url,
                'size': obj.size,
                'metadata': metadata
            })

        # 排序
        if sort_by == 'date_desc':
            images.sort(key=lambda x: x['metadata']['date'] or '0000-00-00', reverse=True)
        elif sort_by == 'date_asc':
            images.sort(key=lambda x: x['metadata']['date'] or '9999-99-99')

        # 分页
        total = len(images)
        images = images[offset:offset + limit]

        # 返回结果
        result = {
            'success': True,
            'data': images,
            'total': total,
            'limit': limit,
            'offset': offset
        }

        # 返回 API 网关需要的格式
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


def parse_query_string(query_string):
    """解析 URL 查询参数"""
    params = {}
    if query_string:
        for pair in query_string.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key] = value
    return params


def decode_oss_meta_value(value):
    """解码 OSS 自定义元数据，兼容历史未编码数据"""
    if not value:
        return ''

    try:
        # 先进行 URL 解码
        decoded = unquote(str(value), encoding='utf-8')

        # 修复 UTF-8 被误解析为 Latin-1 的问题
        # 如果字符串包含乱码特征，尝试重新编码
        try:
            # 将字符串用 Latin-1 编码回字节，再用 UTF-8 解码
            # 这能修复 UTF-8 字节被错误解释为 Latin-1 字符的问题
            fixed = decoded.encode('latin-1').decode('utf-8')
            return fixed
        except (UnicodeDecodeError, UnicodeEncodeError):
            # 如果修复失败，说明原本就是正确的编码
            return decoded
    except Exception:
        # 如果解码失败，尝试直接返回原值
        try:
            return str(value)
        except:
            return ''
