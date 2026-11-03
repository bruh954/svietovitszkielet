# Śviętovit (szkielet)

Sam program: ekran główny, silnik lekcji i jeden kurs (日本語) z jednym działem. Służy do sprawdzenia,
czy aplikacja uruchamia się na telefonie. Kolejne lekcje i kursy dodajemy po udanym uruchomieniu.

Na komputerze: `pip install kivy` i `python main.py`.
Na Androida: GitHub Actions buduje APK (zakładka Actions, artefakt `svietovit-szkielet-apk`).

Gdyby aplikacja zamykała się na telefonie, wklej `main_diag.py` w miejsce `main.py`: pokaże etapy startu.
