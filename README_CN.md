# DOCX2MD — DOCX 转 Markdown 网页转换器

将 Microsoft Word `.docx` 文件转换为 Markdown 格式的网页服务。基于 FastAPI 构建，支持 Docker 部署。

## 功能特性

- **段落与标题** — H1-H6 六级标题
- **行内格式** — 加粗、斜体、下划线、删除线、上标、下标、行内代码
- **列表** — 有序列表和无序列表，支持多层嵌套
- **表格** — GFM（GitHub 风格）Markdown 表格，支持列对齐
- **图片** — 自动提取并生成 Markdown 引用
- **超链接** — 将 `<a>` 标签转换为 `[文本](链接)` 格式
- **页眉页脚** — 从 DOCX 中提取，以引用块形式放置在文档首尾
- **脚注尾注** — 行内引用标记和文末定义汇总
- **目录检测** — 识别目录条目并生成占位标记
- **样式映射** — Word 样式到 Markdown 的对应转换（支持自定义）
- **ZIP 打包** — 可选将 `.md` 文件和图片文件夹打包为 ZIP 下载

## 快速开始

### Docker 部署

```bash
docker-compose up --build
```

浏览器访问 http://localhost:8000 即可使用。

### 本地开发

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- 打开 http://localhost:8000 进入上传页面
- 打开 http://localhost:8000/docs 查看 Swagger API 文档

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 网页上传界面 |
| `POST` | `/convert` | 上传并转换 `.docx` 文件 |
| `GET` | `/download/{job_id}` | 下载转换结果 |
| `GET` | `/health` | 健康检查 |

### POST /convert

**表单参数：**
- `file`（必填）：`.docx` 文件，最大 50MB
- `output_format`（可选）：`"md"`（默认）或 `"zip"`
- `include_headers_footers`（可选）：`true`（默认）或 `false`
- `style_map`（可选）：自定义样式映射的 JSON 字符串

**响应示例：**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "filename": "output.md",
  "image_count": 5,
  "footnote_count": 3,
  "toc_detected": true,
  "warnings": [],
  "download_url": "/download/abc123?format=md"
}
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DOCX2MD_MAX_FILE_SIZE_MB` | `50` | 上传文件大小上限 |
| `DOCX2MD_LOG_LEVEL` | `info` | 日志级别 |
| `DOCX2MD_TEMP_FILE_TTL_MINUTES` | `30` | 转换文件保留时长 |

## 运行测试

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## 项目结构

```
docx2md/
├── app/
│   ├── api/            # FastAPI 路由和依赖
│   ├── converter/      # DOCX 转 Markdown 核心引擎
│   ├── templates/      # Jinja2 网页模板
│   └── utils/          # 文件工具和文本净化
├── tests/
│   ├── fixtures/       # 测试用 .docx 示例文件
│   ├── test_converter/ # 转换器单元测试
│   └── test_api/       # API 集成测试
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
