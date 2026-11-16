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

# Subtitle look: clean, centered cinema-style Arabic text with no opaque card.
replace("service/OverlayRenderer.kt",
        "container.setPadding(dp(14), dp(8), dp(14), dp(8))",
        "container.setPadding(dp(8), dp(4), dp(8), dp(4))")
replace("service/OverlayRenderer.kt",
        'typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)',
        'typeface = Typeface.create("sans-serif", Typeface.BOLD)')
replace("service/OverlayRenderer.kt",
        "if (currentSettings.outlineEnabled) setShadowLayer(3f, 1f, 2f, Color.BLACK)",
        "setShadowLayer(5f, 0f, 0f, Color.BLACK)")
replace("service/OverlayRenderer.kt",
        "            addView(badge, android.widget.LinearLayout.LayoutParams(-2, -2))",
        "            badge.visibility = View.GONE")
replace("service/OverlayRenderer.kt",
        """        container.background = GradientDrawable().apply {
            setColor(Color.argb((currentSettings.backgroundOpacity * 255).toInt(), 10, 16, 21))
            cornerRadius = dp(14).toFloat()
            setStroke(dp(1), 0x557FFFFFFF.toInt())
        }""",
        "        container.background = null")
replace("service/OverlayRenderer.kt",
        """        if (settings.outlineEnabled) subtitle?.setShadowLayer(3f, 1f, 2f, Color.BLACK) else subtitle?.setShadowLayer(0f, 0f, 0f, Color.TRANSPARENT)
        root?.background = GradientDrawable().apply {
            setColor(Color.argb((settings.backgroundOpacity * 255).toInt(), 10, 16, 21))
            cornerRadius = dp(14).toFloat()
            setStroke(dp(1), 0x557FFFFFFF.toInt())
        }""",
        """        subtitle?.setShadowLayer(5f, 0f, 0f, Color.BLACK)
        root?.background = null""")
