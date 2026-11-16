#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
base = root / "app/src/main/java/com/livetrans/trar"

def replace(path: str, old: str, new: str, expected: int = 1) -> None:
    file = base / path
    source = file.read_text(encoding="utf-8")
    count = source.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrence(s), found {count} for {old!r}")
    file.write_text(source.replace(old, new), encoding="utf-8")
    print(f"PATCHED {path}: {old!r}")

replace("domain/TranslationEngine.kt",
        "package com.livetrans.trar.domain\n",
        "package com.livetrans.trar.domain\n\nimport com.livetrans.trar.data.GlossaryEntry\n")
replace("domain/GroqTranslationEngine.kt",
        "package com.livetrans.trar.domain\n",
        "package com.livetrans.trar.domain\n\nimport com.livetrans.trar.data.GlossaryEntry\n")
replace("domain/MlKitTranslationEngine.kt",
        "import com.google.mlkit.nl.translate.DownloadConditions",
        "import com.google.mlkit.common.model.DownloadConditions")
replace("domain/MlKitTranslationEngine.kt",
        "package com.livetrans.trar.domain\n",
        "package com.livetrans.trar.domain\n\nimport com.livetrans.trar.data.GlossaryEntry\n")
replace("domain/LocalWhisperEngine.kt",
        'language = "",',
        'language = "tr",')
replace("domain/LocalWhisperEngine.kt",
        "FeatureConfig(sampleRate = 16000f, featureDim = 80)",
        "FeatureConfig(sampleRate = 16000, featureDim = 80)")
replace("domain/LocalWhisperEngine.kt",
        "            stream.inputFinished()\n",
        "")
replace("service/OverlayRenderer.kt",
        "setStroke(dp(1), 0x557FFFFFFF)",
        "setStroke(dp(1), 0x557FFFFFFF.toInt())",
        expected=2)
replace("domain/GroqTranslationEngine.kt",
        'append("Do not censor, explain, summarize, or add commentary. Keep names consistent. ")',
        'append("Translate Turkish dialogue into natural Arabic, preserving intent, emotion, idioms, relationships, and speaker tone. Do not translate word-for-word when that sounds unnatural. Do not censor, explain, summarize, or add commentary. Keep character names and recurring terms consistent. If a phrase is incomplete, translate only what is clearly heard; never invent missing words. ")')

print("All compile and Turkish-first quality patches applied.")
