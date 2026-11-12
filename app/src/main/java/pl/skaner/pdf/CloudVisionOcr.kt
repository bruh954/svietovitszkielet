package pl.skaner.pdf

import android.graphics.Bitmap
import android.graphics.Rect
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlin.math.max
import kotlin.math.min

/** Jedna linia rozpoznanego tekstu i jej położenie na zdjęciu (w pikselach). */
data class OcrLine(val text: String, val box: Rect, val words: Int)

/**
 * Rozpoznawanie pisma odręcznego przez Google Cloud Vision (DOCUMENT_TEXT_DETECTION).
 * Wymaga internetu i klucza API. Zwraca linie z położeniem, żeby warstwa tekstu w PDF
 * trafiała dokładnie w napisy na zdjęciu.
 */
object CloudVisionOcr {

    fun recognize(bmp: Bitmap, apiKey: String): List<OcrLine> {
        val jpeg = ByteArrayOutputStream().use { bos ->
            bmp.compress(Bitmap.CompressFormat.JPEG, 88, bos); bos.toByteArray()
        }
        val body = JSONObject().put("requests", JSONArray().put(JSONObject()
            .put("image", JSONObject().put("content", Base64.encodeToString(jpeg, Base64.NO_WRAP)))
            .put("features", JSONArray().put(JSONObject().put("type", "DOCUMENT_TEXT_DETECTION")))
            .put("imageContext", JSONObject().put("languageHints", JSONArray().put("pl").put("en")))
        ))

        val conn = (URL("https://vision.googleapis.com/v1/images:annotate?key=" + apiKey.trim())
            .openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            connectTimeout = 20_000
            readTimeout = 60_000
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
        }
        try {
            conn.outputStream.use { it.write(body.toString().toByteArray()) }
            val code = conn.responseCode
            val text = (if (code in 200..299) conn.inputStream else conn.errorStream)
                ?.bufferedReader()?.use { it.readText() } ?: ""
            val json = runCatching { JSONObject(text) }.getOrNull()
            if (code !in 200..299) {
                val msg = json?.optJSONObject("error")?.optString("message") ?: "HTTP $code"
                throw IOException(friendlyError(code, msg))
            }
            val resp = json?.optJSONArray("responses")?.optJSONObject(0) ?: return emptyList()
            resp.optJSONObject("error")?.let { throw IOException("Cloud Vision: " + it.optString("message")) }
            return parse(resp.optJSONObject("fullTextAnnotation"))
        } catch (e: java.net.UnknownHostException) {
            throw IOException("Brak internetu – tryb pisma odręcznego wymaga połączenia.")
        } finally {
            conn.disconnect()
        }
    }

    private fun friendlyError(code: Int, msg: String) = when {
        code == 400 && msg.contains("API key", true) -> "Nieprawidłowy klucz API Google Cloud Vision."
        code == 403 && msg.contains("billing", true) -> "W projekcie Google Cloud trzeba włączyć płatności (billing). Pierwsze 1000 stron miesięcznie jest bezpłatne."
        code == 403 -> "Brak dostępu do Cloud Vision API – sprawdź, czy API jest włączone w projekcie i czy klucz nie ma ograniczeń. ($msg)"
        code == 429 -> "Przekroczono limit zapytań Cloud Vision. Spróbuj za chwilę."
        else -> "Cloud Vision: $msg"
    }

    /** Składa słowa w linie według znaczników końca linii zwracanych przez Vision. */
    private fun parse(full: JSONObject?): List<OcrLine> {
        full ?: return emptyList()
        val lines = mutableListOf<OcrLine>()
        val pages = full.optJSONArray("pages") ?: return emptyList()
        for (p in 0 until pages.length()) {
            val blocks = pages.getJSONObject(p).optJSONArray("blocks") ?: continue
            for (b in 0 until blocks.length()) {
                val paras = blocks.getJSONObject(b).optJSONArray("paragraphs") ?: continue
                for (pa in 0 until paras.length()) {
                    val words = paras.getJSONObject(pa).optJSONArray("words") ?: continue
                    val sb = StringBuilder()
                    var box: Rect? = null
                    var count = 0
                    fun flush() {
                        val t = sb.toString().trim()
                        if (t.isNotEmpty() && box != null) lines += OcrLine(t, box!!, count)
                        sb.clear(); box = null; count = 0
                    }
                    for (w in 0 until words.length()) {
                        val word = words.getJSONObject(w)
                        val symbols = word.optJSONArray("symbols") ?: continue
                        var breakType = ""
                        for (s in 0 until symbols.length()) {
                            val sym = symbols.getJSONObject(s)
                            sb.append(sym.optString("text"))
                            breakType = sym.optJSONObject("property")?.optJSONObject("detectedBreak")
                                ?.optString("type") ?: ""
                        }
                        count++
                        val r = rectOf(word.optJSONObject("boundingBox"))
                        if (r != null) box = box?.apply { union(r) } ?: r
                        when (breakType) {
                            "EOL_SURE_SPACE", "LINE_BREAK" -> flush()
                            "SPACE", "SURE_SPACE" -> sb.append(' ')
                            "HYPHEN" -> { sb.append('-'); flush() }
                        }
                    }
                    flush()
                }
            }
        }
        return lines
    }

    private fun rectOf(poly: JSONObject?): Rect? {
        val v = poly?.optJSONArray("vertices") ?: return null
        if (v.length() == 0) return null
        var l = Int.MAX_VALUE; var t = Int.MAX_VALUE; var r = Int.MIN_VALUE; var b = Int.MIN_VALUE
        for (i in 0 until v.length()) {
            val o = v.getJSONObject(i)
            val x = o.optInt("x", 0); val y = o.optInt("y", 0) // Vision pomija pola równe 0
            l = min(l, x); t = min(t, y); r = max(r, x); b = max(b, y)
        }
        return if (r > l && b > t) Rect(l, t, r, b) else null
    }
}
