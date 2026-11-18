package pl.skaner.pdf

import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.DocumentsContract
import android.provider.MediaStore
import java.io.File
import java.io.IOException

object Cleanup {

    private const val FOLDER = "SkanerPDF"

    /**
     * Zapisuje PDF na stałe w Pobrane/SkanerPDF i sprawdza, czy zapisał się w całości.
     * Zwraca ścieżkę do pokazania użytkownikowi. Rzuca wyjątek, jeśli się nie udało –
     * wtedy zdjęcia NIE są usuwane.
     */
    fun saveToDownloads(ctx: Context, src: File): String {
        val cr = ctx.contentResolver
        if (Build.VERSION.SDK_INT >= 29) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, src.name)
                put(MediaStore.Downloads.MIME_TYPE, "application/pdf")
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/" + FOLDER)
                put(MediaStore.Downloads.IS_PENDING, 1)
            }
            val uri = cr.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: throw IOException("Nie można utworzyć pliku w Pobranych")
            try {
                val written = cr.openOutputStream(uri)!!.use { out -> src.inputStream().use { it.copyTo(out) } }
                if (written != src.length()) throw IOException("PDF zapisał się niekompletnie")
                cr.update(uri, ContentValues().apply { put(MediaStore.Downloads.IS_PENDING, 0) }, null, null)
            } catch (e: Exception) {
                runCatching { cr.delete(uri, null, null) }
                throw e
            }
            val name = cr.query(uri, arrayOf(MediaStore.Downloads.DISPLAY_NAME), null, null, null)
                ?.use { if (it.moveToFirst()) it.getString(0) else null } ?: src.name
            return "Pobrane/$FOLDER/$name"
        } else {
            @Suppress("DEPRECATION")
            val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), FOLDER)
            dir.mkdirs()
            var target = File(dir, src.name)
            var n = 1
            while (target.exists()) target = File(dir, src.nameWithoutExtension + " ($n).pdf").also { n++ }
            src.copyTo(target)
            if (target.length() != src.length()) throw IOException("PDF zapisał się niekompletnie")
            MediaScannerConnection.scanFile(ctx, arrayOf(target.path), arrayOf("application/pdf"), null)
            return "Pobrane/$FOLDER/${target.name}"
        }
    }

    class Plan(val media: List<Uri>, val deletedDirectly: Int, val failed: Int)

    /**
     * Usuwa, co się da, od razu (zdjęcia z aparatu w aplikacji, pliki wybrane przez Pliki/Folder).
     * Zdjęcia z galerii telefonu zwraca w [Plan.media] – na Androidzie 11+ ich usunięcie
     * wymaga systemowego okna z prośbą o zgodę.
     */
    fun deletePhotos(ctx: Context, uris: List<Uri>): Plan {
        val cr = ctx.contentResolver
        val media = linkedSetOf<Uri>()
        var deleted = 0
        var failed = 0
        for (u in uris.distinct()) {
            when {
                // zdjęcie z aparatu zapisane tylko w pamięci podręcznej aplikacji
                u.authority == ctx.packageName + ".files" -> {
                    val f = File(File(ctx.cacheDir, "camera"), u.lastPathSegment ?: "")
                    if (f.exists() && f.delete()) deleted++ else failed++
                }
                u.authority == MediaStore.AUTHORITY && u.pathSegments.firstOrNull() != "picker" -> media += u
                // „Pliki” → Obrazy: dokument to tak naprawdę pozycja z galerii
                u.authority == "com.android.providers.media.documents" -> {
                    val id = DocumentsContract.getDocumentId(u).substringAfter(':').toLongOrNull()
                    if (id != null) media += ContentUris.withAppendedId(
                        MediaStore.Images.Media.EXTERNAL_CONTENT_URI, id) else failed++
                }
                DocumentsContract.isDocumentUri(ctx, u) -> {
                    val ok = runCatching { DocumentsContract.deleteDocument(cr, u) }.getOrDefault(false)
                    if (ok) deleted++ else failed++
                }
                else -> failed++
            }
        }
        if (Build.VERSION.SDK_INT < 30 && media.isNotEmpty()) {
            // Android 10 i starsze: usuwamy bezpośrednio (uprawnienie do zapisu)
            for (m in media) {
                val ok = runCatching { cr.delete(m, null, null) > 0 }.getOrDefault(false)
                if (ok) deleted++ else failed++
            }
            return Plan(emptyList(), deleted, failed)
        }
        return Plan(media.toList(), deleted, failed)
    }
}
