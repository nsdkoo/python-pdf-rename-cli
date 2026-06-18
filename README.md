# PDF 学术文献重命名 CLI

根据 PDF 元数据批量重命名文件，适合论文本地归档。

## 安装

```bash
pip install -e .
```

## 用法

```bash
# 查看版本
python -m pdf_renamer --version

# 预览重命名（不实际修改）
python -m pdf_renamer ./papers --dry-run

# 递归扫描子目录
python -m pdf_renamer ./papers -R --dry-run

# 执行重命名
python -m pdf_renamer ./papers
```

## 说明

- 支持单文件或目录
- 目录模式下仅处理通用文件名的 PDF
- `-R` 可递归扫描子目录
- 重名时自动追加 `_2`、`_3` 后缀
- 元数据清洗后若文件名为空，将回退为 `untitled`

## 提示

建议先使用 `--dry-run` 预览。
