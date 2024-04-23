import sys
import json
import hashlib
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLineEdit, QComboBox,
    QFormLayout, QDialogButtonBox, QMessageBox, QFileDialog,
    QInputDialog, QApplication, QDateEdit, QLabel
)
from PyQt5.QtCore import QDate, QTime
import cv2
import numpy as np
import datetime
import os
import csv
import face_recognition


def hash_password(password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

# 初始化管理员配置（如果需要的话）
if not os.path.exists('admin_config.json'):
    initial_admin_config = {
        "username": "BUPT",
        "hashed_password": hash_password("111")
    }

    with open('admin_config.json', 'w') as f:
        json.dump(initial_admin_config, f)


class AdminLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("管理员登录入口")
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入账号")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_button = QPushButton("登录")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        hashed_password = hash_password(password)

        try:
            with open('admin_config.json', 'r') as f:
                admin_config = json.load(f)

            print("输入的用户名:", username)
            print("输入的哈希密码:", hashed_password)

            # 检查提供的用户名和密码是否匹配
            if username in admin_config and hashed_password == admin_config[username]:
                print("登录成功！")
                self.accept()
                return
            else:
                print("登录失败：用户名或密码不匹配。")
                QMessageBox.warning(self, "登录失败", "账号或密码错误")

        except Exception as e:
            print(f"发生错误：{e}")
            QMessageBox.warning(self, "错误", "发生错误，请稍后再试。")


class AdminManagementDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("管理员账户管理")
        layout = QVBoxLayout()

        add_button = QPushButton("新增管理员账户")
        add_button.clicked.connect(self.add_admin)
        layout.addWidget(add_button)

        delete_button = QPushButton("删除管理员账户")
        delete_button.clicked.connect(self.delete_admin)
        layout.addWidget(delete_button)

        self.setLayout(layout)

    def add_admin(self):
        username, ok = QInputDialog.getText(self, '新增管理员', '请输入用户名:')
        if not ok:
            return

        password, ok = QInputDialog.getText(self, '新增管理员', '请输入密码:')
        if not ok:
            return

        hashed_password = hash_password(password)

        # 尝试读取现有的管理员配置
        try:
            with open('admin_config.json', 'r') as f:
                admin_config = json.load(f)
        except FileNotFoundError:
            admin_config = {}

        # 更新或添加新的管理员信息
        admin_config[username] = hashed_password

        # 将更新后的管理员配置写回文件
        with open('admin_config.json', 'w') as f:
            json.dump(admin_config, f)

        QMessageBox.information(self, "新增成功", "管理员账户添加成功！")

    def delete_admin(self):
        username, ok = QInputDialog.getText(self, '删除管理员', '请输入要删除的用户名:')
        if not ok:
            return

        password, ok = QInputDialog.getText(self, '删除管理员', '请输入密码以确认:')
        if not ok:
            return

        hashed_password = hash_password(password)

        try:
            with open('admin_config.json', 'r') as f:
                admin_config = json.load(f)

            # 检查提供的用户名是否存在于admin_config中
            if username in admin_config:
                # 检查提供的用户名和密码是否匹配
                if hashed_password == admin_config[username]:
                    # 删除指定的管理员账户
                    admin_config.pop(username)
                    # 将更新后的管理员配置写回文件
                    with open('admin_config.json', 'w') as f:
                        json.dump(admin_config, f)
                    QMessageBox.information(self, "删除成功", "管理员账户删除成功！")
                else:
                    QMessageBox.warning(self, "删除失败", "账号或密码错误")
            else:
                QMessageBox.warning(self, "删除失败", "账号不存在！")

        except Exception as e:
            print(f"发生错误：{e}")
            QMessageBox.warning(self, "错误", "发生错误，请稍后再试。")


class AdminFunctionsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("管理员功能")
        layout = QVBoxLayout()

        self.attendance_management_button = QPushButton("签到信息管理")
        self.attendance_management_button.clicked.connect(self.open_attendance_management_dialog)
        layout.addWidget(self.attendance_management_button)

        self.student_info_button = QPushButton("学生信息录入")
        self.student_info_button.clicked.connect(self.take_photo_for_student_info)
        layout.addWidget(self.student_info_button)

        self.admin_management_button = QPushButton("管理员账户管理")
        self.admin_management_button.clicked.connect(self.open_admin_management_dialog)
        layout.addWidget(self.admin_management_button)

        self.setLayout(layout)

    @pyqtSlot()
    def open_attendance_management_dialog(self):
        dialog = AttendanceManagementDialog()
        dialog.exec_()

    @pyqtSlot()
    def take_photo_for_student_info(self):
        name, ok = QInputDialog.getText(self, '学生信息录入', '请输入学生姓名:')
        if not ok:
            return

        student_id, ok = QInputDialog.getText(self, '学生信息录入', '请输入学生学号:')
        if not ok:
            return

        filename = os.path.join(os.getcwd(),
                                f'/Users/sonata/Desktop/Face-Recogntion-PyQt/Face_Detection_PyQt_Final/ImagesAttendance/{name}_{student_id}.jpg')

        ret, frame = self.capture.read()
        if ret:
            cv2.imwrite(filename, frame)
            QMessageBox.information(self, "拍照成功", f"照片已保存为 {filename}")

            with open('student_info.csv', 'a') as file:
                writer = csv.writer(file)
                writer.writerow([student_id, name, '', ''])
        else:
            QMessageBox.warning(self, "拍照失败", "无法拍摄照片")

    @pyqtSlot()
    def open_admin_management_dialog(self):
        dialog = AdminManagementDialog()
        dialog.exec_()


class Ui_OutputDialog(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("./outputwindow.ui", self)

        # 初始化计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        # 设置日期和时间标签
        now = QDate.currentDate()
        current_date = now.toString('yyyy/MM/dd ddd  ')
        current_time = datetime.datetime.now().strftime("%H:%M:%s")
        self.Date_Label.setText(current_date)
        self.Time_Label.setText(current_time)

        # 初始化变量
        self.image = None
        self.class_names = []
        self.encode_list = []

        # 加载学生信息
        self.student_id_to_name = {}
        self.load_student_info()

        # 连接按钮的点击事件
        self.ClockInButton.clicked.connect(self.update_attendance_from_csv)

        # 设置管理员登录按钮
        self.admin_login_button = QPushButton("管理员登录")
        self.admin_login_button.clicked.connect(self.open_admin_login_dialog)
        self.horizontalLayout.addWidget(self.admin_login_button)

        # 设置按钮样式
        self.set_button_style()

    def set_button_style(self):
        button_style = """
            QPushButton {
                background-color: #D3D3D3;
                border: none;
                color: #333333;
                padding: 7px 17px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #808080;
            }

            QPushButton:pressed {
                background-color: #696969;
            }
        """

        self.admin_login_button.setStyleSheet(button_style)
        self.ClockInButton.setStyleSheet(button_style)
        self.ClockOutButton.setStyleSheet(button_style)

    @pyqtSlot()
    def open_admin_login_dialog(self):
        dialog = AdminLoginDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.open_admin_functions_dialog()

    @pyqtSlot()
    def open_admin_functions_dialog(self):
        dialog = AdminFunctionsDialog()
        dialog.exec_()

    def load_student_info(self):
        try:
            with open('student_info.csv', 'r') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if len(row) == 4:
                        student_id, name, status, time = row
                        self.student_id_to_name[student_id] = name
        except FileNotFoundError:
            with open('student_info.csv', 'w') as file:
                writer = csv.writer(file)
                writer.writerow(['student_id', 'name', 'status', 'time'])
                writer.writerow(['2022210686', 'GSC', 'Present', '2024-04-12 08:00:00'])

    def update_attendance_from_csv(self):
        with open('Attendance.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                try:
                    first_item = row[0].split('_')
                    if len(first_item) == 2:
                        new_row = [first_item[0], first_item[1]] + row[1:]
                        row = new_row
                    if not self.check_existing_record(row):
                        with open('student_info.csv', 'a') as student_info_file:
                            writer = csv.writer(student_info_file)
                            writer.writerow(row)

                        self.remove_duplicate_records()
                except ValueError:
                    print("Error: Skipping invalid row:", row)

    def check_existing_record(self, new_row):
        with open('student_info.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row == new_row:
                    return True
        return False

    def remove_duplicate_records(self):
        with open('student_info.csv', 'r') as file:
            lines = file.readlines()

        unique_lines = list(set(lines))

        with open('student_info.csv', 'w') as file:
            file.writelines(unique_lines)

    @pyqtSlot()
    def startVideo(self, camera_name):
        if len(camera_name) == 1:
            self.capture = cv2.VideoCapture(int(camera_name))
        else:
            self.capture = cv2.VideoCapture(camera_name)
        self.timer = QTimer(self)
        path = 'ImagesAttendance'
        if not os.path.exists(path):
            os.mkdir(path)

        attendance_list = os.listdir(path)

        for cl in attendance_list:
            cur_img = cv2.imread(f'{path}/{cl}')
            self.class_names.append(os.path.splitext(cl)[0])
            self.encode_list.append(face_recognition.face_encodings(cur_img)[0])

        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)

    def face_rec_(self, frame, encode_list_known, class_names):
        def mark_attendance(name, confidence):
            if self.ClockInButton.isChecked():
                self.ClockInButton.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                    if name != 'unknown':
                        buttonReply = QMessageBox.question(self, 'Welcome ' + name, 'Are you Clocking In?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            f.writelines(f'\n{name},{date_time_string},Clock In')
                            self.ClockInButton.setChecked(False)

                            self.NameLabel.setText(name)
                            self.StatusLabel.setText('Clocked In')
                            self.HoursLabel.setText('Measuring')
                            self.MinLabel.setText('')

                            self.Time1 = datetime.datetime.now()
                            self.ClockInButton.setEnabled(True)
                        else:
                            print('Not clicked.')
                            self.ClockInButton.setEnabled(True)
            elif self.ClockOutButton.isChecked():
                self.ClockOutButton.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                    if name != 'unknown':
                        buttonReply = QMessageBox.question(self, 'Cheers ' + name, 'Are you Clocking Out?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            f.writelines(f'\n{name},{date_time_string},Clock Out')
                            self.ClockOutButton.setChecked(False)

                            self.NameLabel.setText(name)
                            self.StatusLabel.setText('Clocked Out')
                            self.Time2 = datetime.datetime.now()

                            self.ElapseList(name)
                            self.TimeList2.append(datetime.datetime.now())
                            CheckInTime = self.TimeList1[-1]
                            CheckOutTime = self.TimeList2[-1]
                            self.ElapseHours = (CheckOutTime - CheckInTime)
                            self.MinLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60) % 60) + 'm')
                            self.HoursLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60 ** 2)) + 'h')
                            self.ClockOutButton.setEnabled(True)
                        else:
                            print('Not clicked.')
                            self.ClockOutButton.setEnabled(True)

        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)

        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            match = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.2)
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "unknown"
            min_distance = min(face_dis)
            if min_distance < 0.6:
                best_match_index = np.argmin(face_dis)
                name = class_names[best_match_index].upper()
                confidence = 0.5 + (1 - min_distance) * 0.5
            else:
                confidence = 0

            if confidence > 0.5:
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, f"{name} - C: {confidence:.2f}", (x1 + 6, y2 - 6),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                mark_attendance(name, confidence)

        return frame

    def ElapseList(self, name):
        with open('Attendance.csv', "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            for row in csv_reader:
                if row[0] == name and row[2] == 'Clock In':
                    Time1 = datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S')
                    self.TimeList1.append(Time1)
                elif row[0] == name and row[2] == 'Clock Out':
                    Time2 = datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S')
                    self.TimeList2.append(Time2)

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.class_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):
        image = cv2.resize(image, (640, 480))
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)

    @pyqtSlot()
    def update_time(self):
        current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.Time_Label.setText(current_time)


