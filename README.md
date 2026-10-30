# Offline PDF AI Summarizer

**Author / سازنده / 作者: Hamid Yarali (حمید یارعلی)**  
**Copyright © 2026 Hamid Yarali. All rights reserved.**

A Windows desktop application that extracts and summarizes PDF documents with a **local GGUF language model**. After dependencies and a model have been installed, text extraction and AI inference run on your computer. The app does not require a cloud AI account, API key, or document upload. The local model is not bundled with this repository.

> Important: this is a local-first application, not a guarantee that every third-party installer or manually installed dependency is itself offline. The application code does not call online AI APIs or automatically download model weights. One-time installation of Python packages and manual acquisition of a model may require internet access.

## ภาษา فارسی | راهنمای فارسی

### معرفی

**Offline PDF AI Summarizer** یک نرم‌افزار دسکتاپ برای ویندوز است که متن فایل PDF را استخراج کرده و با استفاده از مدل زبانی محلی در قالب GGUF خلاصه می‌کند. پس از نصب وابستگی‌ها و قرار دادن مدل روی رایانه، پردازش PDF و اجرای هوش مصنوعی به سرویس ابری یا API Key نیاز ندارد. متن سند برای خلاصه‌سازی به سرور خارجی ارسال نمی‌شود.

### قابلیت‌ها

- رابط گرافیکی PySide6 با انتخاب فایل و Drag & Drop
- استخراج تدریجی صفحات با PyMuPDF و تقسیم متن به بخش‌های محدود برای فایل‌های بزرگ
- خلاصه کوتاه، استاندارد، تفصیلی و فصل‌به‌فصل (با تشخیص سرعنوان‌های قابل‌تشخیص)
- زبان خروجی خودکار، فارسی، انگلیسی یا چینی (کیفیت هر زبان به مدل انتخاب‌شده بستگی دارد)
- اجرای مدل GGUF به‌صورت محلی با llama.cpp؛ حالت CPU و امکان تنظیم GPU layers در صورت پشتیبانی نصب
- OCR محلی اختیاری با Tesseract برای PDFهای اسکن‌شده
- خروجی TXT، Markdown، PDF و DOCX، کپی خلاصه، تاریخچه SQLite و تنظیمات محلی
- لغو پردازش، ثبت خطا به‌صورت محلی و حذف فایل‌های میانی موقت
- ساختار ماژولار و تست‌های واحد

### نصب روی Windows 10/11 (64-bit)

1. Python **3.11 نسخه 64-bit** را نصب کنید.
2. فایل `setup_windows.bat` را با دوبار کلیک اجرا کنید. اسکریپت محیط مجازی و وابستگی‌های رابط گرافیکی، PDF و خروجی‌ها را نصب می‌کند و سپس تلاش می‌کند `llama-cpp-python` را نصب کند.
3. یک مدل محلی سازگار با GGUF و قالب Instruct تهیه کنید و آن را در پوشه `models` قرار دهید؛ یا مسیرش را در Settings انتخاب کنید. مدل به‌دلیل حجم و مجوز مستقل داخل Git نیست.
4. `run.bat` را اجرا کنید.
5. فایل PDF را انتخاب یا داخل پنجره رها کنید؛ نوع خلاصه و زبان خروجی را انتخاب و روی **SUMMARIZE** کلیک کنید.

### انتخاب مدل محلی

برای شروع، یک مدل کوچک Instruct در محدوده 3B تا 4B پارامتر با کوانتیزه‌سازی Q4_K_M گزینه‌ای معقول برای رایانه‌های دارای حدود 8 تا 16 گیگابایت RAM است؛ عملکرد واقعی به مدل، زمینه (Context)، سیستم و اندازه PDF وابسته است. یک نمونه خانواده مدل، Qwen Instruct در قالب GGUF است. این پروژه مدل خاصی را دانلود یا داخل مخزن کپی نمی‌کند. از ناشر اصلی مدل دانلود کنید و مجوز آن را بررسی کنید. فایل مدل می‌تواند نام دلخواهی داشته باشد اما باید با llama.cpp سازگار باشد و پسوند `.gguf` داشته باشد.

اگر فقط یک فایل GGUF داخل `models` باشد و مسیر مدل در تنظیمات خالی بماند، برنامه همان فایل را انتخاب می‌کند. اگر چند مدل دارید، مدل موردنظر را در **Settings → AI model** مشخص کنید.

### CPU و GPU

