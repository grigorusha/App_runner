import sys
import subprocess
import time
import argparse
from datetime import datetime, timedelta
import os
import signal
import threading


def format_time(seconds):
    """Форматирование времени в ЧЧ:ММ:СС"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def format_datetime(dt):
    """Форматирование даты и времени в ЧЧ:ММ:СС ДД.ММ.ГГГГ"""
    return dt.strftime("%H:%M:%S %d.%m.%Y")


def get_memory_info():
    """Получение информации о памяти с помощью psutil"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024 ** 3)
        available_gb = memory.available / (1024 ** 3)
        return f"{available_gb:.1f} ГБ из {total_gb:.1f} ГБ"
    except ImportError:
        return "psutil не установлен"
    except Exception as e:
        return f"ошибка: {str(e)}"


def parse_time_param(time_str):
    """Парсинг параметра времени в формате HH:MM"""
    try:
        hours, minutes = map(int, time_str.split(':'))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return hours, minutes
        else:
            return None
    except:
        return None


def calculate_timeout_seconds(target_hours, target_minutes):
    """Вычисление количества секунд до указанного времени"""
    now = datetime.now()
    target_time = now.replace(hour=target_hours, minute=target_minutes, second=0, microsecond=0)

    # Если указанное время уже прошло сегодня, берем на завтра
    if target_time <= now:
        target_time += timedelta(days=1)

    return (target_time - now).total_seconds()


def is_within_5_minutes_after(target_hours, target_minutes):
    """Проверяет, находится ли текущее время в пределах 5 минут после указанного времени"""
    now = datetime.now()
    target_time = now.replace(hour=target_hours, minute=target_minutes, second=0, microsecond=0)

    # Если текущее время позже целевого, но не более чем на 5 минут
    if target_time <= now <= target_time + timedelta(minutes=5):
        return True

    # Также проверяем случай, когда целевое время было вчера
    target_time_yesterday = target_time - timedelta(days=1)
    if target_time_yesterday <= now <= target_time_yesterday + timedelta(minutes=5):
        return True

    return False


def print_usage(program_name):
    """Вывод справки по использованию программы"""
    print("Использование:")
    print(f"  {program_name} [-N | -HH:MM] <программа> [аргументы...]")
    print()
    print("Параметры:")
    print("  -N           - количество часов, через которые программа должна завершиться")
    print("  -HH:MM       - время завершения в формате ЧЧ:MM (24-часовой формат)")
    print("  программа    - путь к запускаемой программе")
    print("  аргументы... - аргументы для передаваемой программы")
    print()
    print("Примеры:")
    print(f"  {program_name} my_app --param1 value1")
    print(f"  {program_name} -2.5 my_app --param1 value1")
    print(f"  {program_name} -7:30 my_app --param1 value1")
    print(f"  {program_name} -0.5 python long_script.py")


