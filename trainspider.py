from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
from tkinter import messagebox
import tkinter, csv, re, threading


class TrainSpider():
    login_url = "https://kyfw.12306.cn/otn/resources/login.html"
    personal_url = "https://kyfw.12306.cn/otn/view/index.html"
    ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc"
    confirm_url = "https://kyfw.12306.cn/otn/confirmPassenger/initDc"
    driver = webdriver.Chrome(executable_path="chromedriver.exe")
    from_station_code = None
    to_station_code = None
    confirm_train = None

    def __init__(self, passengers, from_station, to_station, train_date, trains):
        """
        参数说明
        :param passengers: 乘客姓名 列表类型  ["张三", "李四"]
        :param from_station: 起始站
        :param to_station: 终点站
        :param train_date: 出发日期
        :param trains: 车次信息 字典类型  {"K898": ["4", "3"], "K7918": ["3", "1"]}
        # 9：商务座，M：一等座，O：二等座，6：高级软卧，4：软卧，3：硬卧，1：硬座
        """
        self.passengers = passengers
        self.from_staion = from_station
        self.to_staion = to_station
        self.train_date = train_date
        self.trains = trains
        self.get_code()

    def login(self):
        self.driver.get(self.login_url)
        WebDriverWait(self.driver, 1000).until(EC.url_contains(self.personal_url))
        print("登录成功")

    def get_code(self):
        with open("stations.csv", "r", encoding="utf-8") as fp:
            lines = csv.DictReader(fp)
            for line in lines:
                if line["name"] == self.from_staion:
                    self.from_station_code = line["code"]
                    break
        with open("stations.csv", "r", encoding="utf-8") as fp:
            lines = csv.DictReader(fp)
            for line in lines:
                if line["name"] == self.to_staion:
                    self.to_station_code = line["code"]
                    break

    def search_ticket(self):
        self.driver.get(self.ticket_url)
        # self.driver.switch_to.window(self.driver.window_handles[1])
        # 因疫情期间会出现一个确认的按钮框，可能在疫情过后该按钮框就没了
        try:
            confirm_btn = self.driver.find_element_by_id("qd_closeDefaultWarningWindowDialog_id")
            confirm_btn.click()
        except Exception:
            pass

        # 找到各项信息的输入框并将各项信息填充到输入框中，然后提交查询
        fromStation_input = self.driver.find_element_by_id("fromStation")
        toStation_input = self.driver.find_element_by_id("toStation")
        train_date_input = self.driver.find_element_by_id("train_date")

        self.driver.execute_script(f"arguments[0].value='{self.from_station_code}'", fromStation_input)
        self.driver.execute_script(f"arguments[0].value='{self.to_station_code}'", toStation_input)
        self.driver.execute_script(f"arguments[0].value='{self.train_date}'", train_date_input)
        # 当抢票未开始时循环点击查询按钮更新页面当前信息
        while True:
            WebDriverWait(self.driver, 1000).until(EC.element_to_be_clickable((By.ID, "query_ticket")))
            submit_btn = self.driver.find_element_by_id("query_ticket")
            submit_btn.click()

            # 解析当前各列车的车次信息
            WebDriverWait(self.driver, 1000).until(
                EC.presence_of_element_located((By.XPATH, "//tbody[@id='queryLeftTable']/tr")))
            # 测试时打印各项信息头部
            # train_head = self.driver.find_element_by_xpath("//div[@id='t-list']//thead//tr")
            # print(re.split("\n| ", train_head.text))
            train_infos = self.driver.find_elements_by_xpath("//tbody[@id='queryLeftTable']/tr[not(@datatran)]")
            has_seat = False
            seat_confirm = None
            for train_info in train_infos:
                # 拿到每辆车次的信息
                train_info_list = re.split("\n| ", train_info.text)
                # 如果这辆车的车次在用户需要的车次里
                if train_info_list[0] in self.trains:
                    # print(f"找到{train_info_list[0]}了")
                    # 拿到用户需要的车次并进行比对是否有票
                    for seat in self.trains[train_info_list[0]]:
                        if seat == "9":
                            if train_info_list[7].isdigit() or train_info_list[7] == "有":
                                # 如果商务座有票的话
                                has_seat = True
                                seat_confirm = "9"
                                break
                        if seat == "M":
                            if train_info_list[8].isdigit() or train_info_list[8] == "有":
                                # 如果一等座有票的话
                                has_seat = True
                                seat_confirm = "M"
                                break
                        if seat == "0":
                            if train_info_list[9].isdigit() or train_info_list[9] == "有":
                                # 如果二等座有票的话
                                has_seat = True
                                seat_confirm = "0"
                                break
                        if seat == "6":
                            if train_info_list[10].isdigit() or train_info_list[10] == "有":
                                # 如果高级软卧有票的话
                                has_seat = True
                                seat_confirm = "6"
                                break
                        if seat == "4":
                            if train_info_list[11].isdigit() or train_info_list[11] == "有":
                                # 如果软卧有票的话
                                has_seat = True
                                seat_confirm = "4"
                                break
                        if seat == "3":
                            if train_info_list[13].isdigit() or train_info_list[13] == "有":
                                # 如果硬卧有票的话
                                has_seat = True
                                seat_confirm = "3"
                                break
                        if seat == "1":
                            if train_info_list[15].isdigit() or train_info_list[15] == "有":
                                # 如果硬座有票的话
                                has_seat = True
                                seat_confirm = "1"
                                break
                    if has_seat:
                        order_btn = train_info.find_element_by_xpath(".//a[@class='btn72']")
                        order_btn.click()
                        self.confirm_train = train_info_list[0]
                        return seat_confirm

    def search_ticket_assist(self):
        # 检测是否出现查询超时
        while True:
            WebDriverWait(self.driver, 1000).until(
                EC.visibility_of_element_located((By.ID, "no_filter_ticket_6")))
            WebDriverWait(self.driver, 1000).until(EC.element_to_be_clickable((By.ID, "query_ticket")))
            submit_btn = self.driver.find_element_by_id("query_ticket")
            submit_btn.click()

    def confirm(self, seat):
        is_success = False
        WebDriverWait(self.driver, 1000).until(EC.url_contains(self.confirm_url))
        WebDriverWait(self.driver, 1000).until(
            EC.presence_of_element_located((By.XPATH, "//ul[@id='normal_passenger_id']//label")))
        # 锁定乘客信息
        passengers = self.driver.find_elements_by_xpath("//ul[@id='normal_passenger_id']//label")
        for passenger in passengers:
            if passenger.text in self.passengers:
                passenger.click()
        # 选择列车席位
        for i in range(len(self.passengers)):
            seat_type = self.driver.find_element_by_id(f"seatType_{i + 1}")
            select_option = Select(seat_type)
            try:
                select_option.select_by_value(seat)
            except NoSuchElementException:
                is_success = False
                return is_success
        # 提交订单
        submit_order_btn = self.driver.find_element_by_id("submitOrder_id")
        submit_order_btn.click()
        # 等待模态对话框与确认按钮
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "qr_submit_id")))
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "qr_submit_id")))
        submit_btn = self.driver.find_element_by_id("qr_submit_id")
        while submit_btn:
            try:
                submit_btn.click()
                submit_btn = self.driver.find_element_by_id("qr_submit_id")
            except ElementNotVisibleException:
                is_success = True
                break
        # print(submit_btn.text)
        return is_success

    def run(self):
        # 1.登录12306
        self.login()
        while True:
            # 2.查找车票
            seat = self.search_ticket()
            # 3.确定乘客与席位并提交
            is_success = self.confirm(seat)

            # 4.根据返回参数确定是否提交成功，若成功跳出循环
            if is_success:
                print(f"恭喜抢到【{self.confirm_train}】车次【{seat}】席位，请在30分钟内完成付款！")
                root = tkinter.Tk()
                messagebox.showinfo("提示", f"恭喜抢到【{self.confirm_train}】车次【{seat}】席位，请在30分钟内完成付款！")
                root.destroy()
                break