- مقدار `GPU layers = 0` اجرای CPU را درخواست می‌کند و انتخاب محافظه‌کارانه پیش‌فرض است.
- مقدار `-1` تلاش می‌کند همه لایه‌ها را به GPU پشتیبانی‌شده منتقل کند. این قابلیت به backend و build نصب‌شده `llama-cpp-python` وابسته است؛ GPU/CUDA تضمین‌شده نیست.
- اگر مدل بارگذاری نشد، ابتدا مدل کوچک‌تر و Context برابر 2048 یا 4096 را امتحان کنید و به `logs/app.log` در مسیر داده محلی برنامه مراجعه کنید.

### OCR برای PDF اسکن‌شده

OCR به‌صورت پیش‌فرض خاموش است. در Settings گزینه OCR را فعال کنید، مسیر `tesseract.exe` را در صورت نیاز بدهید و زبان‌هایی را که داده زبانی‌شان نصب شده وارد کنید؛ برای فارسی و انگلیسی معمولاً `fas+eng` است. نصب Python package به‌تنهایی کافی نیست: خود Tesseract و بسته‌های زبان باید روی ویندوز نصب شده باشند. اگر OCR فعال نباشد و PDF متن قابل استخراج نداشته باشد، برنامه پیام روشنی نمایش می‌دهد.

### نصب Runtime مدل در ویندوز

