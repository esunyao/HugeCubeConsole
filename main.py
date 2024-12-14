import json
import sys
import re

from OpenGL.raw.GLU import gluPerspective
from PyQt5 import QtWidgets, QtGui, QtCore
import window
import paho.mqtt.client as mqtt
from OpenGL.GL import *
from urllib.parse import urlparse
import __main__


class CustomOpenGLWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None):
        super(CustomOpenGLWidget, self).__init__(parent)
        self.color = (1.0, 1.0, 1.0, 1.0)  # 默认颜色为白色
        self.brightness = 1.0  # 默认亮度为 1.0

    def initializeGL(self):
        glClearColor(*self.color)
        glEnable(GL_DEPTH_TEST)  # 启用深度测试

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glBegin(GL_QUADS)
        glColor4f(*self.color)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f(1.0, -1.0, -1.0)
        glVertex3f(1.0, 1.0, -1.0)
        glVertex3f(-1.0, 1.0, -1.0)
        glEnd()

    def setColor(self, color, brightness=1.0):
        self.color = tuple(c * brightness for c in color)
        self.update()


def on_message(client, userdata, msg):
    global config, MODE
    if msg.topic == "superCube/callback":
        payload = msg.payload.decode()
        if MODE == "id":
            devices = re.findall(r'\d+\/\d+:(\w+)', payload)
            devices_box = MainWindow.findChild(QtWidgets.QComboBox, "DevicesBox")
            if devices_box is not None:
                existing_devices = {devices_box.itemText(i) for i in range(devices_box.count())}
                for device_id in devices:
                    if device_id not in existing_devices:
                        devices_box.addItem(device_id)
        if MODE == "config":
            config = payload[4:]
            MODE = "asdf"
            js = json.loads(config)
            for i in js["light"]:
                pin = i["pin"]
                r, g, b = i["r"], i["g"], i["b"]
                brightness = i["bright"] / 100.0
                gl_widget = MainWindow.findChild(CustomOpenGLWidget, f"GLLLLL{pin}")
                if gl_widget and isinstance(gl_widget, CustomOpenGLWidget):
                    gl_widget.setColor((r / 255.0, g / 255.0, b / 255.0, 1.0), brightness)
                else:
                    print(
                        f"Widget GLLLLL{pin} not found. Available widgets: {[w.objectName() for w in MainWindow.findChildren(CustomOpenGLWidget)]}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # 连接成功后取消隐藏 label_18
        label_18 = MainWindow.findChild(QtWidgets.QLabel, "label_18")
        if label_18:
            label_18.setHidden(False)
        # 订阅 superCube/callback 主题
        client.subscribe("superCube/callback")
        client.on_message = on_message
    else:
        print("Failed to connect, return code %d\n", rc)


def check_mqtt_connection():
    global mqtt_client
    if mqtt_client and mqtt_client.is_connected():
        return True
    else:
        QtWidgets.QMessageBox.warning(MainWindow, "警告", "MQTT 未连接到服务器")
        return False


def on_connect_mqtt_clicked():
    global mqtt_client
    # 获取 MqttLocation 的数据
    mqtt_location = MainWindow.findChild(QtWidgets.QTextEdit, "MqttLocation")
    mqtt_username = MainWindow.findChild(QtWidgets.QTextEdit, "MqttUsername")
    mqtt_passwd = MainWindow.findChild(QtWidgets.QTextEdit, "MqttPasswd")
    if mqtt_location and mqtt_username and mqtt_passwd:
        url = mqtt_location.toPlainText()
        parsed_url = urlparse(url)
        broker = parsed_url.hostname
        port = parsed_url.port or 1883
        username = mqtt_username.toPlainText()
        password = mqtt_passwd.toPlainText()

        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(username, password)
        mqtt_client.on_connect = on_connect

        try:
            mqtt_client.connect(broker, port, 60)
            mqtt_client.loop_start()
        except Exception as e:
            QtWidgets.QMessageBox.critical(MainWindow, "错误", f"无法连接到MQTT服务器: {e}")
    else:
        QtWidgets.QMessageBox.warning(MainWindow, "警告", "无法获取到相关数据")


def on_get_devices_clicked():
    if not check_mqtt_connection():
        return
    global mqtt_client, MODE
    MODE = "id"
    if mqtt_client:
        mqtt_client.publish("superCube/topic", '{"command":"config ID get"}')
        QtCore.QTimer.singleShot(1000, lambda: setattr(__main__, 'MODE', 'asdf'))


def on_sync_color_clicked():
    selected_device = get_selected_device()
    if selected_device is None and not is_all_select_checked():
        return
    global mqtt_client, MODE
    if mqtt_client:
        payload = {"command": "config get"}
        if selected_device:
            payload["devices"] = selected_device
        mqtt_client.publish("superCube/topic", json.dumps(payload))
        MODE = "config"


real_time_mode = False

def update_color_viewer():
    r = MainWindow.findChild(QtWidgets.QSlider, "R_Line").value()
    g = MainWindow.findChild(QtWidgets.QSlider, "G_Line").value()
    b = MainWindow.findChild(QtWidgets.QSlider, "B_Line").value()
    brightness = MainWindow.findChild(QtWidgets.QSlider, "BR_Line").value() / 100.0
    color_viewer = MainWindow.findChild(CustomOpenGLWidget, "ColorViewer")
    if color_viewer and isinstance(color_viewer, CustomOpenGLWidget):
        color_viewer.setColor((r / 255.0, g / 255.0, b / 255.0, 1.0), brightness)

    # 更新 R_COUNT、G_COUNT、B_COUNT 和 BR_COUNT 标签的文本
    r_count_label = MainWindow.findChild(QtWidgets.QLabel, "R_COUNT")
    g_count_label = MainWindow.findChild(QtWidgets.QLabel, "G_COUNT")
    b_count_label = MainWindow.findChild(QtWidgets.QLabel, "B_COUNT")
    br_count_label = MainWindow.findChild(QtWidgets.QLabel, "BR_COUNT")

    if r_count_label:
        r_count_label.setText(str(r))
    if g_count_label:
        g_count_label.setText(str(g))
    if b_count_label:
        b_count_label.setText(str(b))
    if br_count_label:
        br_count_label.setText(str(int(brightness * 100)))

    # 如果是实时模式，自动执行 SYNC_COMMAND
    if real_time_mode:
        on_sync_command_button_clicked()

def execute_config_mode():
    global config, MODE
    if MODE == "config":
        js = json.loads(config)
        for i in js["light"]:
            pin = i["pin"]
            r, g, b = i["r"], i["g"], i["b"]
            brightness = i["bright"] / 100.0
            gl_widget = MainWindow.findChild(CustomOpenGLWidget, f"GLLLLL{pin}")
            if gl_widget and isinstance(gl_widget, CustomOpenGLWidget):
                gl_widget.setColor((r / 255.0, g / 255.0, b / 255.0, 1.0), brightness)
            else:
                print(f"Widget GLLLLL{pin} not found. Available widgets: {[w.objectName() for w in MainWindow.findChildren(CustomOpenGLWidget)]}")

def on_sync_button_clicked():
    if not check_mqtt_connection():
        return
    r = MainWindow.findChild(QtWidgets.QSlider, "R_Line").value()
    g = MainWindow.findChild(QtWidgets.QSlider, "G_Line").value()
    b = MainWindow.findChild(QtWidgets.QSlider, "B_Line").value()
    brightness = MainWindow.findChild(QtWidgets.QSlider, "BR_Line").value()
    global config
    if not config:
        QtWidgets.QMessageBox.warning(MainWindow, "警告", "配置数据为空，请先同步配置")
        return
    js = json.loads(config)
    surface = MainWindow.findChild(QtWidgets.QComboBox, "Surface")
    if surface is None:
        QtWidgets.QMessageBox.warning(MainWindow, "警告", "请选择要设定的pin口")
        return
    for i in js["light"]:
        if i["pin"] == int(surface.currentText()):
            i["r"] = r
            i["g"] = g
            i["b"] = b
            i["bright"] = brightness
            config = json.dumps(js)
            selected_device = get_selected_device()
            if selected_device is None and not is_all_select_checked():
                return
            payload = {"command": "config setFromJson", "config": js}
            if selected_device:
                payload["devices"] = selected_device
            mqtt_client.publish("superCube/topic", json.dumps(payload).replace("\\", ""))
            MODE = "config"
            execute_config_mode()
            on_sync_command_button_clicked()
            return

    QtWidgets.QMessageBox.warning(MainWindow, "警告", "未找到匹配的pin口")

def on_sync_command_button_clicked():
    if not check_mqtt_connection():
        return
    selected_device = get_selected_device()
    if selected_device is None and not is_all_select_checked():
        return
    r = MainWindow.findChild(QtWidgets.QSlider, "R_Line").value()
    g = MainWindow.findChild(QtWidgets.QSlider, "G_Line").value()
    b = MainWindow.findChild(QtWidgets.QSlider, "B_Line").value()
    brightness = MainWindow.findChild(QtWidgets.QSlider, "BR_Line").value()
    surface = MainWindow.findChild(QtWidgets.QComboBox, "Surface")
    if surface is None:
        QtWidgets.QMessageBox.warning(MainWindow, "警告", "请选择要设定的pin口")
        return
    payload = {
        "command": "Server_NeoPixel",
        "r": r,
        "g": g,
        "b": b,
        "bright": brightness,
        "num": ["0-24"],
        "save": False,
        "pin": int(surface.currentText())
    }
    if selected_device:
        payload["devices"] = selected_device
    mqtt_client.publish("superCube/topic", json.dumps(payload))
    MODE = "config"
    execute_config_mode()

def on_restart_button_clicked():
    if not check_mqtt_connection():
        return
    selected_device = get_selected_device()
    if selected_device is None and not is_all_select_checked():
        return
    payload = {"command": "restart"}
    if selected_device:
        payload["devices"] = selected_device
    mqtt_client.publish("superCube/topic", json.dumps(payload))


def get_selected_device():
    all_select_checkbox = MainWindow.findChild(QtWidgets.QCheckBox, "all_select")
    if all_select_checkbox and all_select_checkbox.isChecked():
        return None  # 如果 all_select 被选中，返回 None
    devices_box = MainWindow.findChild(QtWidgets.QComboBox, "DevicesBox")
    if devices_box is not None:
        selected_device = devices_box.currentText()
        if not selected_device:
            QtWidgets.QMessageBox.warning(MainWindow, "警告", "请先选择一个设备")
            return None
        return selected_device
    else:
        QtWidgets.QMessageBox.warning(MainWindow, "警告", "DevicesBox 未找到")
        return None


def on_clear_devices_button_clicked():
    devices_box = MainWindow.findChild(QtWidgets.QComboBox, "DevicesBox")
    if devices_box is not None:
        devices_box.clear()
    else:
        QtWidgets.QMessageBox.warning(MainWindow, "警告", "DevicesBox 未找到")

def on_mode_qiehuan_button_clicked():
    global real_time_mode
    color_mode_label = MainWindow.findChild(QtWidgets.QLabel, "COLOR_MODE")
    if color_mode_label:
        if color_mode_label.text() == "实时模式":
            color_mode_label.setText("非实时模式")
            real_time_mode = False
        else:
            color_mode_label.setText("实时模式")
            real_time_mode = True

def on_all_select_toggled(checked):
    devices_box = MainWindow.findChild(QtWidgets.QComboBox, "DevicesBox")
    if devices_box:
        for i in range(devices_box.count()):
            item = devices_box.model().item(i)
            item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)

