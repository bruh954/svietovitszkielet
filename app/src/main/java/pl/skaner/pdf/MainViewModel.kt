package pl.skaner.pdf

import android.app.Application
import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainViewModel(app: Application) : AndroidViewModel(app) {

    val photos = mutableStateListOf<PhotoItem>()

    private val prefs = app.getSharedPreferences("ustawienia", 0)

    var options by mutableStateOf(PdfOptions(
        engine = runCatching { OcrEngine.valueOf(prefs.getString("engine", null) ?: "") }
            .getOrDefault(OcrEngine.PRINT)
    ))
    var apiKey by mutableStateOf(prefs.getString("visionKey", "") ?: "")
        private set

    fun updateApiKey(k: String) { apiKey = k; prefs.edit().putString("visionKey", k.trim()).apply() }
    fun updateEngine(e: OcrEngine) { options = options.copy(engine = e); prefs.edit().putString("engine", e.name).apply() }
    var fileName by mutableStateOf(defaultName())
    var busy by mutableStateOf(false); private set
    var progress by mutableStateOf(0 to 0); private set
    var result by mutableStateOf<PdfResult?>(null); private set
    var error by mutableStateOf<String?>(null)

    private val builder by lazy { PdfBuilder(app) }

    fun add(uris: List<Uri>) {
        photos.addAll(uris.map { PhotoItem(it) })
        result = null
    }

    fun remove(i: Int) { photos.removeAt(i); result = null }
    fun rotate(i: Int) { photos[i] = photos[i].copy(rotation = (photos[i].rotation + 90) % 360); result = null }
    fun move(i: Int, delta: Int) {
        val j = i + delta
        if (j !in photos.indices) return
        val item = photos.removeAt(i); photos.add(j, item); result = null
    }
    fun clear() { photos.clear(); result = null; fileName = defaultName() }

    fun generate() {
        if (photos.isEmpty() || busy) return
        busy = true; error = null; result = null
        val name = safeName(fileName)
        val out = File(getApplication<Application>().cacheDir, "pdf/$name.pdf")
        viewModelScope.launch {
            try {
                result = builder.build(photos.toList(), options.copy(title = name, apiKey = apiKey), out) { p, t ->
                    progress = p to t
                }
            } catch (t: Throwable) {
                error = "Błąd: ${t.message ?: t.javaClass.simpleName}"
            } finally {
                busy = false
            }
        }
    }

    /** Kopiuje gotowy PDF w miejsce wybrane przez użytkownika (Zapisz jako…). */
    fun saveTo(target: Uri, onDone: (Boolean) -> Unit) {
        val src = result?.file ?: return
        viewModelScope.launch {
            val ok = withContext(Dispatchers.IO) {
                runCatching {
                    getApplication<Application>().contentResolver.openOutputStream(target)!!.use { out ->
                        src.inputStream().use { it.copyTo(out) }
                    }
                }.isSuccess
            }
            onDone(ok)
        }
    }

    fun currentFileName() = safeName(fileName) + ".pdf"

    private fun safeName(s: String) =
        s.trim().removeSuffix(".pdf").replace(Regex("[\\\\/:*?\"<>|]"), "_").ifBlank { defaultName() }

    private fun defaultName() =
        "Skan_" + SimpleDateFormat("yyyy-MM-dd_HHmm", Locale.getDefault()).format(Date())
}
