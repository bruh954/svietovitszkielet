package pl.skaner.pdf

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import java.io.File

class MainActivity : ComponentActivity() {

    private val vm: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        if (savedInstanceState == null) handleShare(intent)
        setContent {
            MaterialTheme(colorScheme = lightColorScheme()) { MainScreen(vm) }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleShare(intent)
    }

    /** Zdjęcia udostępnione z galerii innej aplikacji. */
    private fun handleShare(intent: Intent?) {
        intent ?: return
        val uris: List<Uri> = when (intent.action) {
            Intent.ACTION_SEND -> listOfNotNull(
                if (Build.VERSION.SDK_INT >= 33) intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
                else @Suppress("DEPRECATION") intent.getParcelableExtra(Intent.EXTRA_STREAM)
            )
            Intent.ACTION_SEND_MULTIPLE ->
                (if (Build.VERSION.SDK_INT >= 33) intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM, Uri::class.java)
                else @Suppress("DEPRECATION") intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM)) ?: emptyList()
            else -> emptyList()
        }
        if (uris.isNotEmpty()) vm.add(uris)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(vm: MainViewModel) {
    val ctx = LocalContext.current
    var pendingCameraUri by remember { mutableStateOf<Uri?>(null) }

    val pickPhotos = rememberLauncherForActivityResult(
        ActivityResultContracts.PickMultipleVisualMedia(100)
    ) { uris -> if (uris.isNotEmpty()) vm.add(uris) }

    val takePhoto = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        val u = pendingCameraUri
        if (ok && u != null) vm.add(listOf(u))
    }

    val saveAs = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/pdf")
    ) { target ->
        if (target != null) vm.saveTo(target) { ok ->
            Toast.makeText(ctx, if (ok) "Zapisano PDF" else "Nie udało się zapisać", Toast.LENGTH_SHORT).show()
        }
    }

    fun launchCamera() {
        val dir = File(ctx.cacheDir, "camera").apply { mkdirs() }
        val file = File(dir, "IMG_${System.currentTimeMillis()}.jpg")
        val uri = FileProvider.getUriForFile(ctx, ctx.packageName + ".files", file)
        pendingCameraUri = uri
        try { takePhoto.launch(uri) } catch (e: ActivityNotFoundException) {
            Toast.makeText(ctx, "Brak aplikacji aparatu", Toast.LENGTH_SHORT).show()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Skaner PDF") },
                actions = {
                    if (vm.photos.isNotEmpty() && !vm.busy)
                        IconButton(onClick = { vm.clear() }) { Icon(Icons.Default.DeleteSweep, "Wyczyść") }
                }
            )
        },
        bottomBar = {
            Surface(tonalElevation = 3.dp) {
                Column(Modifier.fillMaxWidth().navigationBarsPadding().padding(12.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(
                            onClick = { pickPhotos.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
                            enabled = !vm.busy, modifier = Modifier.weight(1f)
                        ) { Icon(Icons.Default.PhotoLibrary, null); Spacer(Modifier.width(6.dp)); Text("Galeria") }
                        OutlinedButton(
                            onClick = { launchCamera() },
                            enabled = !vm.busy, modifier = Modifier.weight(1f)
                        ) { Icon(Icons.Default.PhotoCamera, null); Spacer(Modifier.width(6.dp)); Text("Aparat") }
                    }
                    Spacer(Modifier.height(8.dp))
                    Button(
                        onClick = { vm.generate() },
                        enabled = vm.photos.isNotEmpty() && !vm.busy,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Default.PictureAsPdf, null); Spacer(Modifier.width(6.dp))
                        Text(if (vm.options.ocr) "Utwórz PDF z wyszukiwaniem" else "Utwórz PDF")
                    }
                }
            }
        }
    ) { pad ->
        LazyColumn(
            Modifier.fillMaxSize().padding(pad),
            contentPadding = PaddingValues(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            item { OptionsCard(vm) }

            if (vm.busy) item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        val (p, t) = vm.progress
                        Text(if (vm.options.ocr) "Rozpoznawanie tekstu i składanie… strona $p z $t"
                             else "Składanie… strona $p z $t")
                        Spacer(Modifier.height(8.dp))
                        LinearProgressIndicator(
                            progress = { if (t == 0) 0f else p / t.toFloat() },
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }

            vm.error?.let { msg -> item {
                Card(colors = CardDefaults.cardColors(MaterialTheme.colorScheme.errorContainer)) {
                    Text(msg, Modifier.padding(16.dp))
                }
            } }

            vm.result?.let { r -> item { ResultCard(r, vm, onSave = { saveAs.launch(vm.currentFileName()) }) } }

            if (vm.photos.isEmpty()) item {
                Box(Modifier.fillMaxWidth().padding(vertical = 48.dp), contentAlignment = Alignment.Center) {
                    Text("Dodaj zdjęcia z galerii albo zrób je aparatem.\nKażde zdjęcie to jedna strona PDF.",
                        style = MaterialTheme.typography.bodyLarge)
                }
            } else item {
                Text("Strony (${vm.photos.size})", style = MaterialTheme.typography.titleMedium)
            }

            itemsIndexed(vm.photos, key = { i, p -> "${p.uri}#$i" }) { i, photo ->
                PhotoRow(i, photo, vm)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun OptionsCard(vm: MainViewModel) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedTextField(
                value = vm.fileName, onValueChange = { vm.fileName = it },
                label = { Text("Nazwa pliku") }, singleLine = true,
                suffix = { Text(".pdf") }, enabled = !vm.busy,
                modifier = Modifier.fillMaxWidth()
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Rozpoznawanie tekstu (OCR)")
                    Text("PDF będzie można przeszukiwać i kopiować z niego tekst",
                        style = MaterialTheme.typography.bodySmall)
                }
                Switch(checked = vm.options.ocr, enabled = !vm.busy,
                    onCheckedChange = { vm.options = vm.options.copy(ocr = it) })
            }
            Text("Rozmiar strony", style = MaterialTheme.typography.labelLarge)
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                val sizes = listOf(PageSize.A4 to "A4", PageSize.FIT_PHOTO to "Jak zdjęcie")
                sizes.forEachIndexed { i, (v, label) ->
                    SegmentedButton(
                        selected = vm.options.pageSize == v, enabled = !vm.busy,
                        onClick = { vm.options = vm.options.copy(pageSize = v) },
                        shape = SegmentedButtonDefaults.itemShape(i, sizes.size)
                    ) { Text(label) }
                }
            }
            Text("Jakość", style = MaterialTheme.typography.labelLarge)
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                val qs = Quality.entries
                qs.forEachIndexed { i, q ->
                    SegmentedButton(
                        selected = vm.options.quality == q, enabled = !vm.busy,
                        onClick = { vm.options = vm.options.copy(quality = q) },
                        shape = SegmentedButtonDefaults.itemShape(i, qs.size)
                    ) { Text(q.label) }
                }
            }
        }
    }
}

