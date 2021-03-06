# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1530, 738)
        self.video_label = QtWidgets.QLabel(Form)
        self.video_label.setGeometry(QtCore.QRect(9, 9, 1260, 720))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.video_label.sizePolicy().hasHeightForWidth())
        self.video_label.setSizePolicy(sizePolicy)
        self.video_label.setMinimumSize(QtCore.QSize(1260, 720))
        self.video_label.setFrameShape(QtWidgets.QFrame.Box)
        self.video_label.setText("")
        self.video_label.setObjectName("video_label")
        self.formLayoutWidget = QtWidgets.QWidget(Form)
        self.formLayoutWidget.setGeometry(QtCore.QRect(1304, 9, 221, 241))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.formLayoutWidget)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.fps_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.fps_label.setObjectName("fps_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.fps_label)
        self.label_4 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.altitude_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.altitude_label.setObjectName("altitude_label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.altitude_label)
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.latitude_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.latitude_label.setObjectName("latitude_label")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.latitude_label)
        self.label_5 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.longitude_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.longitude_label.setObjectName("longitude_label")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.longitude_label)
        self.label_3 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.gmt_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.gmt_label.setObjectName("gmt_label")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.gmt_label)
        self.label_14 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_14.setText("")
        self.label_14.setObjectName("label_14")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_14)
        self.label_7 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.label_7)
        self.label_8 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.label_8)
        self.pressure_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.pressure_label.setObjectName("pressure_label")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.pressure_label)
        self.label_10 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_10.setObjectName("label_10")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.label_10)
        self.temperature_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.temperature_label.setObjectName("temperature_label")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.temperature_label)
        self.sync_label = QtWidgets.QLabel(Form)
        self.sync_label.setGeometry(QtCore.QRect(1370, 250, 68, 17))
        self.sync_label.setText("")
        self.sync_label.setObjectName("sync_label")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Street Light Client"))
        self.label.setText(_translate("Form", "FPS"))
        self.fps_label.setText(_translate("Form", "0"))
        self.label_4.setText(_translate("Form", "Altitude"))
        self.altitude_label.setText(_translate("Form", "0"))
        self.label_2.setText(_translate("Form", "Latitude"))
        self.latitude_label.setText(_translate("Form", "0"))
        self.label_5.setText(_translate("Form", "Longitude"))
        self.longitude_label.setText(_translate("Form", "0"))
        self.label_3.setText(_translate("Form", "GMT"))
        self.gmt_label.setText(_translate("Form", "0"))
        self.label_7.setText(_translate("Form", "Sensors"))
        self.label_8.setText(_translate("Form", "Pressure"))
        self.pressure_label.setText(_translate("Form", "0"))
        self.label_10.setText(_translate("Form", "Temperature"))
        self.temperature_label.setText(_translate("Form", "0"))

