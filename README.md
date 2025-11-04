# App_runner
Launches any console application and saves all its standard output to a log file. In this case, standard output will also work, it is not just a redirection.
It is possible to limit the running time of a console application - this is necessary for applications that run for a very long time.

if you just run `app_runner.exe`
```
Использование:
  app_runner.exe [-N | -HH:MM] <программа> [аргументы...]

Параметры:
  -N           - количество часов, через которые программа должна завершиться
  -HH:MM       - время завершения в формате ЧЧ:MM (24-часовой формат)
  программа    - путь к запускаемой программе
  аргументы... - аргументы для передаваемой программы

Примеры:
  app_runner.exe my_app --param1 value1
  app_runner.exe -2.5 my_app --param1 value1
  app_runner.exe -7:30 my_app --param1 value1
  app_runner.exe -0.5 python long_script.py
```
<br>
если вы запустите с помощью `app_runner.exe` архиватор 7z: `app_runner.exe 7z.exe a main.7z main.py`
то программа запишет весь стандартный вывод в лог-файл `app_log_20251104_200152.txt`
```
Запуск: 7z.exe
Аргументы: a main.7z main.py
Время начала: 20:01:51 04.11.2025
Доступная ОЗУ при запуске: 5.4 ГБ из 20.0 ГБ
--------------------------------------------------


7-Zip 19.00 (x64) : Copyright (c) 1999-2018 Igor Pavlov : 2019-02-21

Scanning the drive:
1 file, 17760 bytes (18 KiB)

Creating archive: main.7z

Add new data to archive: 1 file, 17760 bytes (18 KiB)


Files read from disk: 1
Archive size: 4234 bytes (5 KiB)
Everything is Ok

--------------------------------------------------
Время окончания: 20:01:52 04.11.2025
Общее время выполнения: 00:00:00.034 (ЧЧ:ММ:СС)
Код возврата: 0
```
