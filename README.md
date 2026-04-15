# diet-log

OpenClaw 饮食记录与营养分析技能

## 功能

- 营养分析：基于 foodwake 食物数据库（1643条数据）计算每餐热量、蛋白质、脂肪、碳水、矿物质、维生素
- 饮食记录：自动保存到 meal_log.json（JSON Lines 格式）
- 阶段性统计：支持按日/周/月统计营养摄入趋势
- 个性化评估：基于《中国居民膳食营养素参考摄入量（DRIs 2013）》给出推荐对比

## 数据文件

| 文件 | 说明 |
|------|------|
| `references/food-table.json` | foodwake 食物营养数据（1643条，2.7MB） |
| `references/dris_reference.json` | 中国居民膳食营养素参考摄入量 DRIs 2013（21个年龄组） |
| `references/oils_seasonings.json` | 烹调油和调料营养参考数据 |

## 脚本

| 脚本 | 说明 |
|------|------|
| `scripts/query_food.py` | 查询食物营养数据，支持模糊匹配 |
| `scripts/stats_meal.py` | 阶段性营养统计 |

## 使用方法

```bash
# 查询食物营养
python scripts/query_food.py -d references/food-table.json -q "面条" --top-k 3 --json-out

# 统计最近7天饮食
python scripts/stats_meal.py -d meal_log.json -p user_profile.json --days 7
```

## 数据来源

- 食物数据：[foodwake](https://github.com/LuckyHookin/foodwake)（基于 www.foodwake.com）
- DRIs 标准：中国营养学会《中国居民膳食营养素参考摄入量（2013版）》
- 烹调油/调料：基于中国食物成分表整理

## 许可证

Apache-2.0
