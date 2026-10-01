# Обновление готового комплекта курса

Общее описание хранения, браузерного просмотра и лимитов находится в [BINARY_FLOW.md репозитория teaching](https://github.com/partanskiy/teaching/blob/main/BINARY_FLOW.md). Архивные оригиналы и готовые планы публикуются во вложениях Releases, а сайт получает их при сборке. Эти файлы не попадают в историю Git.

## Получение материалов

В Git-клоне перейти в courses/olympiad-math-10 и выполнить:

```sh
python scripts/restore_materials.py
```

restore_materials читает data/release.json, скачивает зафиксированный архив, сверяет SHA256 и восстанавливает archive/. Перед записью проверяются пути внутри ZIP. Совпадающий локальный файл не перезаписывается; несовпадающий не заменяется без --replace. После восстановления извлекается текст для локального поиска и проверок.

Для работы без Git скачать olympiad-math-offline.zip из релиза курса, распаковать его и открыть index.html. Корень этого ZIP - сам курс; команды scripts/... выполняются из распакованной папки.

## Синхронизация планов

Единый источник занятий - data/lessons.json, который строится scripts/make_course.py. Автор, учебный год и описания разделов находятся в data/program.json. План для сдачи и рабочий план используют одинаковые темы, порядок, цели и часы. Рабочие поля дополнительно содержат номера задач и методические пояснения.

```sh
python scripts/make_course.py
python scripts/publish.py
python scripts/export_documents.py
python scripts/check_plans.py
python scripts/validate.py
node scripts/check_catalog.js
```

DOCX и PDF являются результатом сборки. Ручную правку готового документа нужно перенести в исходники, иначе следующая сборка её заменит. Проверка сверяет оба документа и Markdown с исходным планом; CI также проверяет текстовые результаты и собираемый DOCX для сдачи.

## Подготовка новой версии

Все изменения после первоначального импорта проходят через pull request. Начать отдельную ветку, пересобрать и проверить материалы, выбрать новый тег курса. Пример первой версии:

```sh
git switch -c course/refresh-programme
python scripts/package_release.py --tag olympiad-math-10-2026.10.01
git add data/release.json README.md course research site scripts
git commit -m "feat(course): update curriculum and materials"
git push -u origin course/refresh-programme
gh pr create --repo partanskiy/teaching --base main --title "Update the course programme" --body-file /path/to/reviewed-pr-description.md
```

Сообщения коммитов пишутся на английском в формате Conventional Commits. Коммиты небольшие, разделенные по смыслу. Описание PR должно перечислять конкретные изменения и выполненные проверки.

package_release сначала проверяет архив и документы, затем создаёт готовые вложения в dist/, обновляет зафиксированные ссылки и SHA256 в data/release.json и пересобирает текстовые страницы. В Git сохраняются только эти исходные данные и тексты. Проверить изменения перед отправкой PR.

## Публикация после слияния PR

После успешных проверок и слияния через rebase выбрать точный коммит main. Из папки курса:

```sh
gh release create olympiad-math-10-2026.10.01 --repo partanskiy/teaching --target REVIEWED_MAIN_COMMIT --draft --title "Олимпиадная математика 10 класса, 2026/2027" --notes-file dist/release-notes.md dist/olympiad-math-materials.zip dist/olympiad-math-offline.zip dist/submission-plan.docx dist/submission-plan.pdf dist/working-plan.docx dist/working-plan.pdf dist/SHA256SUMS.txt
```

Заменить REVIEWED_MAIN_COMMIT на фактический SHA проверенного коммита. В примере указан тег первой версии; при следующем обновлении использовать новый. Сначала проверить полноту вложений черновика, затем опубликовать:

```sh
gh release edit olympiad-math-10-2026.10.01 --repo partanskiy/teaching --draft=false
```

Публикация релиза запускает сборку Pages из main. Сайт скачивает зафиксированные архивы и документы, проверяет суммы, планы и ссылки. Старые версии остаются в Releases; в сайте хранится текущая версия. Новая готовая версия не требуется на каждый текстовый коммит.

Оригиналы олимпиады не редактируются. Новый файл включается вместе с происхождением и контрольной суммой. Если издатель заменил содержимое, измененная сумма отмечается явно, и файл проходит повторную проверку.
