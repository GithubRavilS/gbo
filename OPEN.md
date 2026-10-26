# Открыть сайт инвестору в Safari

jsDelivr показывает **исходник** — так и должно быть, он отдаёт HTML как текст. Не используй его.

## Рабочий способ (сейчас)

На Mac в Terminal:

```bash
cd ~/Documents/Cursor/gbo
git fetch origin cursor/gbo-katerina-quote-bddf
git checkout cursor/gbo-katerina-quote-bddf
open -a Safari index.html
```

Файл откроется как нормальная страница:  
`/Users/ravilcrypto/Documents/Cursor/gbo/index.html`

## Онлайн-превью (без pull)

https://htmlpreview.github.io/?https://github.com/GithubRavilS/gbo/blob/cursor/gbo-katerina-quote-bddf/index.html

## После merge в main

Сайт станет постоянным здесь (GitHub Pages уже включён с `main`):  
https://githubravils.github.io/gbo/
