# diet-log

OpenClaw Diet Logging & Nutrition Analysis Skill

## Features

- **Nutrition Analysis**: Calculate calories, protein, fat, carbs, minerals, and vitamins per meal based on the foodwake nutrition database (1,643 food items)
- **Diet Logging**: Automatically saves to `meal_log.json` (JSON Lines format)
- **Periodic Statistics**: Support for daily/weekly/monthly nutrition intake trend analysis
- **Personalized Assessment**: Recommendations based on Chinese Dietary Reference Intakes (DRIs 2013)

## Data Files

| File | Description |
|------|-------------|
| `references/food-table.json` | foodwake nutrition data (1,643 items, 2.7MB) |
| `references/dris_reference.json` | Chinese DRIs 2013 (21 age/gender groups) |
| `references/oils_seasonings.json` | Cooking oil and seasoning nutrition reference |

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/query_food.py` | Query food nutrition data with fuzzy matching |
| `scripts/stats_meal.py` | Periodic nutrition statistics |

## Usage

```bash
# Query food nutrition
python scripts/query_food.py -d references/food-table.json -q "noodles" --top-k 3 --json-out

# Statistics for the last 7 days
python scripts/stats_meal.py -d meal_log.json -p user_profile.json --days 7
```

## Data Sources

- Food data: [foodwake](https://github.com/LuckyHookin/foodwake) (based on www.foodwake.com)
- DRIs standard: Chinese Nutrition Society, "Chinese Dietary Reference Intakes (2013 Revision)"
- Cooking oils/seasonings: Compiled from China Food Composition Tables

## License

Apache-2.0
