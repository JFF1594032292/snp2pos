# Snp2pos

[English](README.md) | 简体中文

基于本地 dbSNP 和 tabix 的 rsID ↔ 染色体位置查询工具。

- `snp2pos`：rsID 转位置。
- `pos2snp`：位置转 rsID。
- `vcf2rs_chrall`：从 VCF 创建按 rs 数字索引的查询表。

## 依赖

Python 3.6+（仅标准库）、HTSlib 的 `tabix` 和 `bgzip`、系统 `sort`。示例已用 tabix 1.23 验证。
下列命令均在本目录执行，无需安装 Python 包。

## 快速体验

仓库仅附带 GRCh38 的 10 条示例变异，不包含完整数据库。

```bash
python3 snp2pos examples/rs.list --dbsnp examples/GRCh38.sample_rs.gz
python3 pos2snp examples/positions.tsv --dbsnp examples/GRCh38.sample.vcf.gz

printf 'rs775809821\n' | python3 snp2pos --dbsnp examples/GRCh38.sample_rs.gz
printf '1\t10019\n' | python3 pos2snp --dbsnp examples/GRCh38.sample.vcf.gz
```

以上输出均为（Tab 分隔，无表头）：

```text
1	10019	rs775809821	TA	T
```

单条查询及其他参数：

```bash
python3 snp2pos -rs rs775809821 --dbsnp examples/GRCh38.sample_rs.gz
python3 pos2snp -p 1 10019 --dbsnp examples/GRCh38.sample.vcf.gz
python3 snp2pos --help
python3 pos2snp --help
python3 vcf2rs_chrall --help
```

## 输入输出约定

- 默认输出 `CHR POS ID REF ALT` 五列，Tab 分隔，POS 为 **1-based**。
- rsID 输入每行一个，支持 `rs123`、`RS123` 或 `123`。
- 位置输入每行 `CHR<TAB>POS`，POS 为 **1-based**；染色体名称必须与数据库一致。
- 不提供输入文件或指定 `-` 时读取标准输入；`-o` 指定输出文件。
- `snp2pos -s T` 拆分多 ALT；`-prefix chr` 给输出染色体添加前缀。
- `snp2pos -bed T` 保留既有行为：输出 `[POS-1, POS+1)`，是 **0-based、右端不包含的 2 bp 区间**，不是单碱基 BED，也不是按 REF 长度生成的变异区间。
- 批量输入去重，不保证输入顺序；无匹配记录不输出，部分无效输入会静默跳过。
- 批量模式读完输入后查询，结果保存在内存中；建议大型任务自行分批。
- `-t T` 启用计时；两个查询脚本会把计时信息写入标准输出，生成 TSV 时不要启用。

## 持久化数据库路径

为每个版本分别保存数据库路径一次（将示例路径替换为已建立索引的真实文件）：

```bash
./pos2snp -g 37 --set-dbsnp /path/to/GRCh37.vcf.gz
./snp2pos -g 37 --set-dbsnp /path/to/GRCh37_rs.gz
./pos2snp -g 38 --set-dbsnp /path/to/GRCh38.vcf.gz
./snp2pos -g 38 --set-dbsnp /path/to/GRCh38_rs.gz

./snp2pos -g 38 -rs rs3
./pos2snp -g 38 -p 13 31872705
```

路径保存在安装脚本旁的 `.snp2pos_config` 中。`--set-dbsnp` 检查文件及 CSI/TBI 索引存在，保存绝对路径后退出，不执行查询；不会生成索引或验证基因组版本。其他工具和版本的配置会保留。安装目录需要可写。

优先级：`--dbsnp`（仅本次）> `-g` 对应的配置路径 > 下方默认文件名。默认版本仍为 37。也可复制 `.snp2pos_config.example` 为 `.snp2pos_config` 后手动编辑；配置中的相对路径以安装目录为基准。实际配置已被 Git 忽略，避免发布个人路径。请将 `snp2pos_config.py` 与两个命令脚本一起保留。

## 使用完整数据库

下载入口：

- [dbSNP b152 历史版本](https://ftp.ncbi.nih.gov/snp/archive/b152/VCF/)：本仓库示例数据的原始数据库下载路径（由作者提供）。
- [dbSNP 最新版本](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/)：获取当前发布的数据；该目录随版本更新，不是固定版本链接。

请按参考基因组版本选择文件，并记录下载日期、dbSNP release 和文件名。新版文件名可能不同于下方默认名称，建议用 `--dbsnp` 显式指定。

完整数据库和索引不随仓库分发。自行准备匹配参考基因组版本、按坐标排序的 BGZF VCF。
数据库中的染色体可能是 `1`、`chr1` 或参考序列 accession；本工具不自动转换命名。

```bash
mkdir -p data
# 将自己的 BGZF VCF 放在 data/dbsnp.vcf.gz，然后执行：
tabix -C -p vcf data/dbsnp.vcf.gz
python3 vcf2rs_chrall data/dbsnp.vcf.gz -o data/dbsnp_rs.gz
python3 snp2pos -rs rs3 --dbsnp data/dbsnp_rs.gz
python3 pos2snp -p 13 31872705 --dbsnp data/dbsnp.vcf.gz
```

最后一条坐标仅是 GRCh38 示例，实际查询须匹配数据库版本和命名。
转换器保留 VCF 的坐标和染色体名称，从 ID 列提取 rs 数字，经 `sort`、`bgzip` 生成查询表及 CSI 索引；完整数据库转换需要足够磁盘和排序临时空间。

不指定 `--dbsnp` 时，`-g 37`（默认）或 `-g 38` 选择脚本旁的下列文件：

| 版本 | pos2snp | snp2pos |
| --- | --- | --- |
| 37 | GCF_000001405.25.gz | GCF_000001405.25_rs-chrall.gz |
| 38 | GCF_000001405.38.gz | GCF_000001405.38_rs-chrall.gz |

`-g` 只选择默认文件名，不做坐标转换；指定 `--dbsnp` 后以该文件为准。

## 示例数据来源

`examples/GRCh38.sample.vcf` 截取自现有 GRCh38 dbSNP 参考文件 `GCF_000001405.38.gz`，区域 `1:10001-10100` 的 10 条记录。
仅保留 CHROM、POS、ID、REF、ALT，QUAL/FILTER/INFO 置为 `.`，重新生成最小 VCF 头；不包含样本或基因型。
作者提供的原始数据库下载入口为 [dbSNP b152](https://ftp.ncbi.nih.gov/snp/archive/b152/VCF/)。原始下载日期未记录；此示例仅用于功能演示，不用于正式分析或版本基准。
压缩文件和 CSI 索引均由这份小 VCF 重新生成。

## 验证

```bash
python3 test_cli_compat.py
python3 test_examples.py
python3 test_config.py
```

前者检查 CLI 兼容性，后者使用真实 tabix 检查示例文件、标准输入、单条查询和 BED 输出。

## 许可

代码采用 [MIT 许可证](LICENSE)。dbSNP 示例数据来自 NCBI，不通过代码许可证重新授权。

`test_config.py` 在临时安装目录中验证路径保存及覆盖优先级。
