#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
base = root / "app/src/main/java/com/livetrans/trar"
res = root / "app/src/main/res"

def replace(path: str, old: str, new: str, expected: int = 1) -> None:
    file = base / path
    source = file.read_text(encoding="utf-8")
    count = source.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrence(s), found {count} for {old!r}")
    file.write_text(source.replace(old, new), encoding="utf-8")
    print(f"PATCHED {path}")

def wrap_region(path: str, start: str, end: str, page: int) -> None:
    file = base / path
    source = file.read_text(encoding="utf-8")
    a = source.find(start)
    if a < 0:
        raise SystemExit(f"{path}: start anchor not found: {start[:90]!r}")
    b = source.find(end, a + len(start))
    if b < 0:
        raise SystemExit(f"{path}: end anchor not found: {end[:90]!r}")
    block = source[a:b]
    indented = "".join(("    " + line if line.strip() else line) for line in block.splitlines(keepends=True))
    wrapped = f"            if (selectedPage == {page}) {{\n" + indented + "            }\n\n"
    file.write_text(source[:a] + wrapped + source[b:], encoding="utf-8")
    print(f"WRAPPED {path} section for tab {page}")

# Better sentence segmentation: the old 2.4s cap chopped Turkish clauses.
replace("audio/AudioCapture.kt", "minSilenceDuration = 0.28f", "minSilenceDuration = 0.48f")
replace("audio/AudioCapture.kt", "minSpeechDuration = 0.14f", "minSpeechDuration = 0.20f")
replace("audio/AudioCapture.kt", "maxSpeechDuration = 2.4f", "maxSpeechDuration = 6.0f")

# Explicit Turkish recognition with a Turkish spelling prompt and word/segment timestamps.
replace("domain/GroqAsrEngine.kt", '.addFormDataPart("model", "whisper-large-v3-turbo")',
        '.addFormDataPart("model", "whisper-large-v3")')
replace("domain/GroqAsrEngine.kt", '.addFormDataPart("response_format", "verbose_json")',
        '.addFormDataPart("response_format", "verbose_json")\n            .addFormDataPart("language", "tr")\n            .addFormDataPart("prompt", "Bu ses Türkçe konuşma içerir. Türkçe karakterleri doğru yaz (ç, ğ, ı, İ, ö, ş, ü). Duyulmayan kelimeleri uydurma; çeviri yapma, konuşmayı Türkçe yazıya dök.")\n            .addFormDataPart("timestamp_granularities[]", "segment")\n            .addFormDataPart("timestamp_granularities[]", "word")')

# Local offline Whisper returns a complete VAD segment rather than incremental partial hypotheses.
replace("domain/LocalWhisperEngine.kt",
        "                partial.emit(item.copy(receivedAtMs = System.currentTimeMillis()))\n", "")

# Ensure outline preferences still work after the transparent subtitle restyle.
replace("service/OverlayRenderer.kt",
        "            setShadowLayer(5f, 0f, 0f, Color.BLACK)",
        "            if (currentSettings.outlineEnabled) setShadowLayer(5f, 0f, 0f, Color.BLACK)")
replace("service/OverlayRenderer.kt",
        "        subtitle?.setShadowLayer(5f, 0f, 0f, Color.BLACK)\n        root?.background = null",
        "        if (settings.outlineEnabled) subtitle?.setShadowLayer(5f, 0f, 0f, Color.BLACK) else subtitle?.setShadowLayer(0f, 0f, 0f, Color.TRANSPARENT)\n        root?.background = null")

# Serialize final line decisions and avoid displaying the same sentence twice from local + cloud ASR.
replace("domain/HybridPipeline.kt", "import kotlinx.coroutines.launch\n",
        "import kotlinx.coroutines.launch\nimport kotlinx.coroutines.sync.Mutex\nimport kotlinx.coroutines.sync.withLock\n")
replace("domain/HybridPipeline.kt", "    private val context = ArrayDeque<String>()\n",
        "    private val context = ArrayDeque<String>()\n    private val stateMutex = Mutex()\n    private val recentFinalTexts = ArrayDeque<String>()\n")
replace("domain/HybridPipeline.kt",
        """        jobs += scope.launch(Dispatchers.Default) {
            local.partialResults.collect { result -> translateAndRender(result, false) }
        }
""", "")
replace("domain/HybridPipeline.kt",
        "    private suspend fun translateAndRender(result: AsrResult, final: Boolean) {",
        "    private suspend fun translateAndRender(result: AsrResult, final: Boolean) = stateMutex.withLock {")
