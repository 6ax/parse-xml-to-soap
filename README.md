# Необходимо отрпавлять SOAP в **[ELMA](https://www.elma-bpm.ru/)**

## Что было реализовано в скрипте:

- получить из бд Mysql путь к файлу проекта формата .xml
- получить из бд список уже обработанных файлов
- выбрать новый файл если таковой есть
- для нового файла сделать: 
  - получить данные из нового файла (парсинг)
  - подготовить запрос SOAP на основе данных из файла
  - отправить https POST SOAP в систему управления проектами **[ELMA](https://www.elma-bpm.ru/)**
  - отправить в бд обработанный файл
  - записать log c ответом от **[ELMA](https://www.elma-bpm.ru/)**
