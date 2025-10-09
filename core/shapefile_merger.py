#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHP文件合并模块
用于合并两个或多个SHP文件，支持不同几何类型的智能合并

作者: Claude Code
创建时间: 2024-10-09
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Union
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection
from pyproj import CRS


class ShapefileMerger:
    """SHP文件合并器"""

    def __init__(self):
        """初始化合并器"""
        self.logger = logging.getLogger(__name__)

    def validate_shapefile(self, file_path: str) -> Dict:
        """
        验证SHP文件

        Args:
            file_path: SHP文件路径

        Returns:
            Dict: 验证结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'文件不存在: {file_path}'
                }

            # 检查文件扩展名
            if not file_path.lower().endswith('.shp'):
                return {
                    'success': False,
                    'error': '文件类型错误，请选择.shp文件'
                }

            # 尝试读取文件
            gdf = gpd.read_file(file_path)

            if gdf.empty:
                return {
                    'success': False,
                    'error': 'SHP文件为空'
                }

            # 获取文件信息
            geometry_types = gdf.geometry.geom_type.unique()

            return {
                'success': True,
                'file_info': {
                    'path': file_path,
                    'feature_count': len(gdf),
                    'columns': list(gdf.columns),
                    'geometry_types': geometry_types.tolist(),
                    'crs': str(gdf.crs) if gdf.crs else None,
                    'bounds': gdf.total_bounds.tolist()
                },
                'gdf': gdf
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'读取SHP文件失败: {str(e)}'
            }

    def check_compatibility(self, files_info: List[Dict]) -> Dict:
        """
        检查多个SHP文件的兼容性

        Args:
            files_info: 文件信息列表

        Returns:
            Dict: 兼容性检查结果
        """
        if len(files_info) < 2:
            return {
                'compatible': False,
                'error': '至少需要两个SHP文件进行合并'
            }

        # 检查几何类型
        all_geometry_types = set()
        for info in files_info:
            if info['success']:
                all_geometry_types.update(info['file_info']['geometry_types'])

        # 判断是否可以合并
        geometry_compatible = True
        merge_type = None

        # 检查是否都是点类型
        point_types = {'Point', 'MultiPoint'}
        if all_geometry_types.issubset(point_types):
            merge_type = 'Point'
        # 检查是否都是线类型
        elif all_geometry_types.issubset({'LineString', 'MultiLineString'}):
            merge_type = 'LineString'
        # 检查是否都是面类型
        elif all_geometry_types.issubset({'Polygon', 'MultiPolygon'}):
            merge_type = 'Polygon'
        else:
            geometry_compatible = False

        # 检查坐标系
        crs_list = []
        for info in files_info:
            if info['success']:
                crs = info['file_info']['crs']
                if crs:
                    crs_list.append(crs)

        crs_compatible = len(set(crs_list)) <= 1 if crs_list else True

        return {
            'compatible': geometry_compatible and crs_compatible,
            'merge_type': merge_type,
            'geometry_compatible': geometry_compatible,
            'crs_compatible': crs_compatible,
            'all_geometry_types': list(all_geometry_types),
            'common_crs': crs_list[0] if crs_list else None,
            'issues': []
        }

    def reproject_geodataframe(self, gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame:
        """
        重投影地理数据框到目标坐标系

        Args:
            gdf: 地理数据框
            target_crs: 目标坐标系

        Returns:
            gpd.GeoDataFrame: 重投影后的数据框
        """
        try:
            if gdf.crs is None:
                # 如果没有坐标系，假设为WGS84
                gdf = gdf.set_crs('EPSG:4326')

            # 如果目标坐标系与当前不同，进行重投影
            if str(gdf.crs) != target_crs:
                gdf = gdf.to_crs(target_crs)

            return gdf

        except Exception as e:
            self.logger.error(f"重投影失败: {e}")
            raise e

    def standardize_geometry(self, gdf: gpd.GeoDataFrame, target_type: str) -> gpd.GeoDataFrame:
        """
        标准化几何类型

        Args:
            gdf: 地理数据框
            target_type: 目标几何类型 (Point, LineString, Polygon)

        Returns:
            gpd.GeoDataFrame: 标准化后的数据框
        """
        def standardize_geom(geom):
            if geom is None or geom.is_empty:
                return None

            # 如果已经是目标类型，直接返回
            if target_type == 'Point' and isinstance(geom, (Point, MultiPoint)):
                return geom
            elif target_type == 'LineString' and isinstance(geom, (LineString, MultiLineString)):
                return geom
            elif target_type == 'Polygon' and isinstance(geom, (Polygon, MultiPolygon)):
                return geom

            # 否则尝试转换
            try:
                if target_type == 'Point':
                    if isinstance(geom, Polygon):
                        return geom.centroid
                    elif isinstance(geom, LineString):
                        return geom.interpolate(0.5, normalized=True)
                elif target_type == 'LineString':
                    if isinstance(geom, Polygon):
                        return geom.exterior
                elif target_type == 'Polygon':
                    if isinstance(geom, Point):
                        # 创建一个缓冲区
                        return geom.buffer(0.0001)  # 小缓冲区
                    elif isinstance(geom, LineString):
                        return geom.buffer(0.0001)

                return geom

            except Exception as e:
                self.logger.warning(f"几何类型转换失败: {e}")
                return None

        # 复制数据框
        result_gdf = gdf.copy()

        # 标准化几何对象
        result_gdf['geometry'] = gdf['geometry'].apply(standardize_geom)

        # 移除无效几何
        result_gdf = result_gdf[~result_gdf['geometry'].isnull()]
        result_gdf = result_gdf[~result_gdf['geometry'].is_empty]

        return result_gdf

    def merge_shapefiles(self, file_paths: List[str], output_path: str,
                        target_crs: Optional[str] = None,
                        merge_strategy: str = 'union') -> Dict:
        """
        合并多个SHP文件

        Args:
            file_paths: SHP文件路径列表
            output_path: 输出文件路径
            target_crs: 目标坐标系 (可选)
            merge_strategy: 合并策略 ('union', 'append')

        Returns:
            Dict: 合并结果
        """
        try:
            # 验证所有文件
            files_info = []
            for file_path in file_paths:
                info = self.validate_shapefile(file_path)
                files_info.append(info)

            # 检查兼容性
            compatibility = self.check_compatibility(files_info)
            if not compatibility['compatible']:
                return {
                    'success': False,
                    'error': f'文件不兼容: {compatibility.get("issues", "未知错误")}'
                }

            # 设置目标坐标系
            if not target_crs:
                target_crs = compatibility['common_crs'] or 'EPSG:4326'

            # 读取和预处理所有文件
            geodataframes = []
            for i, info in enumerate(files_info):
                if not info['success']:
                    continue

                gdf = info['gdf']

                # 重投影到目标坐标系
                gdf = self.reproject_geodataframe(gdf, target_crs)

                # 标准化几何类型
                if compatibility['merge_type']:
                    gdf = self.standardize_geometry(gdf, compatibility['merge_type'])

                # 添加来源文件标识
                gdf['source_file'] = os.path.basename(file_paths[i])

                geodataframes.append(gdf)

            if not geodataframes:
                return {
                    'success': False,
                    'error': '没有有效的SHP文件可以合并'
                }

            # 合并数据框
            if merge_strategy == 'union':
                # 联合策略：合并所有要素
                merged_gdf = gpd.GeoDataFrame(pd.concat(geodataframes, ignore_index=True))
            else:
                # 追加策略：简单连接
                merged_gdf = gpd.GeoDataFrame(pd.concat(geodataframes, ignore_index=True))

            # 移除重复的几何对象
            if merge_strategy == 'union':
                merged_gdf = merged_gdf.drop_duplicates(subset=['geometry'])

            # 设置输出坐标系
            merged_gdf.crs = target_crs

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 导出合并后的文件
            merged_gdf.to_file(output_path, encoding='utf-8')

            return {
                'success': True,
                'output_path': output_path,
                'merge_info': {
                    'input_files': len(geodataframes),
                    'total_features': len(merged_gdf),
                    'geometry_type': compatibility['merge_type'],
                    'crs': target_crs,
                    'merge_strategy': merge_strategy
                }
            }

        except Exception as e:
            self.logger.error(f"合并SHP文件失败: {e}")
            return {
                'success': False,
                'error': f'合并失败: {str(e)}'
            }

    def get_merge_summary(self, file_paths: List[str]) -> Dict:
        """
        获取合并预览信息

        Args:
            file_paths: SHP文件路径列表

        Returns:
            Dict: 预览信息
        """
        try:
            files_info = []
            total_features = 0

            for file_path in file_paths:
                info = self.validate_shapefile(file_path)
                files_info.append(info)

                if info['success']:
                    total_features += info['file_info']['feature_count']

            compatibility = self.check_compatibility(files_info)

            return {
                'files_count': len(file_paths),
                'valid_files': sum(1 for info in files_info if info['success']),
                'total_features': total_features,
                'compatible': compatibility['compatible'],
                'merge_type': compatibility['merge_type'],
                'common_crs': compatibility['common_crs'],
                'files_info': files_info,
                'compatibility': compatibility
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'获取预览信息失败: {str(e)}'
            }


if __name__ == "__main__":
    # 测试代码
    merger = ShapefileMerger()

    # 示例用法
    test_files = [
        "path/to/file1.shp",
        "path/to/file2.shp"
    ]

    # 获取预览信息
    summary = merger.get_merge_summary(test_files)
    print("合并预览:", summary)

    # 执行合并
    if summary.get('compatible', False):
        result = merger.merge_shapefiles(test_files, "output/merged.shp")
        print("合并结果:", result)