# 财务经营分析：来源、口径与数值角色约束

Python 标准库实现的可运行财务分析演示。使用 Decimal 计算 7 项指标，保留主体、期间、币种、合并/母公司范围和来源元数据。它展示可信程序计算与模型解释校验之间的边界。

## 启动

需要 Python 3.10+，无需安装第三方包。

```sh
python -m unittest discover -s tests
python -m fin_analysis
python -m fin_analysis --serve --port 8765
```

页面地址：`http://127.0.0.1:8765`；JSON 接口：`/api/results`。服务仅监听本机。默认加载 `data/synthetic.json`，所有公司和金额均为合成样例，不是真实财报或模型输出。

## 版本与限制

- 计算规则来自内部已验证 r02-v3 基线；发布版改为可移植的合成输入加载器，并保留字段、全年流量、期间、主体与范围检查。内部数据来源核定、比较基期审阅和原始资料未发布。发布包不是内部实验 sender 的完整部署副本。
- `numeric_roles.py` 来自 r6 工程候选：按每次数值的附近指标名、单位、期间、主体和引用角色检查。支持中文/财务大写、阿拉伯及全角数字。P/M 政策编号、日期和公式常量不能充当公司金额或增长率。该门禁只验证明确的数值角色与受支持表达，不代表完整自然语言推理或业务验收。
- 内部 r2 真实实验得到 4 个完整 JSON，但可用 final 为 0/4；历史必要项及严格验收仍为 0/16、0/4。独审曾诊断原始文本部分必要信息 10/16，这不等于最终通过。r6 暂无真实模型生成，等待独立复审。
- 演示不自动调用模型。经营原因、舞弊或信用风险结论缺证；不会以程序计算冒充模型分析成功。
- 真实数据的同比返回 `accounting_basis_unverified`，直至另外核定同主体、同范围和同报告可比基期。本仓库仅在显式合成数据中启用 `synthetic_comparable`。

## 文件

- `fin_analysis/engine.py`：7 指标、缺失值、零分母和负基期处理。
- `fin_analysis/contracts.py`：字段角色与全年流量校验。
- `fin_analysis/numeric_roles.py`：工程候选的逐次数字来源角色门禁。
- `data/synthetic.json`：两期虚构公司样例。
- `docs/data_dictionary.md`：输入字段和合法来源接入指引。
- `docs/quality_and_cost.json`：真实批次质量、token 与时间成本摘要。

仓库不包含 CSMAR 原始数据、年报全文、内部路径、服务/SSH 地址、凭据或授权全文。数据使用权须由使用者自行取得；数据文件放入被 git 忽略的 `local_data/`。
