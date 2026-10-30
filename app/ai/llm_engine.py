from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from app.ai.model_manager import resolve_model_path

logger = logging.getLogger(__name__)


class LocalLLM:
    """Lazy llama.cpp wrapper. It never opens network connections or uses a cloud API."""
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._llm = None
        self.model_path: Path | None = None

    def load(self) -> None:
        if self._llm is not None:
            return
        self.model_path = resolve_model_path(str(self.config.get("model_path", "")))
        if not self.model_path:
            raise RuntimeError("The local AI model was not found. Open Settings → AI Model and select a compatible .gguf file, or place a single GGUF file in the models folder.")
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("The local AI runtime is not installed. Run setup_windows.bat again, or install llama-cpp-python using the instructions in README.md.") from exc
        try:
            self._llm = Llama(
                model_path=str(self.model_path),
                n_ctx=max(2048, int(self.config.get("context_size", 4096))),
                n_threads=max(1, int(self.config.get("cpu_threads", 4))),
                n_gpu_layers=int(self.config.get("gpu_layers", 0)),
                verbose=False,
            )
        except Exception as exc:
            logger.exception("Could not load local GGUF model")
            raise RuntimeError("The AI model could not be loaded. Check that the GGUF file is valid and compatible, and that your computer has enough RAM. See Settings → AI Model and logs/app.log.") from exc

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 700, temperature: float = 0.2) -> str:
        self.load()
        assert self._llm is not None
        try:
            result = self._llm.create_chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                max_tokens=max(64, int(max_tokens)),
                temperature=temperature,
                top_p=0.9,
                repeat_penalty=1.08,
            )
            choices = result.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""
            if not content.strip():
                raise RuntimeError("The local model returned an empty response. Try another compatible instruct GGUF model.")
            return content.strip()
        except RuntimeError:
            raise
        except Exception as exc:
            logger.exception("Local model inference failed")
            raise RuntimeError("Local AI inference failed. Try reducing Context Size in Settings or selecting a smaller GGUF model.") from exc

    def close(self) -> None:
        if self._llm is not None:
            try:
                self._llm.close()
            except Exception:
                pass
            self._llm = None
