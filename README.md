# Skaner PDF – zdjęcia → PDF z wyszukiwaniem (Android)

Aplikacja składa jeden plik PDF z wielu zdjęć. Na zdjęciach rozpoznaje tekst (OCR) i dodaje go
jako **niewidoczną warstwę**, ułożoną dokładnie nad napisami. Dzięki temu w gotowym PDF działa
wyszukiwanie (Ctrl+F), zaznaczanie i kopiowanie tekstu, a strony wyglądają jak oryginalne zdjęcia.

## Funkcje
- zdjęcia z galerii (wiele naraz), z aparatu albo przez „Udostępnij → Skaner PDF” z innej aplikacji
- zmiana kolejności stron, obracanie o 90°, usuwanie
- OCR druku na telefonie (Google ML Kit), **bez internetu**, z polskimi znakami
- tryb **pisma odręcznego** (Google Cloud Vision, przez internet, wymaga klucza API)
- rozmiar strony: A4 (pion lub poziom, dobierany automatycznie) albo „jak zdjęcie”
- trzy poziomy jakości (rozmiar pliku a ostrość)
- gotowy PDF: Otwórz / Udostępnij / Zapisz… (dowolny folder, np. Pobrane albo Dysk Google)
- jedyne uprawnienie to internet, używany tylko w trybie pisma odręcznego (galeria i aparat działają przez systemowe okna wyboru)

## Jak zbudować
1. Zainstaluj **Android Studio** (wersja Ladybug 2024.2 albo nowsza).
2. *File → Open* i wskaż folder `SkanerPDF`. Poczekaj, aż Gradle pobierze zależności (za pierwszym razem trwa to kilka minut).
3. Podłącz telefon z włączonym debugowaniem USB i kliknij ▶ **Run**.
   Możesz też zbudować plik APK: *Build → Build App Bundle(s) / APK(s) → Build APK(s)*.
   Plik pojawi się w `app/build/outputs/apk/debug/app-debug.apk`; przenieś go na telefon i zainstaluj.

Z wiersza poleceń (z zainstalowanym Android SDK): `./gradlew assembleDebug`

Wymagania: Android 7.0 (API 24) lub nowszy.

## Struktura
| Plik | Co robi |
|---|---|
| `PdfBuilder.kt` | wczytuje zdjęcia (EXIF, skalowanie), uruchamia OCR, składa PDF (PdfBox-Android) z niewidocznym tekstem |
| `MainViewModel.kt` | lista stron, ustawienia, generowanie w tle, zapis |
| `MainActivity.kt` | interfejs (Jetpack Compose) |

## Uwagi
- Zdjęcia dokumentów wychodzą najlepiej, gdy kartka jest płasko, dobrze oświetlona i zajmuje większość kadru.
- Model OCR jest wbudowany w aplikację (ok. 4 MB), więc działa od razu, także offline.
- Rozpoznawany jest alfabet łaciński (polski, angielski, niemiecki itd.). Do cyrylicy lub pisma azjatyckiego
  trzeba dodać odpowiedni pakiet ML Kit (np. `text-recognition-chinese`).

## Pismo odręczne – klucz Google Cloud Vision
Wbudowany OCR (ML Kit) dobrze czyta druk, ale słabo pismo odręczne. Tryb „Pismo odręczne” wysyła
zdjęcia do Google Cloud Vision (`DOCUMENT_TEXT_DETECTION`), który zwraca tekst wraz z położeniem słów.

1. Wejdź na https://console.cloud.google.com, zaloguj się kontem Google i utwórz projekt.
2. Włącz płatności (Billing) dla projektu. Google tego wymaga, ale pierwsze 1000 stron miesięcznie jest bezpłatne.
3. Włącz **Cloud Vision API**: *APIs & Services → Library → Cloud Vision API → Enable*.
4. Utwórz klucz: *APIs & Services → Credentials → Create credentials → API key*.
   Zalecane: w ustawieniach klucza ogranicz go tylko do Cloud Vision API.
5. W aplikacji włącz OCR, wybierz „Pismo odręczne” i wklej klucz. Aplikacja go zapamięta.
