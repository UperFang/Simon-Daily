# Zotero 知识库目录结构与归档规则

> Zotero 是原始文件的**唯一真相源**。本文件 = 目录结构快照 + 归档纪律，Simon 入库前必读。
> 结构快照日期：2026-09-05。重新生成目录树：`python3 scripts/zotero_lib.py --tree`

## 目录树（2026-09-05）

```
Electronics
  ├─ Analog Circuits
  ├─ DCDC&Power
  │   └─ LM5155
  └─ Power Electronics
FAE&Work
  ├─ 1- Report&achieve
  ├─ 10 - APP
  ├─ 11 - ASC
  ├─ 2- BMS
  │   ├─ 1- TI - BQ          ← BQ 系列器件专属资料
  │   ├─ 2- Others           ← BMS 领域跨器件的方法论/通用资料
  │   ├─ 3 - EIS Backup
  │   ├─ 4 - MCUless
  │   └─ 5- ADI&NXP          ← 竞品（ADI/NXP）BMS 资料
  ├─ 3- Traction Inverter
  │   ├─ 1 - GateDriver & Bias
  │   ├─ 2 - Sensor
  │   ├─ FUSA
  │   └─ LDC507x
  ├─ 4 - OBC
  ├─ 5 - Chasis
  │   ├─ BLDC/BSM
  │   └─ HVAC
  ├─ 6- ESS&EI
  ├─ Achieved
  ├─ Quality backup
  └─ Review
Reference
Technical Routine
  └─ EIS
工作 FAE（全空，疑似历史遗留）
  ├─ 1. BMS / 2. Traction Inverter / 3. 底盘 & 电机驱动 / 4. OBC & 电源 / 5. 通用技术文档 / 6. ESS & 储能
待归档（空）
拓展知识库
  ├─ 1. 数据科学 & ML
  └─ 2. 电子学教材
笔记
```

## 归档纪律

1. **结构神圣**：目录结构由 Wonder 维护，Simon **不得擅自增删改**；只能提改进建议，经同意后操作
2. **入库必分类**：写入具体**子分类路径**（`父/子`），不放父级兜底；找不到合适分类 → 停下来向 Wonder 提议新建，绝不硬塞或自创
3. **命名规范**：`[类型] 标题（编号/版本/日期）`
   - 类型词表：`Datasheet`、`Application Note`、`Reference Guide`、`User Guide`、`EVM User Guide`、`Report`、`Errata`、`Preliminary Datasheet`、`数据`、`培训`
   - 例：`[Datasheet] BQ79616-Q1（SLUSD77 ti.com公开版）`、`[Application Note] Open-Wire Detection in BMS Systems（SDAA369）`
4. **分类决策参考**：器件专属资料 → 该器件同名/对应目录（如 BQ 监测芯片 → `2- BMS/1- TI - BQ`，门驱 → `3- Traction Inverter/1 - GateDriver & Bias`）；跨器件方法论 → 对应领域 `Others`；竞品 → `5- ADI&NXP`
5. **不确定先问**：Simon 拿不准分类时问 Wonder，不猜

## 改进建议（提出待 Wonder 定夺，未获同意不动手）

- 「工作 FAE」与「FAE&Work」结构重复且全部为空 → 建议删除或合并，避免入库时产生歧义
- 「待归档」可正式启用为临时收件箱：不确定分类的资料先入此 + 提示 Wonder，每周清点归位
