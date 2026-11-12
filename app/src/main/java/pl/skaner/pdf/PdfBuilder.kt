package pl.skaner.pdf

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import androidx.exifinterface.media.ExifInterface
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.pdmodel.PDPage
import com.tom_roush.pdfbox.pdmodel.PDPageContentStream
import com.tom_roush.pdfbox.pdmodel.common.PDRectangle
import com.tom_roush.pdfbox.pdmodel.font.PDFont
import com.tom_roush.pdfbox.pdmodel.font.PDType0Font
import com.tom_roush.pdfbox.pdmodel.font.PDType1Font
import com.tom_roush.pdfbox.pdmodel.graphics.image.JPEGFactory
import com.tom_roush.pdfbox.pdmodel.graphics.state.RenderingMode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import java.io.File
import java.text.Normalizer
import kotlin.math.max
import kotlin.math.min

data class PhotoItem(val uri: Uri, val rotation: Int = 0)

enum class PageSize { A4, FIT_PHOTO }

enum class OcrEngine(val label: String) {
    PRINT("Druk (offline)"),
    HANDWRITING("Pismo odręczne")
}

enum class Quality(val label: String, val maxSide: Int, val jpeg: Float) {
    ECONOMY("Mały plik", 1600, 0.65f),
    STANDARD("Standard", 2400, 0.8f),
    HIGH("Wysoka", 3200, 0.9f)
}

data class PdfOptions(
    val ocr: Boolean = true,
    val engine: OcrEngine = OcrEngine.PRINT,
    val apiKey: String = "",
    val pageSize: PageSize = PageSize.A4,
    val quality: Quality = Quality.STANDARD,
    val title: String = "Skan"
)

data class PdfResult(val file: File, val pages: Int, val words: Int)

/**
 * Składa PDF ze zdjęć. Każda strona = zdjęcie (JPEG) + niewidoczna warstwa tekstu z OCR
 * ułożona dokładnie nad napisami na zdjęciu, dzięki czemu PDF da się przeszukiwać,
 * zaznaczać i kopiować z niego tekst.
 */
class PdfBuilder(private val context: Context) {

    init {
        PDFBoxResourceLoader.init(context.applicationContext)
    }

    suspend fun build(
        photos: List<PhotoItem>,
        options: PdfOptions,
        output: File,
        onProgress: (page: Int, total: Int) -> Unit
    ): PdfResult = withContext(Dispatchers.Default) {
        val handwriting = options.ocr && options.engine == OcrEngine.HANDWRITING
        if (handwriting) require(options.apiKey.isNotBlank()) {
            "Wpisz klucz API Google Cloud Vision, żeby rozpoznawać pismo odręczne."
        }
        val recognizer = if (options.ocr && !handwriting)
            TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS) else null
        var words = 0

