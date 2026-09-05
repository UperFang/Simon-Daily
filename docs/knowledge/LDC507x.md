# LDC507x 知识卡片（电感式旋变前端）

> 知识卡片 = 结论与指针；原始文件在 Zotero，本地缓存不入 git。

## 是什么

TI **电感式旋变（Inductive Resolver）模拟前端**：用 PCB 技术替代传统旋变压器，做牵引电机/转向电机位置传感。竞品对标：Renesas IPS2550（库内有对比 PPT）。

## 工作原理（关键理解）

1. LDC5073 驱动**激励线圈**，在导电目标（target，装在电机转子上）中产生涡流
2. 目标与定子 sensed 线圈均为显极（salient）结构 → 转子-定子相对角度被编码为 **COS/SIN** 两路信号
3. 芯片完成激励产生 → 滤波 → 解调 → 放大，MCU 用 COS/SIN 估算角度
4. 支持 EOL（下线）编程：可配置诊断与 OBD2 行为

## 应用

- 牵电机旋变：BEV/HEV、启发电机
- 电机位置传感（MPS）：电动助力转向（EPS）、刹车助力器
- 库内分类正落在 `3- Traction Inverter` 与 `5- Chasis` 双处——两个领域都用

## 应用要点

- 与 LDC507x 同族的分类条目有 Product Overview PDF；选型对比直接看 vs IPS2550 的 PPT
- 无磁路、PCB 共板 = 成本与产线优势；EOL 可编程 = 产线标定友好

## 资料位置

- **Zotero**：`FAE&Work/3- Traction Inverter/LDC507x` 与 `2- Sensor` → `LDC5073` 条目组（SNOSDH9 datasheet 2023、Product Overview、竞品对比 PPT）

## 整理记录

- 2026-09-05：Simon 建卡（首次全库学习）
