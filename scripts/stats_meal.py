# -*- coding: utf-8 -*-
"""
饮食记录 - 阶段性营养统计脚本
读取 meal_log.json，按日/周/月统计营养摄入
"""
import json, argparse, datetime, sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import defaultdict

def parse_date(ts):
    """解析ISO格式时间戳，返回date对象"""
    try:
        # 处理格式: "2026-04-15T12:30:00+08:00"
        ts = ts.split('T')[0]
        return datetime.date.fromisoformat(ts)
    except:
        return None

def load_meal_log(path):
    """加载meal_log.json（JSON Lines格式）"""
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except:
                    pass
    return records

def load_user_profile(path):
    """加载用户档案"""
    if __import__('os').path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def daily_recommend(profile):
    """基于用户档案计算每日推荐摄入量"""
    # 默认推荐值（中国居民膳食指南2022，成年人均值）
    defaults = {
        'energy_kcal': 2000,
        'protein_g': 60,
        'fat_g': 65,
        'carbs_g': 300,
        'fiber_g': 25,
        'sodium_mg': 2000,  # 约5g盐
        'calcium_mg': 800,
        'iron_mg': 12,
        'zinc_mg': 12,
        'vitamin_c_mg': 100,
    }

    if not profile:
        return defaults

    # 根据活动水平调整热量
    activity = profile.get('activity_level', 'moderate')
    activity_multipliers = {
        'sedentary': 0.85,
        'light': 1.0,
        'moderate': 1.15,
        'heavy': 1.35,
    }
    mult = activity_multipliers.get(activity, 1.0)

    # 性别差异
    sex = profile.get('gender', 'male')
    if sex == 'female':
        defaults['energy_kcal'] = 1800 * mult
    else:
        defaults['energy_kcal'] = 2200 * mult

    # BMI调整（粗略）
    height_m = profile.get('height_cm', 170) / 100
    weight = profile.get('weight_kg', 65)
    bmi = weight / (height_m ** 2)
    if bmi < 18.5:
        defaults['energy_kcal'] *= 1.1  # 偏瘦，增加
    elif bmi >= 24:
        defaults['energy_kcal'] *= 0.9  # 超重，减少

    # 目标调整
    goal = profile.get('health_goal', 'maintain')
    if goal == 'lose_weight':
        defaults['energy_kcal'] *= 0.8
    elif goal == 'gain_weight':
        defaults['energy_kcal'] *= 1.15

    return defaults

def aggregate_records(records, days=None, start_date=None, end_date=None):
    """按日期聚合营养数据"""
    if start_date and end_date:
        period_records = [r for r in records
                          if start_date <= (parse_date(r.get('timestamp','')) or datetime.date.min) <= end_date]
    elif days:
        end = end_date or datetime.date.today()
        start = start_date or (end - datetime.timedelta(days=days-1))
        period_records = [r for r in records
                          if start <= (parse_date(r.get('timestamp','')) or datetime.date.min) <= end]
    else:
        period_records = records

    # 按日期分组
    by_date = defaultdict(list)
    for r in period_records:
        d = parse_date(r.get('timestamp',''))
        if d:
            by_date[d].append(r)

    # 计算每日汇总
    daily_totals = []
    for date, day_records in sorted(by_date.items()):
        total = defaultdict(float)
        for rec in day_records:
            t = rec.get('total', {})
            for k, v in t.items():
                if isinstance(v, (int, float)):
                    total[k] += v
        daily_totals.append({'date': date.isoformat(), 'total': dict(total), 'meals': len(day_records)})

    return daily_totals, period_records

def compute_stats(daily_totals, total_records, days):
    """计算统计指标"""
    if not daily_totals:
        return {}

    # 总天数（有记录的天数）
    actual_days = len(daily_totals)
    total_cal = sum(d['total'].get('energy_kcal', 0) for d in daily_totals)
    total_protein = sum(d['total'].get('protein_g', 0) for d in daily_totals)
    total_fat = sum(d['total'].get('fat_g', 0) for d in daily_totals)
    total_carbs = sum(d['total'].get('carbs_g', 0) for d in daily_totals)
    total_sodium = sum(d['total'].get('sodium_mg', 0) for d in daily_totals)
    total_fiber = sum(d['total'].get('fiber_g', 0) for d in daily_totals)
    total_calcium = sum(d['total'].get('calcium_mg', 0) for d in daily_totals)
    total_iron = sum(d['total'].get('iron_mg', 0) for d in daily_totals)

    avg_cal = total_cal / actual_days if actual_days else 0
    avg_protein = total_protein / actual_days if actual_days else 0
    avg_fat = total_fat / actual_days if actual_days else 0
    avg_carbs = total_carbs / actual_days if actual_days else 0

    # 计算供能比
    total_macro_cal = avg_protein * 4 + avg_fat * 9 + avg_carbs * 4
    protein_pct = (avg_protein * 4 / total_macro_cal * 100) if total_macro_cal > 0 else 0
    fat_pct = (avg_fat * 9 / total_macro_cal * 100) if total_macro_cal > 0 else 0
    carbs_pct = (avg_carbs * 4 / total_macro_cal * 100) if total_macro_cal > 0 else 0

    return {
        'actual_days': actual_days,
        'total_meals': total_records,
        'avg_cal': avg_cal,
        'avg_protein': avg_protein,
        'avg_fat': avg_fat,
        'avg_carbs': avg_carbs,
        'protein_pct': protein_pct,
        'fat_pct': fat_pct,
        'carbs_pct': carbs_pct,
        'avg_sodium': total_sodium / actual_days if actual_days else 0,
        'avg_fiber': total_fiber / actual_days if actual_days else 0,
        'avg_calcium': total_calcium / actual_days if actual_days else 0,
        'avg_iron': total_iron / actual_days if actual_days else 0,
    }

