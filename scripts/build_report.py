#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""防错（Poka-Yoke）设计方案生成器：读取结构化数据，输出纯文字版 TXT + Markdown。
内置小样本（密封圈漏装），直接运行 `python build_report.py` 即可产出样例。
产物默认写到当前工作目录（用户目录），不留在技能目录内。
"""
import argparse
import json
import os
import sys

# 内置小样本（演示用，非真实数据）：装配漏装密封圈导致漏水客诉
SAMPLE = {
    "no": "PKY-2026-0714-01",
    "problem": "出水阀装配工站偶发漏装密封圈，导致整机漏水客诉（月均 3 起）。",
    "process": "出水阀总成装配线3 - 步骤5（装入密封圈后拧紧阀芯）",
    "error_mode": "操作员漏装密封圈（无防错，仅靠人眼目检）",
    "current_control": "末端人眼 100% 目检 + 抽检",
    "root_cause": "密封圈为独立小件，装入动作无物理约束；目检疲劳时漏检。",
    "candidates": [
        {"id": "C1", "principle": "断根原理/消除", "effect": "不制造缺陷",
         "technical": "失效-安全装置", "desc": "密封圈随阀芯一体化预装（改设计，取消独立装入步骤）",
         "feasibility": "中（需设计变更 ECN）", "cost": "中"},
        {"id": "C2", "principle": "相符原理/保险", "effect": "不制造缺陷",
         "technical": "失效-安全装置", "desc": "料道仅容在位密封圈通过，缺圈则工位无法合模（物理防呆）",
         "feasibility": "高", "cost": "低"},
        {"id": "C3", "principle": "检测/警告", "effect": "不传递缺陷",
         "technical": "传感器放大", "desc": "视觉检测密封圈有无，缺失则报警并拦截至下道前",
         "feasibility": "高", "cost": "中"},
        {"id": "C4", "principle": "警告原理", "effect": "不接受缺陷",
         "technical": "特殊控制装置", "desc": "称重复检整机重量，异常声光报警（末端兜底）",
         "feasibility": "高", "cost": "低"},
    ],
    "recommended": "C2",
    "selection": "C2（相符/保险原理）以最低成本达成'不制造'：料道物理防呆，缺圈即无法合模，优于末端目检(C4)与视觉拦截(C3)；C1 效果最佳但需设计变更，作为中长期方案并行推进。",
    "implementation": "在装配线3 步骤5 加装防呆料道：密封圈未就位时工位互锁无法合模；配限位传感器确认到位。由设备工程出图，PE 跟进 ECN。",
    "validation": "制作 OK/NG 样件（有圈/无圈）各 50 件试产，验证漏装拦截率 100%；量产前按企业规则走 PPAP。",
    "standardization": "更新 SOP 装配线3 增加防呆料道操作步骤；建立防错案例库；同类旋转件装配横向展开(Yokoten)。",
    "owner": "李PE（工艺）",
    "date": "2026-07-14",
}


def _cand_table_md(cands):
    rows = ["| 编号 | 原理/原则 | 效果等级 | 技术方法 | 方案描述 | 可行性 | 成本 |",
            "|------|-----------|----------|----------|----------|--------|------|"]
    for c in cands:
        rows.append(f"| {c.get('id','')} | {c.get('principle','')} | {c.get('effect','')} | "
                     f"{c.get('technical','')} | {c.get('desc','')} | {c.get('feasibility','')} | {c.get('cost','')} |")
    return "\n".join(rows)


def _cand_lines_txt(cands):
    out = []
    for c in cands:
        out.append(f"- 【{c.get('id','')}】{c.get('principle','')}　效果：{c.get('effect','')}　技术：{c.get('technical','')}")
        out.append(f"    方案：{c.get('desc','')}")
        out.append(f"    可行性：{c.get('feasibility','')}　成本：{c.get('cost','')}")
    return "\n".join(out)


def build_md(d):
    lines = []
    lines.append(f"# 防错设计方案（{d.get('no','—')}）\n")
    lines.append(f"**设计人**：{d.get('owner','—')}　**日期**：{d.get('date','—')}\n")
    lines.append("## 一、问题描述\n")
    lines.append(f"- **问题**：{d.get('problem','—')}")
    lines.append(f"- **工序/操作**：{d.get('process','—')}")
    lines.append(f"- **失误模式**：{d.get('error_mode','—')}")
    lines.append(f"- **当前控制**：{d.get('current_control','—')}\n")
    lines.append("## 二、失误源头（根因）\n")
    lines.append(d.get("root_cause", "（待补充，建议用 5Why/鱼骨图定位）") + "\n")
    lines.append("## 三、候选防错方案（按 E-R-F-D-M 原则 + 十大原理构思）\n")
    lines.append(_cand_table_md(d.get("candidates", [])))
    lines.append("")
    lines.append("## 四、评估选型\n")
    lines.append("- **优先级基准**：不制造缺陷 > 不传递缺陷 > 不接受缺陷。")
    lines.append(f"- **推荐方案**：{d.get('recommended','—')}")
    lines.append(f"- **选型理由**：{d.get('selection','（待补充）')}\n")
    lines.append("## 五、技术落地\n")
    lines.append(d.get("implementation", "（待补充：选定方案对应的装置/传感器/逻辑/夹具）") + "\n")
    lines.append("## 六、实施验证\n")
    lines.append(d.get("validation", "（待补充：OK/NG 样件测试、PPAP、TPM 点检）") + "\n")
    lines.append("## 七、标准化与横向展开\n")
    lines.append(d.get("standardization", "（待补充：SOP 更新、案例库、Yokoten）") + "\n")
    lines.append("## 说明\n")
    lines.append("- 本方案为防错设计提案，物理可行性与最终实施由工艺/设备工程确认，技能不替用户拍板。")
    lines.append("- 效果等级与原则映射为通用参考，企业具体准则「待企业补充」。")
    return "\n".join(lines)


def build_txt(d):
    lines = []
    lines.append("防错设计方案")
    lines.append("=" * 48)
    lines.append(f"编号：{d.get('no','—')}　设计人：{d.get('owner','—')}　日期：{d.get('date','—')}")
    lines.append("")
    lines.append("一、问题描述")
    lines.append("-" * 48)
    lines.append(f"问题：{d.get('problem','—')}")
    lines.append(f"工序/操作：{d.get('process','—')}")
    lines.append(f"失误模式：{d.get('error_mode','—')}")
    lines.append(f"当前控制：{d.get('current_control','—')}")
    lines.append("")
    lines.append("二、失误源头（根因）")
    lines.append("-" * 48)
    lines.append(d.get("root_cause", "（待补充，建议用 5Why/鱼骨图定位）"))
    lines.append("")
    lines.append("三、候选防错方案（按 E-R-F-D-M 原则 + 十大原理构思）")
    lines.append("-" * 48)
    lines.append(_cand_lines_txt(d.get("candidates", [])))
    lines.append("")
    lines.append("四、评估选型")
    lines.append("-" * 48)
    lines.append("优先级基准：不制造缺陷 > 不传递缺陷 > 不接受缺陷。")
    lines.append(f"推荐方案：{d.get('recommended','—')}")
    lines.append(f"选型理由：{d.get('selection','（待补充）')}")
    lines.append("")
    lines.append("五、技术落地")
    lines.append("-" * 48)
    lines.append(d.get("implementation", "（待补充：选定方案对应的装置/传感器/逻辑/夹具）"))
    lines.append("")
    lines.append("六、实施验证")
    lines.append("-" * 48)
    lines.append(d.get("validation", "（待补充：OK/NG 样件测试、PPAP、TPM 点检）"))
    lines.append("")
    lines.append("七、标准化与横向展开")
    lines.append("-" * 48)
    lines.append(d.get("standardization", "（待补充：SOP 更新、案例库、Yokoten）"))
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="JSON 输入文件路径（缺省用内置小样本）")
    ap.add_argument("--out-dir", help="输出目录（缺省为当前工作目录）")
    ap.add_argument("--format", choices=["txt", "md", "all"], default="all",
                    help="输出格式：txt=纯文字版，md=Markdown，all=两者（默认）")
    a = ap.parse_args()

    if a.input:
        try:
            data = json.load(open(a.input, encoding="utf-8"))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
            sys.exit(1)
    else:
        data = SAMPLE

    out_dir = a.out_dir or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    date_tag = data.get("date", "").replace("-", "") or "样例"
    base = f"防错设计方案_{date_tag}"

    result = {"status": "success", "files": []}
    if a.format in ("md", "all"):
        md_path = os.path.join(out_dir, base + ".md")
        open(md_path, "w", encoding="utf-8").write(build_md(data))
        result["files"].append(md_path)
    if a.format in ("txt", "all"):
        txt_path = os.path.join(out_dir, base + ".txt")
        open(txt_path, "w", encoding="utf-8").write(build_txt(data))
        result["files"].append(txt_path)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