اسکریپت نصب در ویندوز ابتدا از CPU wheel رسمی `llama-cpp-python` استفاده می‌کند تا احتمال نیاز به کامپایل کمتر شود. راهنمای رسمی نصب (https://llama-cpp-python.readthedocs.io/en/latest/) گزینه‌های CPU و backendهای GPU را توضیح می‌دهد. اگر نصب شکست خورد، نسخه Python، ابزارهای ساخت و خطای pip را بررسی کنید. پس از نصب موفق، برنامه inference را محلی اجرا می‌کند. برای ساخت EXE نیز لازم است runtime در محیط `.venv` نصب شده باشد.

### خروجی گرفتن

پس از خلاصه‌سازی یا باز کردن موردی از History، از دکمه‌های **Save TXT**، **Save Markdown**، **Save PDF** و **Save DOCX** استفاده کنید. مسیر خروجی از Settings قابل تنظیم است. بخش PDF خروجی با renderer متنی Qt ساخته می‌شود؛ نمایش راست‌به‌چپ به فونت‌های نصب‌شده و امکانات سیستم بستگی دارد.

### ساخت فایل اجرایی EXE

پس از اجرای موفق setup و نصب کامل runtime مدل، `build_windows.bat` را اجرا کنید. خروجی مورد انتظار در `dist/OfflinePDFSummarizer/OfflinePDFSummarizer.exe` قرار می‌گیرد. این build از نوع one-folder است تا فایل‌های وابستگی کنار برنامه قرار بگیرند. مدل GGUF به‌صورت پیش‌فرض بسته‌بندی نمی‌شود؛ مدل را طبق مجوز خودش جداگانه در پوشه `models` قرار دهید. قبل از انتشار، خروجی را روی ویندوز تمیز آزمایش کنید.

### حریم خصوصی

- **Your documents are processed locally on your computer.**
- **No cloud API is required. No document upload is required.**
- برنامه کلید OpenAI، Gemini، Claude یا سرویس مشابه درخواست نمی‌کند.
- History و تنظیمات در مسیر داده محلی کاربر نگهداری می‌شوند. لاگ شامل متن کامل PDF نیست.
- متن اصلی PDF به History یا Log کپی نمی‌شود؛ فقط خلاصه نهایی و متادیتای لازم برای بازکردن نتیجه ذخیره می‌شود.
- در زمان خلاصه‌سازی، متن‌های میانی به‌صورت موقت روی دیسک محلی نگهداری می‌شوند و پوشه موقت پس از اتمام یا خطای پردازش پاک می‌شود.
- برای رعایت آفلاین بودن، اینترنت را پس از نصب اولیه و آماده‌سازی مدل قطع کنید. این نرم‌افزار هیچ درخواست API هوش مصنوعی آنلاین ایجاد نمی‌کند.

### مشکلات متداول

- **Model not found:** مدل `.gguf` را در Settings انتخاب کنید یا اگر تنها یک مدل دارید در `models` قرار دهید.
- **AI runtime not installed:** نصب `llama-cpp-python` کامل نشده است؛ پیام خطا و راهنمای نصب بالا را بررسی کنید.
- **Not enough RAM / model load failed:** مدل Q4 کوچک‌تر انتخاب کنید و Context را کاهش دهید.
- **Scanned PDF:** Tesseract و داده زبان مربوط را نصب کرده و OCR را فعال کنید.
- **PDF damaged or encrypted:** PDF را با یک برنامه PDF معتبر باز کنید و در صورت لزوم نسخه بدون رمز و سالم ذخیره کنید.
- **DOCX/PDF export error:** دسترسی نوشتن به مسیر را بررسی کرده و مسیر دیگری انتخاب کنید.
- **Cancellation:** توقف هنگام اجرای یک فراخوانی مدل ممکن است تا پایان همان فراخوانی زمان ببرد.

### اجرای تست‌ها

در محیط مجازی فعال:

```bat
.venv\Scripts\python.exe -m pytest
```

تست‌های واحد به مدل AI نیاز ندارند. برای اعتبارسنجی کامل inference باید یک مدل سازگار و runtime نصب‌شده داشته باشید.

---

## English Documentation

### Overview

Offline PDF AI Summarizer is a Windows desktop program that extracts PDF text and summarizes it using a local GGUF instruction model. Once Python dependencies and a model are available, extraction and inference happen on the computer. No AI API key, cloud inference service, or document upload is required by the application.

### Features

- PySide6 graphical interface with file picker and drag-and-drop
- Incremental PyMuPDF page extraction and bounded text chunks for long PDFs
- Short, standard, detailed, and chapter-by-chapter summary modes
- Automatic source-language detection or Persian, English, and Chinese output
- Local `llama-cpp-python` inference; CPU mode and configurable GPU layers where supported
- Optional local Tesseract OCR for scanned documents
- TXT, Markdown, PDF and DOCX exports; clipboard copy; SQLite history
- Background worker, progress updates, cancellation requests, local logging and temporary-directory cleanup
- Unit tests and Windows setup/build scripts

### Install and Run

1. Install **64-bit Python 3.11** for Windows 10/11.
2. Double-click `setup_windows.bat`. It creates `.venv`, installs core requirements, then tries the official `llama-cpp-python` CPU wheel index before falling back to the documented manual installation path. See https://llama-cpp-python.readthedocs.io/en/latest/.
3. Obtain a compatible instruction-tuned GGUF model and place it in `models`, or choose its path in Settings. Model weights are intentionally not included in Git.
4. Double-click `run.bat`.
5. Choose or drop a PDF, set the summary type and language, and click **SUMMARIZE**.

### Model and hardware

A quantized 3B–4B instruct model (for example, a compatible Qwen Instruct GGUF in Q4_K_M) can be a reasonable starting point for machines with roughly 8–16 GB RAM, but requirements vary. Review the upstream model's license. The app does not download models automatically. If exactly one `.gguf` file is present in `models` and no explicit path is configured, that file is selected automatically.

`GPU layers = 0` requests CPU inference. `-1` attempts to offload all layers to a supported GPU backend. GPU acceleration depends on the installed llama.cpp build and is not guaranteed. If loading fails, choose a smaller model and reduce Context Size.

### OCR

Install Tesseract itself and its language data locally, enable OCR in Settings, and enter the executable path if it is not discoverable. Use language codes whose data is installed, such as `fas+eng` for Persian and English. If a PDF contains no extractable text and OCR is disabled, the app explains that OCR is needed.

### Build an EXE

After setup and successful runtime installation, run `build_windows.bat`. The expected one-folder output is `dist/OfflinePDFSummarizer/OfflinePDFSummarizer.exe`. The model is not bundled. Test the packaged build on a clean Windows machine before distribution.

### Privacy statement

**Your documents are processed locally on your computer. No cloud API is required. No document upload is required.** Settings, history, temporary intermediates and logs are stored locally. The app does not log full PDF text or call online AI inference APIs. One-time package/model acquisition may require internet; after installing all dependencies and obtaining the model, disconnecting the network is a practical way to verify offline operation.

### Troubleshooting

- **Model not found:** select a `.gguf` file in Settings.
- **Runtime missing:** retry `setup_windows.bat` or follow the upstream `llama-cpp-python` installation guidance for your Python/Windows setup.
- **RAM errors:** use a smaller quantized model and reduce Context Size.
- **Scanned PDF:** install Tesseract and language data, then enable OCR.
- **Cancellation:** the current model generation call may need to finish before the worker exits.

Run tests with `.venv\Scripts\python.exe -m pytest`. The unit tests do not require model weights; end-to-end AI inference does.

---

## 中文文档 | Chinese Documentation

### 项目简介

Offline PDF AI Summarizer 是一个面向 Windows 10/11 64 位系统的桌面 PDF 摘要工具。它使用本地 GGUF 指令模型处理文档。安装运行依赖并准备模型后，PDF 文本提取和 AI 推理都在本机完成；应用不需要云端 AI API、API Key，也不会上传 PDF。

### 主要功能

- PySide6 图形界面，支持文件选择和拖放
- 使用 PyMuPDF 逐页读取，并将大型 PDF 分块处理
- 短摘要、标准摘要、详细摘要和逐章摘要
- 自动检测语言，也可选择波斯语、英语或中文作为输出语言
- 通过 `llama-cpp-python` 本地运行 GGUF 模型；支持 CPU，并可配置受支持的 GPU 层
- 可选的本地 Tesseract OCR，用于扫描版 PDF
- 导出 TXT、Markdown、PDF、DOCX，复制摘要并使用 SQLite 保存本地历史
- 后台线程、进度显示、取消请求、本地日志和临时目录清理

### 安装与运行

1. 安装 Windows 10/11 的 **64 位 Python 3.11**。
2. 双击 `setup_windows.bat`，创建虚拟环境并安装依赖。脚本优先尝试官方 CPU wheel 索引；如果失败，请参考 https://llama-cpp-python.readthedocs.io/en/latest/ 中与系统和 Python 版本匹配的安装方式。
3. 获取兼容的 Instruct GGUF 模型并放入 `models` 文件夹，或在 Settings 中选择其路径。模型权重不会包含在 Git 仓库里，请检查模型发布者的许可证。
4. 双击 `run.bat`。
5. 选择或拖放 PDF，选择摘要类型和输出语言，然后点击 **SUMMARIZE**。

### 模型与硬件

可以先尝试 Q4_K_M 量化的 3B–4B 指令模型；约 8–16 GB 内存可作为初步参考，但实际需求取决于模型、上下文长度和文件大小。`GPU layers = 0` 请求使用 CPU；`-1` 会尝试将所有层卸载到受支持的 GPU 后端。GPU 加速取决于安装的 llama.cpp 构建，不能保证所有设备都可用。模型不会由应用自动下载。

### OCR 与导出

扫描版 PDF 需要本机安装 Tesseract 和相应语言数据。在 Settings 中启用 OCR，并在需要时指定 `tesseract.exe` 路径。语言代码示例为 `fas+eng`，前提是对应语言数据已经安装。摘要可以保存为 TXT、Markdown、PDF 或 DOCX。

### 隐私说明

**文档在您的本地计算机上处理。不需要云端 API，也不需要上传文档。** 设置、历史、临时中间文件和日志都保存在本机。应用不会将完整 PDF 文本写入日志，也不会调用在线 AI 推理 API。首次安装软件包或获取模型时可能需要网络；完成准备后，可断开网络验证离线使用。

### 常见问题

- **找不到模型：** 在 Settings 中选择 GGUF 文件。
- **运行时未安装：** 重新运行 `setup_windows.bat`，并参考 `llama-cpp-python` 对应 Windows/Python 版本的安装说明。
- **内存不足：** 使用更小的量化模型并降低 Context Size。
- **扫描版 PDF：** 安装 Tesseract 及语言数据，并开启 OCR。
- **取消任务：** 当前模型生成调用可能需要结束后，后台任务才会停止。

运行测试：`.venv\Scripts\python.exe -m pytest`。单元测试不需要模型权重；端到端 AI 摘要测试需要已安装兼容模型和运行时。

---

## Project layout

```text
offline-pdf-ai-summarizer/
├── app/
│   ├── main.py
│   ├── ai/          # local GGUF runtime and hierarchical summarization
│   ├── export/      # TXT, Markdown, PDF and DOCX writers
│   ├── pdf/         # streamed extraction, chunking and optional OCR
│   ├── storage/     # local SQLite history
│   ├── ui/          # PySide6 main window, settings and worker thread
│   └── utils/       # configuration, logging and hardware report
├── models/README.md
├── tests/
├── requirements.txt
├── requirements-core.txt
├── setup_windows.bat
├── run.bat
├── build_windows.bat
├── README.md
├── LICENSE
└── COPYRIGHT
```

## License and attribution

Copyright © 2026 Hamid Yarali. All rights reserved. `LICENSE` contains the proprietary terms in English, Persian and Chinese. It is **not an open-source license**. Third-party packages, Tesseract, and model weights retain their own licenses.

Repository suggestion: **`offline-pdf-ai-summarizer`**  
GitHub URL after you create it: `https://github.com/HamidYaraliOfficial/offline-pdf-ai-summarizer`
