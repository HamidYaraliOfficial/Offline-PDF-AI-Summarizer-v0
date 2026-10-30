# Local model directory / پوشه مدل محلی / 本地模型目录

Place a compatible **instruction-tuned GGUF** model here, for example a small Qwen Instruct GGUF quantized to Q4_K_M. The application does not download models automatically, and model files are intentionally excluded from Git.

- Recommended starting point: a 3B–4B instruct model in Q4_K_M for systems with around 8–16 GB RAM (quality and speed vary by model and hardware).
- Larger models may require substantially more RAM. Start with a smaller context size if loading fails.
- You may also browse to a model stored elsewhere in **Settings → AI model**.
- Only use model files you have the right to download and use. Review each model's license and the original publisher before obtaining it.
- The program uses `llama-cpp-python` locally. No AI API key is used and no model is pulled in the background.

نمونه: یک مدل Instruct با قالب GGUF مانند Qwen و کوانتیزه‌سازی Q4_K_M را در این پوشه قرار دهید. مدل داخل مخزن قرار نمی‌گیرد و برنامه آن را خودکار دانلود نمی‌کند.

把兼容的指令微调 GGUF 模型放在此目录中。模型文件不会被提交到 Git，应用也不会在后台自动下载模型。请先阅读模型本身的许可证。
