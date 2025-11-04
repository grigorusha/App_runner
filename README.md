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
