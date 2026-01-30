"""
CS2饰品爬虫配置文件
"""

# 浏览器配置
CHROME_DEBUG_PORT = 9222  # Chrome远程调试端口
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Chrome浏览器路径
CHROME_USER_DATA_DIR = r"C:\temp\chrome_debug"  # Chrome用户数据目录
AUTO_START_CHROME = True  # 是否自动启动Chrome浏览器

# URL模板
BASE_URL = "https://www.youpin898.com/market/goods-list"
GAME_ID = 730  # CS2游戏ID

# listType参数
LIST_TYPE_SELL = 10  # 出售页面
LIST_TYPE_RENT = 30  # 出租页面

# 磨损度类型（中英文对照）
WEAR_LEVELS = {
    '崭新出厂': 'Factory New',
    '略有磨损': 'Minimal Wear', 
    '久经沙场': 'Field-Tested',
    '破损不堪': 'Well-Worn',
    '战痕累累': 'Battle-Scarred'
}

# 反爬配置
MIN_DELAY = 1  # 最小延迟（秒）
MAX_DELAY = 3  # 最大延迟（秒）
PAGE_LOAD_TIMEOUT = 10  # 页面加载超时（秒）

# 文件路径
INPUT_CSV = "items.csv"  # 输入文件
OUTPUT_DIR = "output"  # 输出目录

# 日志配置
LOG_FILE = "scraper.log"
LOG_LEVEL = "INFO"