replace("domain/HybridPipeline.kt", "        if (turkish.isBlank()) return\n",
        "        if (turkish.isBlank()) return@withLock\n")
replace("domain/HybridPipeline.kt", "        val language = result.language.lowercase()\n",
        """        if (final) {
            val fingerprint = turkish.lowercase().replace(Regex("[ ]+"), " ").trim()
            if (fingerprint in recentFinalTexts) return@withLock
        }
        val language = result.language.lowercase()
""")
replace("domain/HybridPipeline.kt",
        """        if (final && result.engineName == "cloud") {
            context.addLast(turkish)
            while (context.size > 5) context.removeFirst()
        }
""",
        """        if (final) {
            val fingerprint = turkish.lowercase().replace(Regex("[ ]+"), " ").trim()
            recentFinalTexts.addLast(fingerprint)
            while (recentFinalTexts.size > 8) recentFinalTexts.removeFirst()
            context.addLast(turkish)
            while (context.size > 5) context.removeFirst()
        }
""")
replace("domain/HybridPipeline.kt", "        context.clear()\n",
        "        context.clear()\n        recentFinalTexts.clear()\n")

# Redesign the long scrolling screen into four Arabic destinations while preserving its existing controls.
screen = base / "ui/MainScreen.kt"
src = screen.read_text(encoding="utf-8")
state_anchor = "    var keySaved by remember { mutableStateOf(false) }\n"
if state_anchor not in src:
    raise SystemExit("MainScreen.kt: selectedPage state anchor not found")
src = src.replace(state_anchor, state_anchor + "    var selectedPage by remember { mutableStateOf(0) }\n", 1)

old_header = """            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("LiveTrans — ترجمة التركية إلى العربية", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Text("ترجمة صوت الفيديو إلى العربية أثناء المشاهدة", color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
"""
new_header = """            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                    Text("↔", modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp), fontSize = 30.sp, color = MaterialTheme.colorScheme.onPrimaryContainer, fontWeight = FontWeight.Bold)
                }
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text("LiveTrans", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                    Text("ترجمة ذكية من التركية إلى العربية", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                PageTab("مباشر", selectedPage == 0, Modifier.weight(1f)) { selectedPage = 0 }
                PageTab("القاموس", selectedPage == 1, Modifier.weight(1f)) { selectedPage = 1 }
                PageTab("السجل", selectedPage == 2, Modifier.weight(1f)) { selectedPage = 2 }
                PageTab("الإعدادات", selectedPage == 3, Modifier.weight(1f)) { selectedPage = 3 }
            }
"""
if old_header not in src:
    raise SystemExit("MainScreen.kt: header anchor not found")
src = src.replace(old_header, new_header, 1)
screen.write_text(src, encoding="utf-8")

status_start = "            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLow)) {"
model_start = """            Card {
                Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Text("محرك التعرّف المحلي","""
selftest_start = """            Card {
                Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("اختبار ذاتي","""
settings_start = """            Card {
                Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("إعدادات الترجمة والنافذة","""
cloud_start = """            Card {
                Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("مفتاح Groq السحابي (اختياري)","""
glossary_start = """            Card {
                Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("القاموس والملفات التعريفية","""
history_start = """            Card {
                Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("الملخص والسجل","""
note_start = '            Text("ملاحظة: بعض خدمات الفيديو تمنع تسجيل صوتها.'
wrap_region("ui/MainScreen.kt", status_start, model_start, 0)
wrap_region("ui/MainScreen.kt", model_start, selftest_start, 0)
wrap_region("ui/MainScreen.kt", selftest_start, settings_start, 0)
wrap_region("ui/MainScreen.kt", settings_start, cloud_start, 3)
wrap_region("ui/MainScreen.kt", cloud_start, glossary_start, 3)
wrap_region("ui/MainScreen.kt", glossary_start, history_start, 1)
wrap_region("ui/MainScreen.kt", history_start, note_start, 2)

# Remove an obsolete opacity slider because the cinema subtitle now has no opaque panel.
src = screen.read_text(encoding="utf-8")
src, count = re.subn(
    r' *Text\("شفافية خلفية الترجمة: [^\n]*"\)\n *Slider\(value = settings\.backgroundOpacity[^\n]*\n',
    '                    Text("نمط الترجمة: نص أبيض عريض بظل أسود، من دون صندوق يحجب الصورة.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)\n',
    src, count=1
)
if count != 1:
    raise SystemExit("MainScreen.kt: obsolete overlay opacity control was not found")
