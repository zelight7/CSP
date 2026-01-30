"""
数据处理模块
负责读取输入CSV、计算租售比、输出结果
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
import config


class Item:
    """商品数据类"""
    def __init__(self, name: str, normal_id: str, dark_gold_id: str):
        self.name = name.strip()
        self.normal_id = normal_id.strip()
        self.dark_gold_id = dark_gold_id.strip()
    
    def __repr__(self):
        return f"Item({self.name}, normal={self.normal_id}, dark_gold={self.dark_gold_id})"


class PriceRecord:
    """价格记录类"""
    def __init__(self, item_name: str, version: str, wear_level: str, 
                 sell_price: Optional[float] = None, rent_price: Optional[float] = None):
        self.item_name = item_name
        self.version = version  # "普通" 或 "暗金"
        self.wear_level = wear_level
        self.sell_price = sell_price
        self.rent_price = rent_price
    
    @property
    def rent_ratio(self) -> Optional[float]:
        """计算租售比（百分比）"""
        if self.sell_price and self.rent_price and self.sell_price > 0:
            return (self.rent_price / self.sell_price) * 100
        return None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            '商品名': self.item_name,
            '版本': self.version,
            '磨损度': self.wear_level,
            '售价': self.sell_price if self.sell_price else '',
            '租价(天)': self.rent_price if self.rent_price else '',
            '租售比(%)': f"{self.rent_ratio:.4f}" if self.rent_ratio else ''
        }


def read_items_csv(filepath: str = None) -> List[Item]:
    """
    读取商品CSV文件
    
    CSV格式：商品名, 普通版templateId, 暗金版templateId
    例如：爪子刀（★） | 人工染色 (崭新出厂), 57387, 60612
    
    Args:
        filepath: CSV文件路径，默认使用config中的配置
    
    Returns:
        Item对象列表
    """
    if filepath is None:
        filepath = config.INPUT_CSV
    
    items = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                name = row[0].strip()
                normal_id = row[1].strip()
                dark_gold_id = row[2].strip()
                items.append(Item(name, normal_id, dark_gold_id))
    
    return items


def save_results_csv(records: List[PriceRecord], output_dir: str = None) -> str:
    """
    保存结果到CSV文件
    
    Args:
        records: PriceRecord列表
        output_dir: 输出目录，默认使用config中的配置
    
    Returns:
        输出文件路径
    """
    if output_dir is None:
        output_dir = config.OUTPUT_DIR
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成带日期的文件名
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f"result_{date_str}.csv")
    
    # 写入CSV
    fieldnames = ['商品名', '版本', '磨损度', '售价', '租价(天)', '租售比(%)']
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
    
    return output_file


def build_url(template_id: str, list_type: int) -> str:
    """
    构建商品页面URL
    
    Args:
        template_id: 商品模板ID
        list_type: 页面类型（10=售价，30=租价）
    
    Returns:
        完整URL
    """
    return f"{config.BASE_URL}?listType={list_type}&templateId={template_id}&gameId={config.GAME_ID}"


def parse_price(price_text: str) -> Optional[float]:
    """
    解析价格文本
    
    支持格式：
    - ¥2329
    - ¥0.60/天
    - 2329.00
    
    Args:
        price_text: 价格文本
    
    Returns:
        价格数值，解析失败返回None
    """
    if not price_text:
        return None
    
    # 移除货币符号、空格和"/天"后缀
    cleaned = price_text.replace('¥', '').replace('/天', '').replace(',', '').strip()
    
    try:
        return float(cleaned)
    except ValueError:
        return None


if __name__ == "__main__":
    # 测试读取CSV
    items = read_items_csv()
    print(f"读取到 {len(items)} 个商品:")
    for item in items:
        print(f"  - {item}")
        print(f"    普通版URL: {build_url(item.normal_id, config.LIST_TYPE_SELL)}")
        print(f"    暗金版URL: {build_url(item.dark_gold_id, config.LIST_TYPE_SELL)}")
