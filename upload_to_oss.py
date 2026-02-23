#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSS 图片上传脚本（支持元数据）
功能：
1. 自动提取 EXIF 信息（拍摄日期、GPS 位置）
2. 上传图片到 OSS 并附加元数据
3. 支持批量上传和单张上传
"""

import oss2
import os
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


class OSSUploader:
    """OSS 上传器（支持元数据）"""

    def __init__(self, config_path=None):
        """初始化上传器"""
        # 加载配置
        self.config_path = config_path or 'config.private.json'
        self.config = self._load_config(self.config_path)

        # 初始化 OSS 客户端
        auth = oss2.Auth(
            self.config['aliyun']['access_key_id'],
            self.config['aliyun']['access_key_secret']
        )
        self.bucket = oss2.Bucket(
            auth,
            self.config['aliyun']['oss']['endpoint'],
            self.config['aliyun']['oss']['bucket_name']
        )

        # 测试连接
        try:
            self.bucket.get_bucket_info()
            print(f"✅ 成功连接到 OSS Bucket: {self.config['aliyun']['oss']['bucket_name']}")
        except Exception as e:
            raise ConnectionError(f"❌ 连接 OSS 失败: {e}")

    def _load_config(self, config_path):
        """加载配置文件"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"❌ 配置文件不存在: {config_path}\n"
                "请先从 config.private.example.json 复制并创建 config.private.json。"
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 验证配置
        if 'YOUR_ACCESS_KEY_ID' in config['aliyun']['access_key_id']:
            raise ValueError(f"❌ 请先在 {config_path} 中配置你的阿里云 AccessKey")

        print(f"📝 使用配置文件: {config_path}")
        return config

    def extract_exif_metadata(self, image_path):
        """
        提取图片的 EXIF 元数据

        Returns:
            dict: {
                'date': '2024-01-15',
                'time': '14:30:25',
                'location': '30.12345,120.67890',
                'camera': 'iPhone 12',
                'note': ''
            }
        """
        metadata = {
            'date': '',
            'time': '',
            'location': '',
            'camera': '',
            'note': ''
        }

        try:
            image = Image.open(image_path)
            exif_data = image._getexif()

            if not exif_data:
                return metadata

            # 提取拍摄日期和时间
            datetime_original = exif_data.get(36867) or exif_data.get(306)
            if datetime_original:
                try:
                    dt = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
                    metadata['date'] = dt.strftime('%Y-%m-%d')
                    metadata['time'] = dt.strftime('%H:%M:%S')
                except:
                    pass

            # 提取相机型号
            camera_make = exif_data.get(271)  # Make
            camera_model = exif_data.get(272)  # Model
            if camera_make and camera_model:
                metadata['camera'] = f"{camera_make} {camera_model}"
            elif camera_model:
                metadata['camera'] = camera_model

            # 提取 GPS 位置
            gps_info = exif_data.get(34853)
            if gps_info:
                location = self._parse_gps(gps_info)
                if location:
                    metadata['location'] = location

        except Exception as e:
            print(f"⚠️  提取 EXIF 信息失败 ({image_path}): {e}")

        return metadata

    def _parse_gps(self, gps_info):
        """解析 GPS 信息"""
        try:
            gps_data = {}
            for tag, value in gps_info.items():
                decoded = GPSTAGS.get(tag, tag)
                gps_data[decoded] = value

            # 获取经纬度
            lat = gps_data.get('GPSLatitude')
            lat_ref = gps_data.get('GPSLatitudeRef')
            lon = gps_data.get('GPSLongitude')
            lon_ref = gps_data.get('GPSLongitudeRef')

            if lat and lon:
                # 转换为十进制
                lat_decimal = self._convert_to_degrees(lat)
                if lat_ref == 'S':
                    lat_decimal = -lat_decimal

                lon_decimal = self._convert_to_degrees(lon)
                if lon_ref == 'W':
                    lon_decimal = -lon_decimal

                return f"{lat_decimal:.6f},{lon_decimal:.6f}"
        except:
            pass

        return None

    def _convert_to_degrees(self, value):
        """将 GPS 坐标转换为十进制度数"""
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)

    def upload_file(self, local_path, oss_path, metadata=None):
        """
        上传单个文件到 OSS（带元数据）

        Args:
            local_path: 本地文件路径
            oss_path: OSS 中的文件路径
            metadata: 元数据字典

        Returns:
            tuple: (是否成功, 文件路径)
        """
        try:
            # 如果没有提供元数据，自动提取
            if metadata is None:
                metadata = self.extract_exif_metadata(local_path)

            # 准备 OSS 对象元数据 headers
            headers = {
                'x-oss-meta-date': metadata.get('date', ''),
                'x-oss-meta-time': metadata.get('time', ''),
                'x-oss-meta-location': metadata.get('location', ''),
                'x-oss-meta-camera': metadata.get('camera', ''),
                'x-oss-meta-note': metadata.get('note', ''),
                'x-oss-meta-upload-time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 上传文件
            with open(local_path, 'rb') as f:
                self.bucket.put_object(oss_path, f, headers=headers)

            return (True, local_path, metadata)
        except Exception as e:
            return (False, f"{local_path}: {e}", None)

    def upload_directory(self, local_dir='images', interactive=False):
        """
        批量上传文件夹中的所有图片

        Args:
            local_dir: 本地文件夹路径
            interactive: 是否交互式添加备注
        """
        if not os.path.exists(local_dir):
            print(f"❌ 本地文件夹不存在: {local_dir}")
            return

        # 获取所有图片文件
        formats = self.config['image']['formats']
        image_files = []

        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if Path(file).suffix.lower() in formats:
                    local_path = os.path.join(root, file)
                    # 计算相对路径
                    rel_path = os.path.relpath(local_path, local_dir)
                    oss_prefix = self.config['aliyun']['oss']['image_prefix']
                    oss_path = os.path.join(oss_prefix, rel_path).replace('\\', '/')
                    image_files.append((local_path, oss_path))

        if not image_files:
            print(f"⚠️  在 {local_dir} 中没有找到任何图片文件")
            return

        print(f"\n📦 找到 {len(image_files)} 个图片文件")

        # 交互式模式：为每张图片添加备注
        file_metadata = {}
        if interactive:
            print("\n🖊️  交互式模式：为每张图片添加备注（直接回车跳过）\n")
            for local_path, oss_path in image_files:
                filename = os.path.basename(local_path)
                print(f"\n📷 {filename}")

                # 自动提取 EXIF
                metadata = self.extract_exif_metadata(local_path)
                if metadata['date']:
                    print(f"   拍摄日期: {metadata['date']} {metadata['time']}")
                if metadata['location']:
                    print(f"   GPS 位置: {metadata['location']}")
                if metadata['camera']:
                    print(f"   相机: {metadata['camera']}")

                # 手动输入备注
                note = input("   备注: ").strip()
                if note:
                    metadata['note'] = note

                file_metadata[local_path] = metadata

        # 开始上传
        print(f"\n🚀 开始上传...\n")
        success_count = 0
        failed_files = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {}
            for local_path, oss_path in image_files:
                metadata = file_metadata.get(local_path)
                future = executor.submit(self.upload_file, local_path, oss_path, metadata)
                future_to_file[future] = (local_path, oss_path)

            with tqdm(total=len(image_files), desc="上传进度") as pbar:
                for future in as_completed(future_to_file):
                    success, result, meta = future.result()
                    if success:
                        success_count += 1
                    else:
                        failed_files.append(result)
                    pbar.update(1)

        # 输出结果
        print(f"\n{'='*60}")
        print(f"✅ 上传完成! 成功: {success_count}/{len(image_files)}")

        if failed_files:
            print(f"\n❌ 失败的文件 ({len(failed_files)}):")
            for failed in failed_files:
                print(f"   - {failed}")
        else:
            print("🎉 所有文件上传成功!")
        print(f"{'='*60}\n")

    def list_images_with_metadata(self, prefix='images/', max_count=20):
        """列出 OSS 中的图片及其元数据"""
        print(f"\n📋 OSS 中的图片列表 (前 {max_count} 张):")
        print(f"{'='*80}")

        count = 0
        for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
            if count >= max_count:
                print(f"\n... (还有更多文件)")
                break

            # 获取对象元数据
            try:
                meta = self.bucket.get_object_meta(obj.key)
                headers = meta.headers

                print(f"\n📷 {obj.key}")
                print(f"   大小: {obj.size / 1024:.2f} KB")

                # 显示自定义元数据
                if 'x-oss-meta-date' in headers:
                    date = headers['x-oss-meta-date']
                    time = headers.get('x-oss-meta-time', '')
                    if date:
                        print(f"   拍摄时间: {date} {time}")

                if 'x-oss-meta-location' in headers and headers['x-oss-meta-location']:
                    print(f"   位置: {headers['x-oss-meta-location']}")

                if 'x-oss-meta-note' in headers and headers['x-oss-meta-note']:
                    print(f"   备注: {headers['x-oss-meta-note']}")

                count += 1
            except:
                count += 1
                continue

        print(f"\n{'='*80}\n")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 阿里云 OSS 图片上传工具（支持元数据）")
    print("="*60 + "\n")

    try:
        # 创建上传器
        uploader = OSSUploader()

        # 询问上传模式
        print("请选择上传模式:")
        print("1. 批量上传（自动提取 EXIF）")
        print("2. 交互式上传（可为每张图片添加备注）")
        print("3. 查看已上传的图片")

        choice = input("\n请输入选项 (1/2/3): ").strip()

        if choice == '1':
            uploader.upload_directory('images', interactive=False)
        elif choice == '2':
            uploader.upload_directory('images', interactive=True)
        elif choice == '3':
            uploader.list_images_with_metadata()
        else:
            print("❌ 无效的选项")
            return

        print("\n✨ 完成！")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 检查依赖
    try:
        import oss2
        import tqdm
        from PIL import Image
    except ImportError:
        print("❌ 缺少依赖库，请先安装:")
        print("   pip install oss2 tqdm pillow")
        exit(1)

    main()
