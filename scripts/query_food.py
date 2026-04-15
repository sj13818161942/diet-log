# -*- coding: utf-8 -*-
"""
饮食记录 - 食物营养数据查询脚本
查询 food-table.json (JSON Lines格式) 并返回匹配食物的营养数据
"""
import json, re, sys, argparse, os
from difflib import SequenceMatcher

# Force UTF-8 output on all platforms (especially Windows)
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

DATA_FILE = None
OILS_AND_SEASONINGS_FILE = None

def parse_value(s):
    """从营养值字符串中提取数值，如 '37千卡' -> 37.0, '1.5克' -> 1.5"""
    if not s or s in ('克', '毫克', '微克', '千卡', '%', ''):
        return 0.0
    m = re.search(r'([\d.]+)', str(s))
    return float(m.group(1)) if m else 0.0

def load_data(data_path):
    """加载JSON Lines格式的食物数据"""
    items = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except:
                    pass
    return items

def load_oils_seasonings(path):
    """加载烹调油和佐料参考数据"""
    if path and __import__('os').path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def normalize(s):
    """用于模糊匹配的规范化字符串"""
    return re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', str(s)).lower()

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def search_food(query, data, top_k=5, threshold=0.4):
    """
    搜索食物，支持：
    1. 精确/包含匹配
    2. 同类推荐
    3. 模糊匹配
    返回 top_k 个最可能匹配的食物及其相似度
    """
    query_n = normalize(query)
    results = []

    # 第一轮：名称包含查询词
    for i, item in enumerate(data):
        name = item.get('name', '')
        nickname = item.get('nickname', '')
        if query_n in normalize(name) or query_n in normalize(nickname):
            results.append((i, item, 1.0))

    # 第二轮：模糊匹配
    if len(results) < top_k:
        for i, item in enumerate(data):
            if any(i == r[0] for r in results):
                continue
            name = item.get('name', '')
            sim = similarity(query, name)
            if sim >= threshold:
                results.append((i, item, sim))

    # 第三轮：同类食物推荐（按类型）
    if len(results) < top_k:
        # 找出已有结果的类型
        matched_types = set(r[1].get('type', '') for r in results)
        for i, item in enumerate(data):
            if any(i == r[0] for r in results):
                continue
            ftype = item.get('type', '')
            if ftype in matched_types:
                results.append((i, item, 0.3))

    # 按相似度排序，同分时优先选择名称更短（更精确）的匹配
    results = sorted(results, key=lambda x: (-x[2], len(x[1].get('name', ''))))[:top_k]
    return results

def format_food_info(item):
    """将食物营养数据格式化为易读字符串"""
    info = item.get('info', {})
    lines = []
    lines.append(f"【{item.get('name', '未知')}】(类型: {item.get('type', '未知')})")
    lines.append(f"  热量: {info.get('能量', 'N/A')}")
    for key in ['蛋白质', '脂肪', '碳水化合物', '粗纤维']:
        lines.append(f"  {key}: {info.get(key, 'N/A')}")
    # 脂肪酸
    for key in ['单不饱和脂肪酸', '多不饱和脂肪酸', '胆固醇']:
        v = info.get(key, 'N/A')
        if v and v not in ('克', '毫克', 'N/A'):
            lines.append(f"  {key}: {v}")
    # 矿物质
    minerals = ['钙', '磷', '钾', '钠', '镁', '铁', '锌', '铜', '锰', '硒']
    for key in minerals:
        v = info.get(key, '')
        if v and v not in ('毫克', '微克', ''):
            lines.append(f"  {key}: {v}")
    # 维生素
    vitamins = ['维生素A', '维生素C', '维生素D', '维生素E', '维生素K',
                '维生素B1（硫胺素）', '维生素B2（核黄素）', '维生素B3（烟酸）',
                '维生素B6', '维生素B12', '维生素B9（叶酸）']
    for key in vitamins:
        v = info.get(key, '')
        if v and v not in ('毫克', '微克', ''):
            lines.append(f"  {key}: {v}")
    return '\n'.join(lines)