def main():
    parser = argparse.ArgumentParser(description='饮食统计')
    parser.add_argument('--data', '-d', type=str, required=True, help='meal_log.json路径')
    parser.add_argument('--profile', '-p', type=str, default='', help='user_profile.json路径')
    parser.add_argument('--days', type=int, default=7, help='统计天数')
    parser.add_argument('--start', type=str, default='', help='开始日期 YYYY-MM-DD')
    parser.add_argument('--end', type=str, default='', help='结束日期 YYYY-MM-DD')
    parser.add_argument('--json-out', action='store_true', help='JSON格式输出')
    args = parser.parse_args()

    if not __import__('os').path.exists(args.data):
        print(json.dumps({'error': 'meal_log.json不存在，请先记录饮食'}))
        return

    records = load_meal_log(args.data)
    profile = load_user_profile(args.profile) if args.profile else {}

    start_date = datetime.date.fromisoformat(args.start) if args.start else None
    end_date = datetime.date.fromisoformat(args.end) if args.end else datetime.date.today()

    daily_totals, period_records = aggregate_records(records, days=args.days, start_date=start_date, end_date=end_date)
    stats = compute_stats(daily_totals, len(period_records), args.days)
    recs = daily_recommend(profile)

    if args.json_out:
        out = {
            'period': f'{start_date or (end_date - datetime.timedelta(days=args.days))} ~ {end_date}',
            'days': args.days,
            'stats': stats,
            'recommendations': recs,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    # 文本输出
    period_str = f'{start_date or (end_date - datetime.timedelta(days=args.days))} ~ {end_date}'
    print(f"\n📊 【最近{args.days}天饮食统计】{period_str}")
    print(f"  记录天数: {stats.get('actual_days', 0)}天，共{stats.get('total_meals', 0)}餐")

    print(f"\n热量：日均 {stats.get('avg_cal',0):.0f} kcal（日总量 {sum(d['total'].get('energy_kcal',0) for d in daily_totals):.0f} kcal）")
    delta = stats.get('avg_cal', 0) - recs.get('energy_kcal', 2000)
    if abs(delta) < 100:
        print(f"  → 与推荐值差距约 {delta:.0f} kcal，基本正常")
    elif delta > 0:
        print(f"  → ⚠️ 超出推荐约 {delta:.0f} kcal，注意控制")
    else:
        print(f"  → 偏低约 {-delta:.0f} kcal")

    print(f"\n营养素供能比：")
    print(f"  蛋白质 {stats.get('protein_pct',0):.0f}%（日均 {stats.get('avg_protein',0):.1f}g）  {'✅' if 15<=stats.get('protein_pct',0)<=25 else '⚠️'} 建议15-25%")
    print(f"  脂肪 {stats.get('fat_pct',0):.0f}%（日均 {stats.get('avg_fat',0):.1f}g）  {'✅' if 20<=stats.get('fat_pct',0)<=30 else '⚠️'} 建议20-30%")
    print(f"  碳水 {stats.get('carbs_pct',0):.0f}%（日均 {stats.get('avg_carbs',0):.1f}g）  {'✅' if 45<=stats.get('carbs_pct',0)<=65 else '⚠️'} 建议45-65%")

    print(f"\n矿物质（每日）：")
    print(f"  钠 {stats.get('avg_sodium',0):.0f}mg  {'⚠️' if stats.get('avg_sodium',0) > 2000 else '✅'}（建议<2000mg，约<5g盐）")
    print(f"  钙 {stats.get('avg_calcium',0):.0f}mg  {'⚠️' if stats.get('avg_calcium',0) < 800 else '✅'}（建议800mg/天）")
    print(f"  铁 {stats.get('avg_iron',0):.1f}mg  {'✅' if stats.get('avg_iron',0) >= 12 else '⚠️'}（建议12mg/天）")

    print(f"\n膳食纤维：日均 {stats.get('avg_fiber',0):.1f}g  {'✅' if stats.get('avg_fiber',0) >= 25 else '⚠️'}（建议25g/天）")

if __name__ == '__main__':
    main()
