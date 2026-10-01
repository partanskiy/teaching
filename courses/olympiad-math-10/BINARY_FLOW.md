# Обновление материалов курса

[Общая схема хранения и лимиты](../../BINARY_FLOW.md): официальные PDF и готовые планы находятся в GitHub LFS, исходные данные и код - в обычном Git. Скачиваемые Releases остаются дополнительными снимками.

## Получение материалов

С установленным Git LFS обычный git clone teaching автоматически получает архив и четыре готовых файла планов. Если клон уже создан без LFS, выполнить git lfs install и git lfs pull из корня репозитория.

Из папки courses/olympiad-math-10:

```sh
python scripts/restore_materials.py
```

Команда проверяет SHA256 422 оригиналов и извлекает текст для поиска без сетевых загрузок. При отсутствии или изменении оригинала останавливается с пояснением. Явный --release скачивает зафиксированный ZIP из data/release.json; --from-file использует ранее скачанный ZIP. Совпадающие файлы не перезаписываются, несовпадающие не заменяются без --replace. Снимок релиза может отставать от main.

Для работы без Git можно скачать olympiad-math-offline.zip из релиза курса, распаковать его и открыть index.html. Корень этого ZIP - сам курс; команды scripts/... выполняются из распакованной папки.

## Синхронизация планов

Единый источник занятий - data/lessons.json, который строится scripts/make_course.py. Автор, учебный год и разделы находятся в data/program.json. План для сдачи и рабочий план используют одинаковые темы, порядок, цели и часы. Рабочий план дополнительно содержит задачи, домашнюю работу и методические пояснения.

```sh
python scripts/make_course.py
python scripts/publish.py
python scripts/export_documents.py
python scripts/check_plans.py
python scripts/validate.py
node scripts/check_catalog.js
```

Ручную правку готового документа нужно перенести в исходники. При содержательных изменениях пересобирать оба DOCX и PDF вместе и добавлять их через git add. CI получает только четыре готовых плана через LFS и сравнивает официальный DOCX с новой сборкой без учета времени создания. Проверка также сверяет календарную таблицу, часы, автора, учебный год и рабочие документы.

## Работа через PR

Начать ветку, выполнить изменения и проверки. Коммиты писать на английском в формате Conventional Commits, разделяя изменения по смыслу. Например, из корня репозитория:

```sh
git switch -c course/refresh-programme
git add courses/olympiad-math-10/data courses/olympiad-math-10/course courses/olympiad-math-10/research courses/olympiad-math-10/site
git commit -m "feat(course): update curriculum and synchronized plans"
git lfs fsck
git push -u origin course/refresh-programme
gh pr create --repo partanskiy/teaching --base main --title "Update the course programme" --body-file /path/to/reviewed-pr-description.md
```

Hook pre-push загружает оригиналы в LFS перед отправкой коммитов. Не обходить hook и не заменять указатели вручную. main защищен; после проверок используется rebase merge.

Оригиналы олимпиады не редактируются. Каждый новый файл добавляется вместе с происхождением и SHA256. Если издатель заменил содержимое, измененная сумма отмечается явно и файл проходит повторную проверку.

## Дополнительный релиз

Для готового снимка из папки курса:

```sh
python scripts/package_release.py --tag olympiad-math-10-NEW_VERSION
```

Заменить NEW_VERSION новой версией. Скрипт проверяет архив и планы, создает ZIP и копии документов в dist/, обновляет data/release.json и текстовые страницы. ZIP не добавляется в Git; новые реестры и ссылки проходят обычный PR.

После слияния выбрать точный проверенный коммит main и создать черновик релиза:

```sh
gh release create olympiad-math-10-NEW_VERSION --repo partanskiy/teaching --target REVIEWED_MAIN_COMMIT --draft --title "Олимпиадная математика 10 класса, 2026/2027" --notes-file dist/release-notes.md dist/olympiad-math-materials.zip dist/olympiad-math-offline.zip dist/submission-plan.docx dist/submission-plan.pdf dist/working-plan.docx dist/working-plan.pdf dist/SHA256SUMS.txt
```

После проверки полноты вложений опубликовать черновик. Публикация запускает дополнительную сборку Pages из проверенных файлов релиза; трафик GitHub LFS для полного банка она не использует. Пользование репозиторием не зависит от сайта или публикации нового релиза на каждый коммит.