def get_food_nutrition(item, macros_only=False):
    """提取营养数值，返回数值字典（单位统一为克/毫克/微克）"""
    info = item.get('info', {})
    result = {
        'name': item.get('name', ''),
        'type': item.get('type', ''),
        'energy_kcal': parse_value(info.get('能量', '0')),
        'protein_g': parse_value(info.get('蛋白质', '0')),
        'fat_g': parse_value(info.get('脂肪', '0')),
        'carbs_g': parse_value(info.get('碳水化合物', '0')),
        'fiber_g': parse_value(info.get('粗纤维', '0')),
        # 脂肪酸
        'monounsaturated_fat_g': parse_value(info.get('单不饱和脂肪酸', '0')),
        'polyunsaturated_fat_g': parse_value(info.get('多不饱和脂肪酸', '0')),
        'trans_fat_g': parse_value(info.get('反式脂肪酸', '0')),
        'cholesterol_mg': parse_value(info.get('胆固醇', '0')),
        # 矿物质
        'calcium_mg': parse_value(info.get('钙', '0')),
        'phosphorus_mg': parse_value(info.get('磷', '0')),
        'potassium_mg': parse_value(info.get('钾', '0')),
        'sodium_mg': parse_value(info.get('钠', '0')),
        'magnesium_mg': parse_value(info.get('镁', '0')),
        'iron_mg': parse_value(info.get('铁', '0')),
        'zinc_mg': parse_value(info.get('锌', '0')),
        'copper_mg': parse_value(info.get('铜', '0')),
        'manganese_mg': parse_value(info.get('锰', '0')),
        'selenium_mg': parse_value(info.get('硒', '0')),
        # 维生素
        'vitamin_a_mcg': parse_value(info.get('维生素A', '0')),
        'vitamin_c_mg': parse_value(info.get('维生素C', '0')),
        'vitamin_d_mcg': parse_value(info.get('维生素D', '0')),
        'vitamin_e_mg': parse_value(info.get('维生素E', '0')),
        'vitamin_k_mcg': parse_value(info.get('维生素K', '0')),
        'vitamin_b1_mg': parse_value(info.get('维生素B1（硫胺素）', '0')),
        'vitamin_b2_mg': parse_value(info.get('维生素B2（核黄素）', '0')),
        'vitamin_b3_mg': parse_value(info.get('维生素B3（烟酸）', '0')),
        'vitamin_b6_mg': parse_value(info.get('维生素B6', '0')),
        'vitamin_b12_mcg': parse_value(info.get('维生素B12', '0')),
        'folate_mcg': parse_value(info.get('维生素B9（叶酸）', '0')),
        # 氨基酸（部分食物有）
        'leucine_mg': parse_value(info.get('亮氨酸', '0')),
        'lysine_mg': parse_value(info.get('赖氨酸', '0')),
    }
    return result

def main():
    parser = argparse.ArgumentParser(description='食物营养数据查询')
    parser.add_argument('--query', '-q', type=str, help='搜索关键词')
    parser.add_argument('--data', '-d', type=str, required=True, help='食物数据JSON Lines文件路径')
    parser.add_argument('--oils', '-o', type=str, default='', help='油和佐料参考数据文件')
    parser.add_argument('--top-k', '-k', type=int, default=5, help='返回结果数量')
    parser.add_argument('--json-out', action='store_true', help='输出JSON格式')
    parser.add_argument('--nutrition-only', action='store_true', help='只输出营养数值')
    args = parser.parse_args()

    data = load_data(args.data)
    oils_seasons = load_oils_seasonings(args.oils) if args.oils else {}

    # 如果查询油/调味品，先查专门的数据
    if oils_seasons and args.query:
        q = args.query.strip()
        # oils_seasonings.json 结构: {"油类": [{"name":..., "aliases":[], "info":{}}], "调味品类": [...]}
        for cat_key, cat_data in oils_seasons.items():
            if not isinstance(cat_data, list):
                continue
            for item in cat_data:
                if not isinstance(item, dict):
                    continue
                aliases = item.get('aliases', [])
                if not isinstance(aliases, list):
                    aliases = []
                if q in item.get('name', '') or any(q in str(a) for a in aliases):
                    if args.json_out:
                        out = get_food_nutrition({'name': item['name'], 'type': cat_key, 'info': item.get('info', {})})
                        out['similarity'] = 1.0
                        out['source'] = 'oils_seasonings'
                        print(json.dumps([out], ensure_ascii=True))
                    else:
                        print(f"【{item['name']}】(类型: {cat_key})")
                        for k, v in list(item.get('info', {}).items())[:10]:
                            print(f"  {k}: {v}")
                    return

    if not args.query:
        print("请提供 --query 参数")
        return

    results = search_food(args.query, data, top_k=args.top_k)

    if not results:
        print("未找到匹配的食物，请尝试更通用的名称。")
        return

    if args.json_out:
        out_results = []
        for _, item, sim in results:
            n = get_food_nutrition(item)
            n['similarity'] = round(sim, 3)
            n['source'] = 'foodwake'
            out_results.append(n)
        print(json.dumps(out_results, ensure_ascii=True, indent=2))
    elif args.nutrition_only:
        for _, item, sim in results:
            n = get_food_nutrition(item)
            print(f"{item.get('name', '')} (相似度:{sim:.2f}): 热量{n['energy_kcal']}kcal, 蛋白质{n['protein_g']}g, 脂肪{n['fat_g']}g, 碳水{n['carbs_g']}g")
    else:
        for rank, (_, item, sim) in enumerate(results, 1):
            print(f"\n--- 匹配 {rank} (相似度: {sim:.2f}) ---")
            print(format_food_info(item))

if __name__ == '__main__':
    main()