def main():
    # Получаем имя исполняемого файла для использования в справке
    program_name = os.path.basename(sys.argv[0])

    # Если нет параметров, выводим справку и завершаемся
    if len(sys.argv) == 1:
        print_usage(program_name)
        sys.exit(0)

    # Выводим время начала работы
    start_datetime = datetime.now()
    print(f"Время начала работы лаунчера: {format_datetime(start_datetime)}")

    # Выводим информацию о памяти
    memory_info = get_memory_info()
    print(f"Доступная ОЗУ: {memory_info}")
    print()

    # Обработка параметра -N или -HH:MM перед основным парсингом
    timeout_seconds = None
    timeout_description = None
    skip_launch = False

    if len(sys.argv) > 1 and sys.argv[1].startswith('-'):
        param = sys.argv[1][1:]  # Убираем знак минуса

        # Проверяем, является ли параметром время в формате HH:MM
        time_params = parse_time_param(param)
        if time_params:
            hours, minutes = time_params

            # Проверяем, не запускаем ли мы программу в течение 5 минут после указанного времени
            if is_within_5_minutes_after(hours, minutes):
                skip_launch = True
                timeout_description = f"завершение в {hours:02d}:{minutes:02d} (пропущено, запуск в течение 5 минут после времени завершения)"
            else:
                timeout_seconds = calculate_timeout_seconds(hours, minutes)
                timeout_description = f"завершение в {hours:02d}:{minutes:02d}"
        else:
            # Пробуем интерпретировать как число (часы)
            try:
                timeout_hours = float(param)
                timeout_seconds = timeout_hours * 3600
                timeout_description = f"таймаут {timeout_hours} часов"
            except ValueError:
                # Если не число и не время, пропускаем - это будет обработано argparse
                pass

        # Удаляем обработанный параметр из sys.argv
        if timeout_seconds is not None or skip_launch:
            del sys.argv[1]

    # Если после удаления параметра не осталось аргументов, выводим справку
    if len(sys.argv) == 1:
        print_usage(program_name)
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description='Запуск приложения с измерением времени и логированием вывода',
        add_help=False  # Отключаем стандартный help, чтобы использовать наш
    )
    parser.add_argument(
        'app_to_run',
        help='Путь к приложению, которое нужно запустить'
    )
    parser.add_argument(
        'app_args',
        nargs=argparse.REMAINDER,
        help='Аргументы для передаваемого приложения'
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        # Если argparse не может распарсить аргументы, выводим нашу справку
        print_usage(program_name)
        sys.exit(0)

    if not args.app_to_run:
        print_usage(program_name)
        sys.exit(0)

    # Создаем имя лог-файла на основе времени
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"app_log_{timestamp}.txt"

    print(f"Запуск приложения: {args.app_to_run}")
    print(f"Аргументы: {args.app_args}")
    if timeout_description:
        print(f"Ограничение: {timeout_description}")
    print(f"Лог-файл: {log_filename}")
    print("-" * 50)

    # Если нужно пропустить запуск из-за времени
    if skip_launch:
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            log_file.write(f"Запуск: {args.app_to_run}\n")
            log_file.write(f"Аргументы: {' '.join(args.app_args)}\n")
            log_file.write(f"Ограничение: {timeout_description}\n")
            log_file.write(f"Время начала: {format_datetime(start_datetime)}\n")
            log_file.write(f"Доступная ОЗУ при запуске: {memory_info}\n")
            log_file.write("-" * 50 + "\n\n")
            log_file.write(
                "ОШИБКА: Приложение не было запущено, так как запуск произошел в течение 5 минут после указанного времени завершения.\n")

        print("\n" + "=" * 50)
        print(
            "ОШИБКА: Приложение не было запущено, так как запуск произошел в течение 5 минут после указанного времени завершения.")
        print(f"Лог сохранен в: {log_filename}")
        sys.exit(1)

    process_start_time = time.time()
    process = None
    timer = None
    interrupted = False

    def signal_handler(sig, frame):
        """Обработчик сигнала Ctrl+C"""
        nonlocal interrupted
        interrupted = True
        print(f"\nПолучен сигнал прерывания (Ctrl+C). Завершение дочернего процесса...")

        if process and process.poll() is None:
            # Записываем в лог информацию о прерывании
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n[ПРЕРЫВАНИЕ] Получен сигнал SIGINT в {format_datetime(datetime.now())}\n")
                log_file.write("[ПРЕРЫВАНИЕ] Завершение дочернего процесса...\n")

            # Пытаемся корректно завершить процесс
            try:
                process.terminate()  # Посылаем SIGTERM
                print("Ожидание graceful shutdown (2 секунды)...")
                time.sleep(2)
                if process.poll() is None:  # Если все еще работает
                    process.kill()  # Принудительно завершаем
                    print("Процесс принудительно завершен")
            except Exception as e:
                print(f"Ошибка при завершении процесса: {e}")

        # Отменяем таймер если он есть
        if timer:
            timer.cancel()

    # Регистрируем обработчик сигнала
    original_sigint = signal.signal(signal.SIGINT, signal_handler)

    try:
        # Запускаем приложение и перехватываем вывод
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            # Записываем заголовок в лог
            log_file.write(f"Запуск: {args.app_to_run}\n")
            log_file.write(f"Аргументы: {' '.join(args.app_args)}\n")
            if timeout_description:
                log_file.write(f"Ограничение: {timeout_description}\n")
            log_file.write(f"Время начала: {format_datetime(start_datetime)}\n")
            log_file.write(f"Доступная ОЗУ при запуске: {memory_info}\n")
            log_file.write("-" * 50 + "\n\n")

            # Запускаем процесс
            process = subprocess.Popen(
                [args.app_to_run] + args.app_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Объединяем stdout и stderr
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Если задано ограничение по времени, запускаем таймер
            if timeout_seconds is not None:

                def timeout_handler():
                    nonlocal interrupted
                    if process and process.poll() is None:
                        interrupted = True
                        if "завершение в" in timeout_description:
                            print(f"\nДостигнуто время {timeout_description}. Завершение процесса...")
                        else:
                            print(f"\nТаймаут истек ({timeout_description}). Завершение процесса...")

                        with open(log_filename, 'a', encoding='utf-8') as log_file:
                            if "завершение в" in timeout_description:
                                log_file.write(f"\n[ТАЙМАУТ] Достигнуто время завершения {timeout_description}\n")
                            else:
                                log_file.write(f"\n[ТАЙМАУТ] Превышено время выполнения {timeout_description}\n")
                            log_file.write("[ТАЙМАУТ] Завершение дочернего процесса...\n")

                        try:
                            process.terminate()
                            time.sleep(2)
                            if process.poll() is None:
                                process.kill()
                        except Exception as e:
                            print(f"Ошибка при завершении по таймауту: {e}")

                timer = threading.Timer(timeout_seconds, timeout_handler)
                timer.daemon = True
                timer.start()

            # Читаем вывод в реальном времени и пишем в лог и консоль
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    log_file.write(output)
                    log_file.flush()  # Обеспечиваем немедленную запись в файл

            # Отменяем таймер, если процесс завершился самостоятельно
            if timer and timer.is_alive():
                timer.cancel()

            # Получаем код возврата
            return_code = process.poll()

    except FileNotFoundError:
        print(f"Ошибка: приложение '{args.app_to_run}' не найдено")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)
    finally:
        # Восстанавливаем оригинальный обработчик сигнала
        signal.signal(signal.SIGINT, original_sigint)

    end_time = time.time()
    execution_time = end_time - process_start_time
    formatted_time = format_time(execution_time)

    # Записываем итоговую информацию в лог
    with open(log_filename, 'a', encoding='utf-8') as log_file:
        log_file.write("\n" + "-" * 50 + "\n")
        log_file.write(f"Время окончания: {format_datetime(datetime.now())}\n")
        log_file.write(f"Общее время выполнения: {formatted_time} (ЧЧ:ММ:СС)\n")
        log_file.write(f"Код возврата: {return_code}\n")

        if interrupted:
            log_file.write("ПРИМЕЧАНИЕ: Процесс был прерван пользователем (Ctrl+C)\n")
        elif timeout_seconds is not None and execution_time >= timeout_seconds:
            if "завершение в" in timeout_description:
                log_file.write(f"ПРИМЕЧАНИЕ: Процесс был завершен по достижении времени {timeout_description}\n")
            else:
                log_file.write(f"ПРИМЕЧАНИЕ: Процесс был завершен по таймауту {timeout_description}\n")

    # Выводим итоговую информацию в консоль
    print("\n" + "=" * 50)
    print(f"Приложение завершено с кодом возврата: {return_code}")
    print(f"Время окончания: {format_datetime(datetime.now())}")
    print(f"Общее время выполнения: {formatted_time} (ЧЧ:ММ:СС)")
    if interrupted:
        print("ПРИМЕЧАНИЕ: Процесс был прерван пользователем (Ctrl+C)")
    elif timeout_seconds is not None and execution_time >= timeout_seconds:
        if "завершение в" in timeout_description:
            print(f"ПРИМЕЧАНИЕ: Процесс был завершен по достижении времени {timeout_description}")
        else:
            print(f"ПРИМЕЧАНИЕ: Процесс был завершен по таймауту {timeout_description}")
    print(f"Лог сохранен в: {log_filename}")


if __name__ == "__main__":
    main()