@Composable
private fun PhotoRow(i: Int, photo: PhotoItem, vm: MainViewModel) {
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
            AsyncImage(
                model = photo.uri, contentDescription = "Strona ${i + 1}",
                contentScale = ContentScale.Fit,
                modifier = Modifier.size(80.dp).clip(RoundedCornerShape(6.dp)).rotate(photo.rotation.toFloat())
            )
            Text("Strona ${i + 1}", Modifier.weight(1f).padding(horizontal = 12.dp))
            val enabled = !vm.busy
            IconButton(onClick = { vm.move(i, -1) }, enabled = enabled && i > 0) {
                Icon(Icons.Default.ArrowUpward, "W górę") }
            IconButton(onClick = { vm.move(i, 1) }, enabled = enabled && i < vm.photos.lastIndex) {
                Icon(Icons.Default.ArrowDownward, "W dół") }
            IconButton(onClick = { vm.rotate(i) }, enabled = enabled) {
                Icon(Icons.Default.RotateRight, "Obróć") }
            IconButton(onClick = { vm.remove(i) }, enabled = enabled) {
                Icon(Icons.Default.Delete, "Usuń") }
        }
    }
}

@Composable
private fun ResultCard(r: PdfResult, vm: MainViewModel, onSave: () -> Unit) {
    val ctx = LocalContext.current
    fun uri() = FileProvider.getUriForFile(ctx, ctx.packageName + ".files", r.file)

    Card(colors = CardDefaults.cardColors(MaterialTheme.colorScheme.primaryContainer)) {
        Column(Modifier.padding(16.dp)) {
            Text("Gotowe: ${r.file.name}", style = MaterialTheme.typography.titleMedium)
            val kb = r.file.length() / 1024
            val size = if (kb > 1024) "%.1f MB".format(kb / 1024f) else "$kb KB"
            Text(buildString {
                append("${r.pages} str. · $size")
                if (vm.options.ocr) append(" · rozpoznane słowa: ${r.words}")
            })
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = {
                    val i = Intent(Intent.ACTION_VIEW).setDataAndType(uri(), "application/pdf")
                        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    try { ctx.startActivity(i) } catch (e: ActivityNotFoundException) {
                        Toast.makeText(ctx, "Brak aplikacji do PDF", Toast.LENGTH_SHORT).show()
                    }
                }) { Text("Otwórz") }
                FilledTonalButton(onClick = {
                    val i = Intent(Intent.ACTION_SEND).setType("application/pdf")
                        .putExtra(Intent.EXTRA_STREAM, uri())
                        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    ctx.startActivity(Intent.createChooser(i, "Udostępnij PDF"))
                }) { Text("Udostępnij") }
                FilledTonalButton(onClick = onSave) { Text("Zapisz…") }
            }
        }
    }
}