def is_all_select_checked():
    all_select_checkbox = MainWindow.findChild(QtWidgets.QCheckBox, "all_select")
    return all_select_checkbox and all_select_checkbox.isChecked()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = window.Ui_MainWindow()
    ui.setupUi(MainWindow)

    # 初始化 mqtt_client
    mqtt_client = None
    config = ""
    MODE = "asdf"

    # 将 label_18 设定为隐藏
    label_18 = MainWindow.findChild(QtWidgets.QLabel, "label_18")
    if label_18:
        label_18.setHidden(True)

    # 获取已经在 UI 文件中定义的 QOpenGLWidget 实例
    for i in range(1, 7):
        gl_widget = MainWindow.findChild(QtWidgets.QOpenGLWidget, f"GLLLLL{i}")
        if gl_widget:
            custom_gl_widget = CustomOpenGLWidget(MainWindow)
            custom_gl_widget.setObjectName(f"GLLLLL{i}")
            custom_gl_widget.setGeometry(gl_widget.geometry())
            gl_widget.setParent(None)  # 移除原有的 QOpenGLWidget
            MainWindow.layout().addWidget(custom_gl_widget)  # 添加新的 CustomOpenGLWidget

    # 替换 ColorViewer 实例
    color_viewer_widget = MainWindow.findChild(QtWidgets.QOpenGLWidget, "ColorViewer")
    if color_viewer_widget:
        custom_color_viewer = CustomOpenGLWidget(MainWindow)
        custom_color_viewer.setObjectName("ColorViewer")
        custom_color_viewer.setGeometry(color_viewer_widget.geometry())
        color_viewer_widget.setParent(None)  # 移除原有的 QOpenGLWidget
        MainWindow.layout().addWidget(custom_color_viewer)  # 添加新的 CustomOpenGLWidget

    # 监听颜色和亮度滑块的值变化
    r_slider = MainWindow.findChild(QtWidgets.QSlider, "R_Line")
    g_slider = MainWindow.findChild(QtWidgets.QSlider, "G_Line")
    b_slider = MainWindow.findChild(QtWidgets.QSlider, "B_Line")
    br_slider = MainWindow.findChild(QtWidgets.QSlider, "BR_Line")

    if r_slider:
        r_slider.valueChanged.connect(update_color_viewer)
    if g_slider:
        g_slider.valueChanged.connect(update_color_viewer)
    if b_slider:
        b_slider.valueChanged.connect(update_color_viewer)
    if br_slider:
        br_slider.valueChanged.connect(update_color_viewer)

    # 监听 SYNC 按钮的点击事件
    sync_button = MainWindow.findChild(QtWidgets.QToolButton, "SYNC")
    if sync_button:
        sync_button.clicked.connect(on_sync_button_clicked)

    # 监听 RESTART 按钮的点击事件
    restart_button = MainWindow.findChild(QtWidgets.QToolButton, "RESTART")
    if restart_button:
        restart_button.clicked.connect(on_restart_button_clicked)

    # 监听 SYNC_COMMAND 按钮的点击事件
    sync_command_button = MainWindow.findChild(QtWidgets.QToolButton, "SYNC_COMMAND")
    if sync_command_button:
        sync_command_button.clicked.connect(on_sync_command_button_clicked)

    # 监听 ClearDevices 按钮的点击事件
    clear_devices_button = MainWindow.findChild(QtWidgets.QToolButton, "ClearDevices")
    if clear_devices_button:
        clear_devices_button.clicked.connect(on_clear_devices_button_clicked)

    # 监听 MODE_QIEHUAN 按钮的点击事件
    mode_qiehuan_button = MainWindow.findChild(QtWidgets.QToolButton, "MODE_QIEHUAN")
    if mode_qiehuan_button:
        mode_qiehuan_button.clicked.connect(on_mode_qiehuan_button_clicked)

    # 监听 all_select 复选框的切换事件
    all_select_checkbox = MainWindow.findChild(QtWidgets.QCheckBox, "all_select")
    if all_select_checkbox:
        all_select_checkbox.toggled.connect(on_all_select_toggled)

    MainWindow.show()

    connect_mqtt_button = MainWindow.findChild(QtWidgets.QToolButton, "ConnectMqtt")
    if connect_mqtt_button:
        connect_mqtt_button.clicked.connect(on_connect_mqtt_clicked)

    # 监听 getDevices 按钮的点击事件
    get_devices_button = MainWindow.findChild(QtWidgets.QToolButton, "getDevices")
    if get_devices_button:
        get_devices_button.clicked.connect(on_get_devices_clicked)

    sync_color_button = MainWindow.findChild(QtWidgets.QToolButton, "SyncColor")
    if sync_color_button:
        sync_color_button.clicked.connect(on_sync_color_clicked)

    sys.exit(app.exec_())
