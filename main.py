from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import pandas as pd
from datetime import datetime, timedelta


def set_date(date, driver):
    date_input = driver.find_element(By.ID, "aid_stats_1_date2")
    driver.execute_script("arguments[0].value = arguments[1];", date_input, date.strftime("%d.%m.%Y"))
    date_input.send_keys(Keys.RETURN)


def select_zone(zone_value, driver):
    zone_dropdown = Select(driver.find_element(By.ID, "aid_stats_zone_select"))
    zone_dropdown.select_by_value(str(zone_value))


def select_hour_period(driver):
    hour_tab = driver.find_element(By.XPATH, '//li[@onclick="ShChangePeriod(0);"]')
    hour_tab.click()


def extract_table_data(table_id, driver, date_str):
    table = driver.find_element(By.ID, table_id)
    rows = table.find_elements(By.TAG_NAME, "tr")
    data = []
    for row in rows[1:]: # first string is always empty. I don't know reason
        cells = row.find_elements(By.TAG_NAME, "td")
        data.append([date_str] + [cell.text for cell in cells])
    return data


def add_to_csv(data, file_path):
    df = pd.DataFrame(data)
    df.to_csv(file_path, mode='a', header=False, index=False)


def print_headers(headers, file_path):
    df = pd.DataFrame([], columns=headers)
    df.to_csv(file_path, mode='w', index=False)


def main():
    folder_path = "data"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    buyers_headers = [
        "Дата",
        "Час",
        "Объем полного планового потребления, МВт.ч",
        "Индекс равновесных цен на покупку электроэнергии, руб./МВт.ч.",
        "Объем покупки по регулируемым договорам, МВт.ч",
        "Объем покупки на РСВ, МВт.ч",
        "Объем продажи в обеспечение РД, МВт.ч",
        "Максимальный индекс равновесной цены, руб./МВт.ч",
        "Минимальный индекс равновесной цены, руб./МВт.ч"
    ]
    providers_headers = [
        "Дата",
        "День",
        "Объем планового производства, МВт.ч",
        "Индекс равновесных цен на продажу электроэнергии, руб./МВт.ч.",
        "Объем продажи по регулируемым договорам, МВт.ч",
        "Объем продажи на РСВ, МВт.ч",
        "Объем покупки в обеспечение РД, МВт.ч",
        "Максимальный индекс равновесной цены за период, руб./МВт.ч",
        "Минимальный индекс равновесной цены за период, руб./МВт.ч"
    ]
    table = [[[], []], [[], []]]
    buyers_paths = ["data/buyers_1_zone_value.csv", "data/buyers_2_zone_value.csv"]
    providers_paths = ["data/providers_1_zone_value.csv", "data/providers_2_zone_value.csv"]
    for path in buyers_paths:
        print_headers(buyers_headers, path)
    for path in providers_paths:
        print_headers(providers_headers, path)
    start_date = datetime(2021, 11, 26)
    end_date = datetime(2024, 11, 24)
    url = "https://www.atsenergo.ru/results/rsv/index?zone=1"

    options = Options()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    driver.maximize_window()  # select_hour_period don't work without it
    time_delta = 0.2
    time.sleep(time_delta * 3)

    current_date = start_date
    while current_date <= end_date:
        try:
            for zone_value in 0, 1:
                set_date(current_date, driver)
                select_zone(zone_value + 1, driver)
                select_hour_period(driver)
                time.sleep(time_delta)
                date_str = current_date.strftime("%Y.%m.%d")
                table[0][zone_value] = extract_table_data("aid_stats_1_table_table", driver, date_str)
                table[1][zone_value] = extract_table_data("aid_stats_2_table_table", driver, date_str)

            add_to_csv(table[0][0], buyers_paths[0])
            add_to_csv(table[0][1], buyers_paths[1])
            add_to_csv(table[1][0], providers_paths[0])
            add_to_csv(table[1][1], providers_paths[1])
            print(f"Saved data for {current_date}")

            current_date += timedelta(days=1)

        except Exception as e:
            print(e)

    driver.quit()
    return 0


if __name__ == "__main__":
    main()
