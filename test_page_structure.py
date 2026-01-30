"""
页面结构测试脚本
用于分析悠悠有品网站的页面结构，确定正确的CSS选择器
"""

import time
from DrissionPage import ChromiumPage, ChromiumOptions
import config


def test_page_structure():
    """测试页面结构并输出可用的选择器"""
    
    print("=" * 60)
    print("页面结构分析工具")
    print("=" * 60)
    print()
    print(f"请先启动Chrome并带上调试端口:")
    print(f'  chrome.exe --remote-debugging-port={config.CHROME_DEBUG_PORT}')
    print()
    
    input("准备好后按回车键开始...")
    
    # 连接浏览器
    try:
        co = ChromiumOptions().set_local_port(config.CHROME_DEBUG_PORT)
        page = ChromiumPage(co)
        print("\n成功连接到浏览器")
    except Exception as e:
        print(f"\n连接浏览器失败: {e}")
        return
    
    # 测试URL
    test_urls = [
        ("售价页面", f"{config.BASE_URL}?listType=10&templateId=57387&gameId=730"),
        ("租价页面", f"{config.BASE_URL}?listType=30&templateId=57387&gameId=730"),
    ]
    
    for name, url in test_urls:
        print(f"\n{'=' * 60}")
        print(f"分析 {name}: {url}")
        print("=" * 60)
        
        page.get(url)
        time.sleep(5)  # 等待页面完全加载
        
        # 分析页面结构
        analyze_page(page)
        
        input("\n按回车键继续下一个页面...")


def analyze_page(page):
    """分析页面结构"""
    
    print("\n1. 查找磨损度相关元素...")
    wear_keywords = ['崭新出厂', '略有磨损', '久经沙场', '破损不堪', '战痕累累']
    
    for keyword in wear_keywords:
        try:
            elements = page.eles(f'text:{keyword}')
            if elements:
                print(f"   找到 '{keyword}': {len(elements)} 个元素")
                for i, ele in enumerate(elements[:3]):  # 只显示前3个
                    print(f"      [{i}] 标签: {ele.tag}, 类: {ele.attr('class')}")
                    # 尝试获取父元素信息
                    try:
                        parent = ele.parent()
                        print(f"          父元素: {parent.tag}, 类: {parent.attr('class')}")
                        print(f"          父元素文本: {parent.text[:100]}..." if len(parent.text) > 100 else f"          父元素文本: {parent.text}")
                    except:
                        pass
        except Exception as e:
            print(f"   查找 '{keyword}' 时出错: {e}")
    
    print("\n2. 查找价格相关元素...")
    price_selectors = [
        '[class*="price"]',
        '[class*="Price"]',
        '.price',
        '.item-price',
        '[class*="money"]',
        '[class*="yuan"]',
    ]
    
    for selector in price_selectors:
        try:
            elements = page.eles(f'css:{selector}')
            if elements:
                print(f"   选择器 '{selector}': 找到 {len(elements)} 个元素")
                for i, ele in enumerate(elements[:5]):  # 只显示前5个
                    text = ele.text.strip()
                    if text:
                        print(f"      [{i}] 文本: {text[:50]}...")
        except Exception as e:
            print(f"   选择器 '{selector}' 出错: {e}")
    
    print("\n3. 查找包含¥符号的元素...")
    try:
        # 使用XPath查找包含¥的文本
        elements = page.eles('xpath://*[contains(text(), "¥")]')
        if elements:
            print(f"   找到 {len(elements)} 个包含¥的元素")
            for i, ele in enumerate(elements[:10]):
                print(f"      [{i}] 标签: {ele.tag}, 类: {ele.attr('class')}, 文本: {ele.text[:50]}")
    except Exception as e:
        print(f"   查找¥元素时出错: {e}")
    
    print("\n4. 查找商品列表容器...")
    list_selectors = [
        '[class*="goods"]',
        '[class*="Goods"]',
        '[class*="list"]',
        '[class*="List"]',
        '[class*="item"]',
        '[class*="Item"]',
    ]
    
    for selector in list_selectors:
        try:
            elements = page.eles(f'css:{selector}')
            if elements:
                print(f"   选择器 '{selector}': 找到 {len(elements)} 个元素")
        except:
            pass
    
    print("\n5. 查找标签页/Tab元素...")
    tab_selectors = [
        '[class*="tab"]',
        '[class*="Tab"]',
        '[role="tab"]',
        '.nav-item',
        '[class*="nav"]',
    ]
    
    for selector in tab_selectors:
        try:
            elements = page.eles(f'css:{selector}')
            if elements:
                print(f"   选择器 '{selector}': 找到 {len(elements)} 个元素")
                for i, ele in enumerate(elements[:5]):
                    text = ele.text.strip()
                    if text:
                        print(f"      [{i}] 文本: {text[:30]}")
        except:
            pass
    
    print("\n6. 保存页面HTML供分析...")
    try:
        html_file = "page_structure.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(page.html)
        print(f"   页面HTML已保存到: {html_file}")
    except Exception as e:
        print(f"   保存HTML失败: {e}")


def interactive_test():
    """交互式测试模式"""
    
    print("\n交互式测试模式")
    print("输入CSS选择器或XPath来测试，输入'quit'退出")
    print()
    
    try:
        co = ChromiumOptions().set_local_port(config.CHROME_DEBUG_PORT)
        page = ChromiumPage(co)
    except Exception as e:
        print(f"连接浏览器失败: {e}")
        return
    
    while True:
        selector = input("\n输入选择器 (css:xxx 或 xpath:xxx): ").strip()
        
        if selector.lower() == 'quit':
            break
        
        try:
            if selector.startswith('css:') or selector.startswith('xpath:'):
                elements = page.eles(selector)
            else:
                # 默认当作CSS选择器
                elements = page.eles(f'css:{selector}')
            
            print(f"找到 {len(elements)} 个元素")
            for i, ele in enumerate(elements[:10]):
                print(f"  [{i}] 标签: {ele.tag}, 类: {ele.attr('class')}")
                print(f"       文本: {ele.text[:100] if ele.text else '(空)'}")
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '-i':
        interactive_test()
    else:
        test_page_structure()