        PDDocument().use { doc ->
            doc.documentInformation.title = options.title
            doc.documentInformation.creator = "Skaner PDF"
            val font = if (options.ocr) loadUnicodeFont(doc) else null

            photos.forEachIndexed { index, photo ->
                onProgress(index + 1, photos.size)

                val bmp = loadBitmap(photo.uri, photo.rotation, options.quality.maxSide)
                val w = bmp.width.toFloat()
                val h = bmp.height.toFloat()

                // --- geometria strony ---
                val landscape = w > h
                val pageRect = when (options.pageSize) {
                    PageSize.A4 -> if (landscape)
                        PDRectangle(PDRectangle.A4.height, PDRectangle.A4.width) else PDRectangle.A4
                    PageSize.FIT_PHOTO -> {
                        val pw = if (landscape) PDRectangle.A4.height else PDRectangle.A4.width
                        PDRectangle(pw, pw * h / w)
                    }
                }
                val s = min(pageRect.width / w, pageRect.height / h)
                val dw = w * s
                val dh = h * s
                val ox = (pageRect.width - dw) / 2f
                val oy = (pageRect.height - dh) / 2f

                // --- OCR ---
                val lines: List<OcrLine> = when {
                    handwriting -> withContext(Dispatchers.IO) { CloudVisionOcr.recognize(bmp, options.apiKey) }
                    recognizer != null -> recognizer.process(InputImage.fromBitmap(bmp, 0)).await()
                        .textBlocks.flatMap { b -> b.lines }
                        .mapNotNull { l -> l.boundingBox?.let { OcrLine(l.text, it, l.elements.size) } }
                    else -> emptyList()
                }

                val page = PDPage(pageRect)
                doc.addPage(page)
                val image = JPEGFactory.createFromImage(doc, bmp, options.quality.jpeg)
                bmp.recycle()

                PDPageContentStream(doc, page).use { cs ->
                    cs.drawImage(image, ox, oy, dw, dh)

                    if (font != null) {
                        for (line in lines) {
                            val box = line.box
                            val str = sanitize(line.text, font).trim()
                            if (str.isEmpty()) continue
                            words += line.words

                            val bw = box.width() * s
                            val bh = box.height() * s
                            if (bw < 1f || bh < 1f) continue
                            val bx = ox + box.left * s
                            val bottom = oy + (h - box.bottom) * s // PDF: początek układu na dole

                            val fontSize = max(1f, bh * 0.9f)
                            val textW = font.getStringWidth(str) / 1000f * fontSize
                            if (textW <= 0f) continue

                            cs.beginText()
                            cs.setRenderingMode(RenderingMode.NEITHER) // tekst niewidoczny
                            cs.setFont(font, fontSize)
                            cs.setHorizontalScaling(bw / textW * 100f)  // rozciągnij do szerokości linii
                            cs.newLineAtOffset(bx, bottom + bh * 0.22f)
                            cs.showText(str)
                            cs.endText()
                        }
                    }
                }
            }
            output.parentFile?.mkdirs()
            doc.save(output)
            recognizer?.close()
            PdfResult(output, photos.size, words)
        }
    }

    // ---------------------------------------------------------------------------------

    /** Wczytuje zdjęcie, zmniejsza do maxSide, uwzględnia EXIF i ręczny obrót. */
    private fun loadBitmap(uri: Uri, extraRotation: Int, maxSide: Int): Bitmap {
        val cr = context.contentResolver
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        cr.openInputStream(uri).use { BitmapFactory.decodeStream(it, null, bounds) }
        require(bounds.outWidth > 0) { "Nie można odczytać zdjęcia: $uri" }

        var sample = 1
        while (max(bounds.outWidth, bounds.outHeight) / (sample * 2) >= maxSide) sample *= 2
        val decoded = cr.openInputStream(uri).use {
            BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply { inSampleSize = sample })
        } ?: error("Nie można zdekodować zdjęcia")

        val m = Matrix()
        val orientation = try {
            cr.openInputStream(uri)?.use { ExifInterface(it).getAttributeInt(
                ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL) }
                ?: ExifInterface.ORIENTATION_NORMAL
        } catch (e: Exception) { ExifInterface.ORIENTATION_NORMAL }
        when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> m.postRotate(90f)
            ExifInterface.ORIENTATION_ROTATE_180 -> m.postRotate(180f)
            ExifInterface.ORIENTATION_ROTATE_270 -> m.postRotate(270f)
            ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> m.postScale(-1f, 1f)
            ExifInterface.ORIENTATION_FLIP_VERTICAL -> m.postScale(1f, -1f)
            ExifInterface.ORIENTATION_TRANSPOSE -> { m.postRotate(90f); m.postScale(-1f, 1f) }
            ExifInterface.ORIENTATION_TRANSVERSE -> { m.postRotate(270f); m.postScale(-1f, 1f) }
        }
        if (extraRotation % 360 != 0) m.postRotate(extraRotation.toFloat())

        val longest = max(decoded.width, decoded.height)
        if (longest > maxSide) {
            val f = maxSide.toFloat() / longest
            m.postScale(f, f)
        }
        if (m.isIdentity) return decoded
        val out = Bitmap.createBitmap(decoded, 0, 0, decoded.width, decoded.height, m, true)
        if (out !== decoded) decoded.recycle()
        return out
    }

    /** Czcionka z polskimi znakami: systemowe Roboto/Noto/Droid, w ostateczności Helvetica. */
    private fun loadUnicodeFont(doc: PDDocument): PDFont {
        val candidates = listOf(
            "/system/fonts/Roboto-Regular.ttf",
            "/system/fonts/RobotoStatic-Regular.ttf",
            "/system/fonts/NotoSans-Regular.ttf",
            "/system/fonts/DroidSans.ttf",
            "/system/fonts/DejaVuSans.ttf"
        )
        for (path in candidates) {
            val f = File(path)
            if (!f.canRead()) continue
            try {
                val font = PDType0Font.load(doc, f)
                font.encode("Zażółć gęślą jaźń") // test polskich znaków
                return font
            } catch (_: Throwable) { /* następna */ }
        }
        return PDType1Font.HELVETICA
    }

    /** Usuwa znaki, których czcionka nie potrafi zakodować (zamienia ą→a itd. jeśli trzeba). */
    private fun sanitize(input: String, font: PDFont): String {
        val sb = StringBuilder()
        var i = 0
        while (i < input.length) {
            val cp = input.codePointAt(i)
            i += Character.charCount(cp)
            val ch = String(Character.toChars(cp))
            if (canEncode(font, ch)) { sb.append(ch); continue }
            val folded = fold(ch)
            if (folded.isNotEmpty() && canEncode(font, folded)) sb.append(folded)
            else if (canEncode(font, " ")) sb.append(' ')
        }
        return sb.toString()
    }

    private fun canEncode(font: PDFont, s: String): Boolean =
        try { font.encode(s); true } catch (_: Throwable) { false }

    private fun fold(s: String): String = when (s) {
        "ł" -> "l"; "Ł" -> "L"
        "‘", "’" -> "'"; "“", "”", "„" -> "\""
        "–", "—" -> "-"
        else -> Normalizer.normalize(s, Normalizer.Form.NFD).replace(Regex("\\p{M}+"), "")
    }
}
