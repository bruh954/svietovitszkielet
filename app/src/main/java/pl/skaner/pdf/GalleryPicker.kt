package pl.skaner.pdf

import android.content.ContentUris
import android.content.Context
import android.net.Uri
import android.provider.MediaStore
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class GalleryImage(val id: Long, val uri: Uri, val bucketId: Long, val bucket: String)

/** Wszystkie zdjęcia z pamięci telefonu, od najnowszych. */
suspend fun loadGallery(ctx: Context): List<GalleryImage> = withContext(Dispatchers.IO) {
    val out = mutableListOf<GalleryImage>()
    val base = MediaStore.Images.Media.EXTERNAL_CONTENT_URI
    ctx.contentResolver.query(
        base,
        arrayOf(
            MediaStore.Images.Media._ID,
            MediaStore.Images.Media.BUCKET_ID,
            MediaStore.Images.Media.BUCKET_DISPLAY_NAME
        ),
        null, null,
        "${MediaStore.Images.Media.DATE_TAKEN} DESC, ${MediaStore.Images.Media.DATE_ADDED} DESC"
    )?.use { c ->
        while (c.moveToNext()) {
            val id = c.getLong(0)
            out += GalleryImage(id, ContentUris.withAppendedId(base, id), c.getLong(1), c.getString(2) ?: "Inne")
        }
    }
    out
}

/**
 * Własna galeria z numerami stron. Kolejność stron = kolejność zaznaczania.
 * „Zaznacz wszystkie” dodaje zdjęcia z bieżącego albumu od najstarszego do najnowszego.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GalleryPicker(firstPage: Int, onDone: (List<Uri>) -> Unit, onCancel: () -> Unit) {
    val ctx = LocalContext.current
    var all by remember { mutableStateOf<List<GalleryImage>?>(null) }
    var album by remember { mutableStateOf<Long?>(null) }
    val selected = remember { mutableStateListOf<GalleryImage>() }

    LaunchedEffect(Unit) { all = runCatching { loadGallery(ctx) }.getOrDefault(emptyList()) }
    BackHandler { onCancel() }

    val albums = remember(all) {
        (all ?: emptyList()).groupBy { it.bucketId }
            .map { (id, list) -> Triple(id, list.first().bucket, list.size) }
            .sortedByDescending { it.third }
    }
    val shown = remember(all, album) { (all ?: emptyList()).filter { album == null || it.bucketId == album } }

    Scaffold(
        topBar = {
            TopAppBar(
                navigationIcon = {
                    IconButton(onClick = onCancel) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Wróć") }
                },
                title = {
                    Text(if (selected.isEmpty()) "Wybierz zdjęcia"
                         else "Zaznaczono: ${selected.size}")
                },
                actions = {
                    val allShownSelected = shown.isNotEmpty() && shown.all { it in selected }
                    TextButton(onClick = {
                        if (allShownSelected) selected.removeAll(shown.toSet())
                        else shown.asReversed().forEach { if (it !in selected) selected += it }
                    }) { Text(if (allShownSelected) "Odznacz" else "Zaznacz wszystkie") }
                }
            )
        },
        bottomBar = {
            Surface(tonalElevation = 3.dp) {
                Button(
                    onClick = { onDone(selected.map { it.uri }) },
                    enabled = selected.isNotEmpty(),
                    modifier = Modifier.fillMaxWidth().navigationBarsPadding().padding(12.dp)
                ) {
                    Text(when (selected.size) {
                        0 -> "Zaznacz zdjęcia"
                        1 -> "Dodaj jako stronę $firstPage"
                        else -> "Dodaj jako strony $firstPage–${firstPage + selected.size - 1}"
                    })
                }
            }
        }
    ) { pad ->
        Column(Modifier.fillMaxSize().padding(pad)) {
            if (albums.size > 1) LazyRow(
                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                item {
                    FilterChip(selected = album == null, onClick = { album = null },
                        label = { Text("Wszystkie (${all?.size ?: 0})") })
                }
                items(albums, key = { it.first }) { (id, name, count) ->
                    FilterChip(selected = album == id, onClick = { album = id },
                        label = { Text("$name ($count)") })
                }
            }
            when {
                all == null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                shown.isEmpty() -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Brak zdjęć")
                }
                else -> LazyVerticalGrid(
                    columns = GridCells.Adaptive(96.dp),
                    contentPadding = PaddingValues(2.dp),
                    modifier = Modifier.fillMaxSize()
                ) {
                    items(shown, key = { it.id }) { img ->
                        val idx = selected.indexOf(img)
                        Box(
                            Modifier.padding(2.dp).aspectRatio(1f)
                                .clickable { if (idx >= 0) selected.removeAt(idx) else selected += img }
                        ) {
                            AsyncImage(
                                model = img.uri, contentDescription = null,
                                contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize()
                            )
                            if (idx >= 0) {
                                Box(Modifier.fillMaxSize()
                                    .background(Color.Black.copy(alpha = 0.35f))
                                    .border(3.dp, MaterialTheme.colorScheme.primary))
                                Box(
                                    Modifier.align(Alignment.TopEnd).padding(5.dp)
                                        .defaultMinSize(minWidth = 28.dp, minHeight = 28.dp)
                                        .background(MaterialTheme.colorScheme.primary, CircleShape)
                                        .padding(horizontal = 6.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text("${firstPage + idx}", color = MaterialTheme.colorScheme.onPrimary,
                                        fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                }
                            } else {
                                Box(Modifier.align(Alignment.TopEnd).padding(6.dp).size(22.dp)
                                    .border(2.dp, Color.White, CircleShape))
                            }
                        }
                    }
                }
            }
        }
    }
}