class AttendanceManagementDialog(QDialog):
    def create_date_dropdowns(self):
        # 创建日期选择下拉菜单
        self.year_combo = QComboBox()
        self.month_combo = QComboBox()
        self.day_combo = QComboBox()

        self.populate_year_combo()  # 填充年份
        self.populate_month_combo()  # 填充月份
        self.populate_day_combo()  # 填充日期

        # 添加日期选择到布局
        layout = QVBoxLayout()
        layout.addWidget(self.year_combo)
        layout.addWidget(self.month_combo)
        layout.addWidget(self.day_combo)

        return layout

    def get_selected_date(self):
        year = self.year_combo.currentText()
        month = self.month_combo.currentText()
        day = self.day_combo.currentText()
        return f"{year}/{month}/{day}"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("签到信息管理")
        layout = QVBoxLayout()

        self.add_record_button = QPushButton("添加签到记录")
        self.add_record_button.clicked.connect(self.add_record)
        layout.addWidget(self.add_record_button)

        self.delete_record_button = QPushButton("删除签到记录")
        self.delete_record_button.clicked.connect(self.delete_record)
        layout.addWidget(self.delete_record_button)

        self.export_button = QPushButton("导出签到记录")
        self.export_button.clicked.connect(self.export_records)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def populate_year_combo(self):
        years = [str(year) for year in range(2000, QDate.currentDate().year() + 1)]
        self.year_combo.addItems(years)

    def populate_month_combo(self):
        months = [str(month).zfill(2) for month in range(1, 13)]
        self.month_combo.addItems(months)

    def populate_day_combo(self):
        days = [str(day).zfill(2) for day in range(1, 32)]
        self.day_combo.addItems(days)

    import datetime

    def add_record(self):
        # 创建一个新的对话框窗口
        dialog = QDialog(self)
        dialog.setWindowTitle("添加签到记录")

        # 使用QFormLayout布局，将标签和输入字段组合在一起
        layout = QFormLayout()

        # 添加输入字段和标签
        name_edit = QLineEdit()
        layout.addRow("学生姓名:", name_edit)

        student_id_edit = QLineEdit()
        layout.addRow("学生学号:", student_id_edit)

        # 添加日期选择器
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        layout.addRow("日期:", date_edit)

        # 添加确定和取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)

        # 连接按钮的信号和槽函数
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        # 设置对话框的主布局
        dialog.setLayout(layout)

        # 显示对话框并等待用户操作
        if dialog.exec_() == QDialog.Accepted:
            # 获取输入的信息
            name = name_edit.text()
            student_id = student_id_edit.text()
            selected_date = date_edit.date().toString("yy/MM/dd")

            # 检查输入是否完整
            if not name:
                QMessageBox.warning(self, "输入错误", "学生姓名不能为空！")
                return
            if not student_id:
                QMessageBox.warning(self, "输入错误", "学生学号不能为空！")
                return
            if not selected_date:
                QMessageBox.warning(self, "输入错误", "日期不能为空！")
                return

            # 获取当前系统时间
            current_time = datetime.datetime.now().strftime('%H:%M:%S')

            # 将日期和时间组合成一个字符串，使用空格分隔
            datetime_str = f"{selected_date} {current_time}"

            # 将记录追加到CSV文件
            with open('student_info.csv', 'a') as file:
                writer = csv.writer(file)
                writer.writerow([name, student_id, datetime_str, 'Sign In'])

            # 显示添加成功的消息框
            QMessageBox.information(self, "添加成功", "签到记录添加成功！")

    def delete_record(self):
        # 创建输入对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("删除签到记录")
        layout = QVBoxLayout()

        # 添加姓名输入字段
        name_label = QLabel("学生姓名:")
        name_edit = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(name_edit)

        # 添加学号输入字段
        student_id_label = QLabel("学生学号:")
        student_id_edit = QLineEdit()
        layout.addWidget(student_id_label)
        layout.addWidget(student_id_edit)

        # 添加日期选择器
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        layout.addWidget(QLabel("选择日期:"))
        layout.addWidget(date_edit)

        # 添加确定和取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        # 连接按钮的信号和槽函数
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        # 设置对话框的主布局
        dialog.setLayout(layout)

        # 显示对话框并等待用户操作
        while True:
            if not dialog.exec_():
                return

            # 获取用户输入的姓名、学号和日期
            name = name_edit.text()
            student_id = student_id_edit.text()
            selected_date = date_edit.date().toString("yy/MM/dd")  # 获取选中的日期

            # 检查输入是否完整
            if not name:
                QMessageBox.warning(self, "输入错误", "学生姓名不能为空！")
                continue
            if not student_id:
                QMessageBox.warning(self, "输入错误", "学生学号不能为空！")
                continue
            if not selected_date:
                QMessageBox.warning(self, "输入错误", "日期不能为空！")
                continue

            # 读取CSV文件中的记录到内存
            with open('student_info.csv', 'r') as file:
                lines = list(csv.reader(file))

            # 在内存中进行删除操作
            filtered_lines = [line for line in lines if
                              line[0] != name or line[1] != student_id or line[2].split()[0] != selected_date]

            # 检查是否有记录被删除
            if len(filtered_lines) == len(lines):
                QMessageBox.warning(self, "删除失败", "找不到匹配的记录！")
                continue

            # 将过滤后的记录写回CSV文件
            with open('student_info.csv', 'w') as file:
                writer = csv.writer(file)
                writer.writerows(filtered_lines)

            QMessageBox.information(self, "删除成功", "签到记录删除成功！")
            break

    def export_records(self):
        name, ok = QInputDialog.getText(self, '导出签到记录', '请输入学生姓名:')
        if not ok:
            return

        student_id, ok = QInputDialog.getText(self, '导出签到记录', '请输入学生学号:')
        if not ok:
            return

        selected_date = self.get_selected_date()

        # Export records from CSV based on user input
        with open('student_info.csv', 'r') as file:
            reader = csv.reader(file)
            records = [row for row in reader if row[0] == name and row[1] == student_id]

        if not records:
            QMessageBox.warning(self, "错误", "找不到匹配的记录！")
            return

        # Write records to a new CSV file
        filename, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w') as file:
                writer = csv.writer(file)
                writer.writerows(records)

        QMessageBox.information(self, "导出成功", "签到记录导出成功！")

    def get_selected_date(self):
        year, ok = QInputDialog.getText(self, '选择日期', '请输入年份:')
        if not ok:
            return

        month, ok = QInputDialog.getText(self, '选择日期', '请输入月份:')
        if not ok:
            return

        day, ok = QInputDialog.getText(self, '选择日期', '请输入日期:')
        if not ok:
            return

        return f"{year}/{month}/{day}"


if __name__ == "__main__":
    app = QApplication(sys.argv)

    ui = Ui_OutputDialog()
    ui.show()
    ui.startVideo("0")

    sys.exit(app.exec_())
