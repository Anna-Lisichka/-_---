import os
import csv
from tabulate import tabulate


class PriceMachine:
    def __init__(self):
        self.data = []
        self.result = ''
        self.name_length = 0

    def load_prices(self, file_path=''):
        # Проверяем все файлы в папке и ищем с "price" в названии и форматом .csv
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if 'price' in file.lower() and file.endswith('.csv'):
                    file_full_path = os.path.join(root, file)
                    self.process_file(file_full_path)

    def process_file(self, file_path):
        # добавляем блок исключения, чтобы избежать аварийного завершения при открытии файлов
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                # Определяем разделитель колонок в файлах
                sniffer = csv.Sniffer()
                sample = csvfile.read(300)
                csvfile.seek(0)

                try:
                    # добавляем блок исключения, чтобы избежать аварийного завершения если файл поврежден
                    dialect = sniffer.sniff(sample)
                    delimiter = dialect.delimiter
                except csv.Error:
                    delimiter = ';'  # Используем точку с запятой, если не удалось определить разделитель

                # Чтение CSV с определенным разделителем
                reader = csv.DictReader(csvfile, delimiter=delimiter)

                # Создаем переменные для хранения индексов столбцов
                product_column = None
                price_column = None
                weight_column = None

                # Перебираем все столбцы, чтобы найти нужные нам для вывода в таблицу
                for header in reader.fieldnames:
                    if header.lower() in ['название', 'продукт', 'товар', 'наименование']:
                        product_column = header
                    elif header.lower() in ['цена', 'розница']:
                        price_column = header
                    elif header.lower() in ['фасовка', 'масса', 'вес']:
                        weight_column = header

                # Если все нужные столбцы найдены
                if product_column and price_column and weight_column:
                    for row in reader:
                        # Обработка пустых строк: если данных нет в какой-то колонке, используем пустое значение
                        product_name = row.get(product_column, '').strip()
                        try:
                            # добавляем блок исключения, чтобы избежать аварийного завершения, если будут данные,
                            # которые нельзя преобразовать в числа
                            price = float(row.get(price_column, '0').replace(',', '.'))
                            weight = float(row.get(weight_column, '0').replace(',', '.'))
                        except ValueError:
                            continue  # Пропускаем строки с некорректными данными

                        # Обновляем длину наименования для выравнивания
                        self.name_length = max(self.name_length, len(product_name))

                        # Рассчитываем цену за килограмм
                        price_per_kg = price / weight if weight > 0 else 0

                        # Извлекаем только имя файла без пути
                        file_name = os.path.basename(file_path)

                        # Добавляем данные в итоговый список с округлением: 2 знака для цен и 3 знака для веса
                        self.data.append({
                            'product_name': product_name,
                            'price': round(price, 2),
                            'weight': round(weight, 3),
                            'price_per_kg': round(price_per_kg, 2)
                        })

        except Exception as e:
            # перехватываем ошибки
            print(f"Ошибка при обработке файла {file_path}: {e}")

    def find_text(self, search_text):
        # Ищем товар по фрагменту и выводим список с сортировкой по цене за килограмм
        found_items = [item for item in self.data if search_text.lower() in item['product_name'].lower()]
        return sorted(found_items, key=lambda x: x['price_per_kg'])

    def export_to_html(self, fname='output.html'):
        # Формируем данные для сохранения в файл HTML с сортировкой по цене за килограмм
        sorted_data = sorted(self.data, key=lambda x: x['price_per_kg'])

        result = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Позиции продуктов</title>
            <meta charset="UTF-8">
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 10px;
                    border: 1px solid #ddd;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
            </style>
        </head>
        <body>
            <h1>Список позиций продуктов</h1>
            <table>
                <thead>
                    <tr>
                        <th>Номер</th>
                        <th>Название</th>
                        <th>Цена</th>
                        <th>Фасовка</th>
                        <th>Цена за кг.</th>
                    </tr>
                </thead>
                <tbody>
            '''

        for idx, item in enumerate(sorted_data, start=1):
            result += f'''
            <tr>
                <td>{idx}</td>
                <td>{item['product_name']}</td>
                <td>{item['price']:.2f}</td>
                <td>{item['weight']:.3f}</td>
                <td>{item['price_per_kg']:.2f}</td>
            </tr>
            '''

        result += '''
        </tbody>
    </table>
</body>
</html>
'''

        # Сохранение HTML в файл
        with open(fname, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"Данные экспортированы в файл {fname}")

    def print_table(self, items):
        # Формируем таблицу для вывода в консоль
        table = []
        for idx, item in enumerate(items, start=1):
            table.append([
                idx,
                item['product_name'].ljust(self.name_length),
                f"{item['price']:.2f}",
                f"{item['weight']:.3f}",
                f"{item['price_per_kg']:.2f}"
            ])

        headers = ["№", "Наименование", "Цена", "Вес", "Цена за кг."]
        print(tabulate(table, headers=headers, tablefmt="grid"))


# Пример использования:
if __name__ == '__main__':
    price_machine = PriceMachine()
    price_machine.load_prices('./price_lists')  # Путь к папке с прайс-листами

    # Сортируем все товары по цене за килограмм и выводим
    sorted_items = sorted(price_machine.data, key=lambda x: x['price_per_kg'])
    print("Список всех товаров из всех файлов, отсортированных по цене за килограмм:")
    price_machine.print_table(sorted_items)

    # Экспортируем данные в HTML файл
    price_machine.export_to_html("output.html")

    # Интерфейс для поиска
    while True:
        query = input("\nВведите название товара для поиска (или 'exit' для завершения): ").strip()
        if query.lower() == 'exit':
            print("Работа программы завершена.")
            break

        # Поиск товаров
        found_items = price_machine.find_text(query)

        # Вывод результатов
        if found_items:
            price_machine.print_table(found_items)
        else:
            print("Товары не найдены.")