def main():
    """
    需要你修改223行代码，格式如下：
    TrainSpider(["乘车姓名1", "乘车人姓名2"], "起始站名", "终点站名", "出行时间",  {"车次1": ["座位类别1", "座位类别2"], "车次2": ["座位类别1", "座位类别2"]})

     需要注意的：
        1. 由于购票需要，乘车人姓名必须是12306里已经完成认证的，可以多个，至少一个
        2. 起始站名与终点站名必须写清楚且与官网一致，，不要写多余的站字，写站名就可以了。比如呼和浩特与呼和浩特东是两个站
        3. 出行时间就是你要买几号的票，格式为"年-月-日"，注意：2月要写02,3号要写03,例："2022-02-03"
        4. 车次信息里第一个双引号里填的是车次信息，比如北京去上海中午十二点的车次叫D111，那你就填这个。
            车次信息里座位类别是你想买什么座，比如只想买软卧，那就填"4"。如果没有软卧，硬卧也可以，但是优先软卧，那就填"4", "3"
            车次信息可以多个，至少一个，从前往后填。座位类别参考以下：
         座位类别：9：商务座，M：一等座，O：二等座，6：高级软卧，4：软卧，3：硬卧，1：硬座
    """
    customer = TrainSpider(["张三"], "北京南", "上海虹桥", "2022-01-03", {"G15": ["M", "0"]})
    master = threading.Thread(target=customer.run)
    assist = threading.Thread(target=customer.search_ticket_assist)
    assist.start()
    master.start()


if __name__ == '__main__':
    main()
