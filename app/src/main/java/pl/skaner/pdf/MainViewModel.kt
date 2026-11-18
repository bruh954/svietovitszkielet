package pl.skaner.pdf

import android.app.Application
import android.content.Intent
import android.provider.DocumentsContract
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

    var options by mutableStateOf(PdfOptions())

    init {
        // Usuń klucz Google zapisany przez wersję 1.1–1.2
        prefs.edit().remove("visionKey").remove("engine").apply()
    }
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

    /** Dodaje wszystkie zdjęcia z folderu (bez podfolderów), w kolejności nazw plików. */
    fun addFolder(tree: Uri, onDone: (Int) -> Unit) {
        val cr = getApplication<Application>().contentResolver
        viewModelScope.launch {
            val found = withContext(Dispatchers.IO) {
                runCatching { cr.takePersistableUriPermission(tree, Intent.FLAG_GRANT_READ_URI_PERMISSION) }
                val children = DocumentsContract.buildChildDocumentsUriUsingTree(
                    tree, DocumentsContract.getTreeDocumentId(tree))
                val list = mutableListOf<Pair<String, Uri>>()
                cr.query(children, arrayOf(
                    DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                    DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                    DocumentsContract.Document.COLUMN_MIME_TYPE
                ), null, null, null)?.use { c ->
                    while (c.moveToNext()) {
                        val mime = c.getString(2) ?: continue
                        if (!mime.startsWith("image/")) continue
                        list += (c.getString(1) ?: "") to
                            DocumentsContract.buildDocumentUriUsingTree(tree, c.getString(0))
                    }
                }
                list.sortedBy { naturalKey(it.first) }.map { it.second }
            }
            if (found.isNotEmpty()) add(found)
            onDone(found.size)
        }
    }

    /** "IMG_2.jpg" przed "IMG_10.jpg" – liczby porównywane jak liczby. */
    private fun naturalKey(name: String) =
        Regex("\\d+").replace(name.lowercase()) { it.value.padStart(12, '0') }

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
                result = builder.build(photos.toList(), options.copy(title = name), out) { p, t ->
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
