from card_validator import CardValidator
from exceptions import CardError


def show_menu() -> None:
    print("\n Поиск и проверка номеров банковских карт ")
    print("1. Проверить номер карты (синтаксис + алгоритм Луна)")
    print("2. Проверить номер карты (только синтаксис)")
    print("3. Найти карты во введенном тексте")
    print("4. Найти карты в файле")
    print("5. Найти карты на веб-странице (по URL)")
    print("0. Выход")


def print_cards(cards: list[str]) -> None:
    if not cards:
        print("Номера карт не найдены.")
        return

    print(f"Найдено карт ({len(cards)}):")
    for i, card in enumerate(cards, start=1):
        print(f"   * {i}. {card}")


def main() -> None:
    while True:
        show_menu()
        cmd = input("Введите номер команды: ").strip()

        try:
            if cmd == "1":
                card = input("Введите номер карты: ")
                if CardValidator.is_valid_card(card, use_luhn=True):
                    print("Номер карты корректный.")
                else:
                    print("Некорректный номер карты.")

            elif cmd == "2":
                card = input("Введите номер карты: ")
                if CardValidator.is_valid_card(card, use_luhn=False):
                    print("Синтаксис номера корректный.")
                else:
                    print("Синтаксис номера некорректный.")

            elif cmd == "3":
                text = input("Введите текст: ")
                found = CardValidator.find_in_text(text)
                print_cards(found)

            elif cmd == "4":
                path = input("Путь к файлу: ")
                found = CardValidator.find_in_file(path)
                print_cards(found)

            elif cmd == "5":
                url = input("URL страницы: ")
                found = CardValidator.find_on_url(url)
                print_cards(found)

            elif cmd == "0":
                break

            else:
                print("Нет такой команды.")

        except CardError as e:
            print(f"Ошибка: {e}")
        except OSError as e:
            print(f"Ошибка файла: {e}")


if __name__ == "__main__":
    main()