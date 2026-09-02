# -*- coding: utf-8 -*-
"""把教育部《全国普通高等学校名单》《全国成人高等学校名单》(2024-06-20) xls 转成 schools.json。

教育部官方来源：
  普通高等学校名单：http://www.moe.gov.cn/jyb_xxgk/s5743/s5744/A03/202406/W020240621412769813275.xls
  成人高等学校名单：http://www.moe.gov.cn/jyb_xxgk/s5743/s5744/A03/202406/W020240621412769848577.xls

字段映射到 School 表：
  name    <- 学校名称
  address <- 所在地（成人高校无此列，用主管部门所在地兜底）
"""
import json
import os
import re

import xlrd

HERE = os.path.dirname(os.path.abspath(__file__))
PU_XLS = os.path.join(HERE, 'moe_pu.xls')
CR_XLS = os.path.join(HERE, 'moe_cr.xls')
OUT = os.path.join(HERE, 'schools.json')

# 主管部门只要看起来像省级行政区才当作地址兜底（省/自治区/直辖市/兵团）
_PLACE_RE = re.compile(r'.*(省|自治区|特别行政区|兵团|市)$')


def parse(path, adult=False):
    wb = xlrd.open_workbook(path)
    ws = wb.sheet_by_index(0)
    out = []
    for r in range(ws.nrows):
        vals = [str(c).strip().replace('\n', '') if not isinstance(c, float) else str(int(c))
                for c in ws.row_values(r)]
        if not vals[0] or not vals[0].isdigit():
            continue
        name = vals[1].strip()
        if not name:
            continue
        if adult:
            # 成人高校：无所在地列，用主管部门（一般为省级）兜底
            supervisor = vals[3].strip()
            address = supervisor if _PLACE_RE.match(supervisor) else ''
        else:
            address = (vals[4].strip() if len(vals) > 4 else '') or ''
        out.append({'name': name, 'address': address})
    return out


def main():
    records = parse(PU_XLS, adult=False) + parse(CR_XLS, adult=True)
    names = [r['name'] for r in records]
    dups = {n for n in names if names.count(n) > 1}
    no_addr = [r for r in records if not r['address']]
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=1)
    print(f'写入了 {len(records)} 所高校 -> {OUT}')
    print(f'重复名称: {len(dups)} {sorted(dups)[:10]}')
    print(f'无地址: {len(no_addr)}  {[r["name"] for r in no_addr[:5]]}')


if __name__ == '__main__':
    main()
