# PDF 学术文献重命名 CLI

根据 PDF 元数据批量重命名文件，适合论文本地归档。

## 安装

```bash
pip install -e .
```

## 用法

```bash
# 预览重命名（不实际修改）
python -m pdf_renamer ./papers --dry-run

# 执行重命名
python -m pdf_renamer ./papers
```

## 说明

- 支持单文件或目录
- 目录模式下仅处理通用文件名的 PDF