screen.write_text(src, encoding="utf-8")

replace("ui/MainScreen.kt", "@Composable\nprivate fun SettingSwitch(",
        """@Composable
private fun PageTab(label: String, selected: Boolean, modifier: Modifier = Modifier, onClick: () -> Unit) {
    if (selected) {
        Button(onClick = onClick, modifier = modifier) { Text(label, maxLines = 1) }
    } else {
        OutlinedButton(onClick = onClick, modifier = modifier) { Text(label, maxLines = 1) }
    }
}

@Composable
private fun SettingSwitch(""")

# Fresh vector launcher artwork: two speech bubbles and a bidirectional translation mark.
drawables = res / "drawable"
drawables.mkdir(parents=True, exist_ok=True)
launcher = '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#071629" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#F04452" android:pathData="M12,24 C12,14 20,8 30,8 H58 C69,8 77,16 77,27 V44 C77,55 69,63 58,63 H39 L22,76 V63 C16,60 12,53 12,44 Z"/>
    <path android:fillColor="#00BFA5" android:pathData="M39,49 C39,38 47,31 58,31 H82 C93,31 100,39 100,50 V72 C100,83 92,91 81,91 H68 L54,103 V90 C45,88 39,81 39,72 Z"/>
    <path android:fillColor="#FFF8EF" android:pathData="M31,23 C21,23 19,39 27,46 C34,52 45,49 49,39 C43,44 33,43 30,36 C28,31 29,27 31,23 Z"/>
    <path android:fillColor="#26D6FF" android:pathData="M34,48h5v12h-5z M43,42h5v24h-5z M52,36h5v36h-5z M61,42h5v24h-5z M70,48h5v12h-5z"/>
    <path android:fillColor="#FFC247" android:pathData="M59,7 L82,7 L76,14 L92,28 L84,36 L68,22 L62,29 L59,7 Z"/>
    <path android:fillColor="#268DFF" android:pathData="M48,94 L26,94 L32,87 L18,73 L26,65 L40,79 L46,72 L48,94 Z"/>
</vector>
'''
(drawables / "ic_launcher.xml").write_text(launcher, encoding="utf-8")

manifest = root / "app/src/main/AndroidManifest.xml"
xml = manifest.read_text(encoding="utf-8")
xml = xml.replace('android:label="ترجمة مباشرة TR → AR"', 'android:label="@string/app_name"')
xml = xml.replace('android:icon="@drawable/ic_launcher"',
                  'android:icon="@drawable/ic_launcher"\n        android:roundIcon="@drawable/ic_launcher"', 1)
xml = xml.replace('android:supportsRtl="true"',
                  'android:description="@string/app_description"\n        android:supportsRtl="true"')
xml = xml.replace('android:label="ترجمة مباشرة"', 'android:label="@string/app_name"')
manifest.write_text(xml, encoding="utf-8")

values = res / "values"
values.mkdir(parents=True, exist_ok=True)
strings = values / "strings.xml"
st = strings.read_text(encoding="utf-8") if strings.exists() else '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n</resources>\n'
for name, value in [
    ("app_name", "LiveTrans | تركي إلى عربي"),
    ("app_description", "ترجمة الكلام التركي إلى العربية مع ترجمة عائمة أثناء المشاهدة")
]:
    pattern = rf'<string name="{name}">.*?</string>'
    entry = f'<string name="{name}">{value}</string>'
    if re.search(pattern, st, flags=re.S):
        st = re.sub(pattern, entry, st, count=1, flags=re.S)
    else:
        st = st.replace("</resources>", f"    {entry}\n</resources>")
strings.write_text(st, encoding="utf-8")

# App version 2.0.0.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
g = g.replace("versionCode = 1", "versionCode = 2", 1)
g = g.replace('versionName = "1.0.0"', 'versionName = "2.0.0"', 1)
needle = '        vectorDrawables { useSupportLibrary = true }'
if g.count(needle) != 1:
    raise SystemExit("Gradle: cannot find the expected vectorDrawables defaultConfig line")
g = g.replace(
    needle,
    needle + chr(10) + '        ndk { abiFilters.addAll(listOf("arm64-v8a", "armeabi-v7a")) }',
    1
)
gradle.write_text(g, encoding="utf-8")

print("LiveTrans 2.0 product patches applied.")
