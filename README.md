# CS2饰品价格爬虫 - 悠悠有品

自动采集悠悠有品网站的CS2饰品售价和租价信息，计算租售比并输出到CSV文件。

## 功能特点

- 自动采集指定饰品的售价和租价
- 支持5种磨损度：崭新出厂、略有磨损、久经沙场、破损不堪、战痕累累
- 支持普通版和暗金版两种版本
- 自动计算租售比
- 使用DrissionPage接管已有浏览器，有效绑过反爬检测
- 随机延迟模拟人工操作
- 完善的错误处理和重试机制
- 详细的日志记录

## 环境要求

- Python 3.8+
- Chrome浏览器
- Windows/macOS/Linux

## 安装

1. 安装依赖包：

```powershell
pip install -r requirements.txt
```

## 使用方法

### 第一步：准备商品列表

编辑 `items.csv` 文件，每行一个商品，格式为：

```
商品名, 普通版templateId, 暗金版templateId
```

示例：
```
爪子刀（★） | 人工染色 (崭新出厂), 57387, 60612
蝴蝶刀（★） | 澄澈之水, 62032, 62022
```

### 第二步：启动Chrome浏览器

必须使用远程调试端口启动Chrome：

**Windows (PowerShell):**
```powershell
# 先关闭所有Chrome窗口，然后运行：
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Windows (CMD):**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**Linux:**
```bash
google-chrome --remote-debugging-port=9222
```

### 第三步：运行爬虫

```powershell
python scraper.py
```

### 第四步：查看结果

结果保存在 `output/` 目录下，文件名格式为 `result_YYYYMMDD_HHMMSS.csv`

## 输出格式

| 商品名 | 版本 | 磨损度 | 售价 | 租价(天) | 租售比(%) |
|--------|------|--------|------|----------|-----------|
| 爪子刀 人工染色 | 普通 | 崭新出厂 | 2329 | 0.60 | 0.0258 |
| 爪子刀 人工染色 | 普通 | 略有磨损 | 787 | 0.68 | 0.0864 |

**租售比计算公式：** `租售比 = (日租金 / 售价) × 100%`

## 页面结构分析（开发者工具）

如果爬虫无法正确获取价格，可以运行页面结构分析工具：

```powershell
# 分析页面结构
python test_page_structure.py

# 交互式测试选择器
python test_page_structure.py -i
```

这会帮助你确定正确的CSS选择器，然后修改 `scraper.py` 中的 `_parse_prices_from_page` 方法。

## 配置说明

编辑 `config.py` 可以修改以下配置：

```python
# 浏览器配置
CHROME_DEBUG_PORT = 9222  # Chrome远程调试端口

# 反爬配置
MIN_DELAY = 3  # 最小延迟（秒）
MAX_DELAY = 8  # 最大延迟（秒）
MAX_RETRIES = 3  # 最大重试次数
PAGE_LOAD_TIMEOUT = 15  # 页面加载超时（秒）
```

## 项目结构

```
e:\AI\CS\
├── requirements.txt         # 依赖包
├── config.py                # 配置文件
├── items.csv                # 输入：商品列表
├── scraper.py               # 主爬虫程序
├── data_processor.py        # 数据处理模块
├── test_page_structure.py   # 页面结构分析工具
├── scraper.log              # 运行日志
├── output/                  # 输出目录
│   └── result_*.csv         # 结果文件
└── README.md                # 使用说明
```

## 常见问题

### Q: 连接浏览器失败？

A: 确保：
1. Chrome已经关闭所有窗口
2. 使用正确的命令启动Chrome（带 `--remote-debugging-port=9222`）
3. 端口9222没有被其他程序占用

### Q: 获取不到价格数据？

A: 
1. 运行 `test_page_structure.py` 分析页面结构
2. 检查网站是否改变了页面结构
3. 根据分析结果修改 `scraper.py` 中的选择器

### Q: 被网站限制访问？

A:
1. 增加 `config.py` 中的延迟时间
2. 减少单次运行的商品数量
3. 更换IP或等待一段时间后重试

## 注意事项

- 本工具仅供学习和个人使用
- 请遵守网站的服务条款和robots.txt
- 不要过于频繁地访问，以免给网站服务器造成压力
- 建议在非高峰时段运行

## 获取templateId

商品的templateId可以从商品页面URL中获取：

```
https://www.youpin898.com/market/goods-list?listType=10&templateId=57387&gameId=730
                                                            ↑
                                                      这就是templateId
```

## License

MIT License
