"""
CS2饰品爬虫主程序
使用DrissionPage自动化采集悠悠有品网站的饰品价格
"""

import random
import time
import logging
import re
import subprocess
import os
from typing import Dict, List, Optional, Tuple

from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage.errors import ElementNotFoundError

import config
from data_processor import (
    Item, PriceRecord, read_items_csv, save_results_csv, 
    build_url, parse_price
)


# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class YoupinScraper:
    """悠悠有品爬虫类"""
    
    def __init__(self, use_existing_browser: bool = None):
        """
        初始化爬虫
        
        Args:
            use_existing_browser: 是否接管已打开的浏览器
                             None: 根据config.AUTO_START_CHROME自动决定
                             True: 连接现有浏览器
                             False: 自动启动新浏览器
        """
        if use_existing_browser is None:
            use_existing_browser = not config.AUTO_START_CHROME
        
        self.page = None
        self.use_existing_browser = use_existing_browser
        self.records: List[PriceRecord] = []
    
    def start_chrome(self) -> bool:
        """
        自动启动Chrome浏览器
        
        Returns:
            是否启动成功
        """
        try:
            logger.info("正在启动Chrome浏览器...")
            
            # 确保用户数据目录存在
            os.makedirs(config.CHROME_USER_DATA_DIR, exist_ok=True)
            
            # 构建启动命令
            cmd = [
                config.CHROME_PATH,
                f"--remote-debugging-port={config.CHROME_DEBUG_PORT}",
                f"--user-data-dir={config.CHROME_USER_DATA_DIR}"
            ]
            
            # 启动Chrome（不等待窗口关闭）
            subprocess.Popen(cmd, shell=True)
            
            # 等待Chrome启动
            logger.info("等待Chrome启动...")
            time.sleep(3)
            
            logger.info(f"Chrome已启动 (端口: {config.CHROME_DEBUG_PORT})")
            return True
        except Exception as e:
            logger.error(f"启动Chrome失败: {e}")
            return False
    
    def connect(self) -> bool:
        """
        连接到浏览器
        
        Returns:
            是否连接成功
        """
        if self.use_existing_browser:
            # 只尝试连接现有浏览器，不启动新窗口
            max_retries = 3
            for retry in range(max_retries):
                try:
                    logger.info(f"尝试连接现有浏览器 (端口: {config.CHROME_DEBUG_PORT}, 重试: {retry+1}/{max_retries})")
                    
                    # 使用ChromiumOptions来指定端口，然后创建ChromiumPage
                    co = ChromiumOptions()
                    co.set_local_port(config.CHROME_DEBUG_PORT)
                    self.page = ChromiumPage(co)
                    logger.info(f"成功接管已有浏览器 (端口: {config.CHROME_DEBUG_PORT})")
                    return True
                except Exception as e:
                    logger.error(f"连接现有浏览器失败: {e}")
                    if retry < max_retries - 1:
                        logger.info(f"{2}秒后重试...")
                        time.sleep(2)
                    else:
                        logger.error("已达到最大重试次数，无法连接现有浏览器")
                        logger.error("=" * 60)
                        logger.error("请确保已正确启动Chrome并带有调试端口和用户数据目录:")
                        logger.error(f'  chrome.exe --remote-debugging-port={config.CHROME_DEBUG_PORT} --user-data-dir="{config.CHROME_USER_DATA_DIR}"')
                        logger.error("=" * 60)
                        logger.error("注意:")
                        logger.error("1. 必须添加 --user-data-dir 参数，否则DrissionPage无法正确连接")
                        logger.error("2. 用户数据目录路径可以自定义，但必须指定")
                        logger.error("3. 确保目录存在或有权限创建")
                        logger.error("4. 关闭所有Chrome窗口后重新启动")
                        logger.error("=" * 60)
                        return False
        else:
            # 自动启动新浏览器
            if config.AUTO_START_CHROME:
                logger.info("使用自定义配置启动Chrome浏览器...")
                if self.start_chrome():
                    # 启动成功后尝试连接
                    logger.info("Chrome已启动，正在连接...")
                    time.sleep(2)
                    try:
                        co = ChromiumOptions()
                        co.set_local_port(config.CHROME_DEBUG_PORT)
                        self.page = ChromiumPage(co)
                        logger.info(f"成功接管自动启动的浏览器 (端口: {config.CHROME_DEBUG_PORT})")
                        return True
                    except Exception as e:
                        logger.error(f"连接自动启动的浏览器失败: {e}")
                        return False
                else:
                    logger.error("自动启动Chrome失败")
                    return False
            else:
                logger.error("未启用自动启动Chrome功能")
                logger.error("请在config.py中设置 AUTO_START_CHROME = True")
                return False
    
    def random_delay(self, min_sec: float = None, max_sec: float = None):
        """随机延迟，模拟人工操作"""
        if min_sec is None:
            min_sec = config.MIN_DELAY
        if max_sec is None:
            max_sec = config.MAX_DELAY
        
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def get_prices_from_page(self, template_id: str, list_type: int) -> Dict[str, Optional[float]]:
        """
        从页面获取各磨损度的价格（不重试，失败直接返回）
        
        Args:
            template_id: 商品模板ID
            list_type: 页面类型（10=售价，30=租价）
        
        Returns:
            {磨损度: 价格} 字典
        """
        url = build_url(template_id, list_type)
        prices = {wear: None for wear in config.WEAR_LEVELS.keys()}
        
        try:
            logger.info(f"访问页面: {url}")
            self.page.get(url)
            
            # 等待价格元素出现
            self._wait_for_content()
            
            # 解析价格
            prices = self._parse_prices_from_page()
            
            if any(v is not None for v in prices.values()):
                logger.info(f"成功获取价格")
            else:
                logger.warning(f"未找到价格数据，跳过")
                
        except Exception as e:
            logger.error(f"获取价格失败: {e}，跳过")
        
        return prices
    
    def _wait_for_content(self):
        """等待页面内容加载"""
        try:
            # 等待磨损度按钮出现（btn-box___ 开头的class）
            self.page.wait.ele_displayed('css:[class^="btn-box___"]', timeout=5)
        except Exception as e:
            logger.debug(f"等待超时，继续解析: {e}")
    
    def _parse_prices_from_page(self) -> Dict[str, Optional[float]]:
        """
        从当前页面解析价格
        
        悠悠有品的页面结构：
        <div class="btn-box___eKv2g">崭新出厂<span class="price-unit___xhhFc">¥</span>4.50/天</div>
        <div class="btn-box___eKv2g">略有磨损<span class="price-unit___xhhFc">¥</span>2.78/天</div>
        
        售价页面格式：崭新出厂¥2329
        租价页面格式：崭新出厂¥0.60/天
        """
        prices = {wear: None for wear in config.WEAR_LEVELS.keys()}
        
        try:
            # 查找所有磨损度按钮（class以btn-box___开头）
            btn_elements = self.page.eles('css:[class^="btn-box___"]')
            
            if not btn_elements:
                # 备用选择器
                btn_elements = self.page.eles('css:[class*="btn-box"]')
            
            logger.debug(f"找到 {len(btn_elements)} 个按钮元素")
            
            for btn in btn_elements:
                try:
                    # 获取按钮的完整文本
                    btn_text = btn.text.strip()
                    
                    if not btn_text:
                        continue
                    
                    # 跳过StatTrak切换按钮（包含"★ StatTrak"）
                    if 'StatTrak' in btn_text or '★' in btn_text:
                        logger.debug(f"跳过StatTrak按钮: {btn_text}")
                        continue
                    
                    # 检查是否包含磨损度名称
                    for wear_name in config.WEAR_LEVELS.keys():
                        if wear_name in btn_text:
                            # 提取价格
                            # 格式可能是：崭新出厂¥2329 或 崭新出厂¥0.60/天
                            price = self._extract_price_from_text(btn_text)
                            if price is not None:
                                prices[wear_name] = price
                                logger.debug(f"解析到 {wear_name}: {price}")
                            break
                            
                except Exception as e:
                    logger.debug(f"解析按钮时出错: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"解析价格时出错: {e}")
        
        return prices
    
    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """
        从按钮文本中提取价格
        
        支持格式：
        - 崭新出厂¥2329
        - 崭新出厂¥0.60/天
        - 略有磨损¥787.5
        
        Args:
            text: 按钮文本
        
        Returns:
            价格数值
        """
        if not text:
            return None
        
        # 使用正则表达式提取¥后面的数字
        # 匹配 ¥ 或 ￥ 后面的数字（可能包含逗号和小数点）
        patterns = [
            r'[¥￥]\s*([\d,]+\.?\d*)',  # 匹配 ¥2329 或 ¥0.60
            r'([\d,]+\.?\d*)\s*/天',     # 匹配 0.60/天
            r'([\d,]+\.?\d*)\s*元',      # 匹配 2329元
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def scrape_item(self, item: Item) -> List[PriceRecord]:
        """
        爬取单个商品的所有价格数据
        
        Args:
            item: 商品对象
        
        Returns:
            PriceRecord列表
        """
        records = []
        
        # 处理普通版和暗金版
        versions = [
            ("普通", item.normal_id),
            ("暗金", item.dark_gold_id)
        ]
        
        for version_name, template_id in versions:
            if not template_id:
                continue
            
            logger.info(f"正在采集: {item.name} ({version_name}版)")
            
            # 获取售价
            sell_prices = self.get_prices_from_page(template_id, config.LIST_TYPE_SELL)
            self.random_delay()  # 请求后延迟，避免访问过快
            
            # 获取租价
            rent_prices = self.get_prices_from_page(template_id, config.LIST_TYPE_RENT)
            self.random_delay()  # 请求后延迟
            
            # 创建记录
            for wear_name in config.WEAR_LEVELS.keys():
                record = PriceRecord(
                    item_name=item.name,
                    version=version_name,
                    wear_level=wear_name,
                    sell_price=sell_prices.get(wear_name),
                    rent_price=rent_prices.get(wear_name)
                )
                records.append(record)
                
                # 打印调试信息
                if record.sell_price or record.rent_price:
                    logger.debug(f"  {wear_name}: 售价={record.sell_price}, 租价={record.rent_price}, 租售比={record.rent_ratio}")
        
        return records
    
    def run(self, items_csv: str = None) -> str:
        """
        运行爬虫主流程
        
        Args:
            items_csv: 输入CSV文件路径
        
        Returns:
            输出文件路径
        """
        # 读取商品列表
        items = read_items_csv(items_csv)
        logger.info(f"读取到 {len(items)} 个商品")
        
        if not items:
            logger.error("没有找到商品数据")
            return ""
        
        # 连接浏览器
        if not self.connect():
            logger.error("无法连接到浏览器")
            if not config.AUTO_START_CHROME:
                print("\n请先运行以下命令启动Chrome:")
                print(f'  chrome.exe --remote-debugging-port={config.CHROME_DEBUG_PORT} --user-data-dir="{config.CHROME_USER_DATA_DIR}"')
                print("\n或者在config.py中设置 AUTO_START_CHROME = True 以自动启动Chrome")
            return ""
        
        # 批量保存阈值
        BATCH_SIZE = 10
        output_file = ""
        
        # 爬取每个商品
        for i, item in enumerate(items):
            logger.info(f"处理商品 [{i+1}/{len(items)}]: {item.name}")
            
            try:
                records = self.scrape_item(item)
                self.records.extend(records)
            except Exception as e:
                logger.error(f"处理商品 {item.name} 时出错: {e}")
                continue
            
            # 批量保存
            if (i + 1) % BATCH_SIZE == 0 or (i + 1) == len(items):
                if self.records:
                    output_file = save_results_csv(self.records)
                    logger.info(f"已保存 {len(self.records)} 条记录到: {output_file}")
                    # 清空记录列表，准备下一批
                    self.records = []
            
            # 商品之间的延迟已在scrape_item中处理，不需要额外延迟
        
        if not output_file:
            logger.warning("没有采集到任何数据")
            return ""
        
        return output_file


def main():
    """主函数"""
    print("=" * 60)
    print("CS2饰品价格爬虫 - 悠悠有品")
    print("=" * 60)
    print()
    print("使用说明:")
    if config.AUTO_START_CHROME:
        print("程序将自动启动Chrome浏览器")
        print("请确保items.csv文件已准备好")
    else:
        print("请先启动Chrome并带上调试端口:")
        print(f'   chrome.exe --remote-debugging-port={config.CHROME_DEBUG_PORT} --user-data-dir="{config.CHROME_USER_DATA_DIR}"')
        print()
        print("2. 确保items.csv文件已准备好")
    print()
    
    input("准备好后按回车键开始...")
    
    scraper = YoupinScraper()
    output_file = scraper.run()
    
    if output_file:
        print(f"\n爬取完成! 结果保存在: {output_file}")
    else:
        print("\n爬取失败，请查看日志文件获取详细信息")


if __name__ == "__main__":
    main()
