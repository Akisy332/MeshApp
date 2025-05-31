import os
import sys
from PyQt5.QtWidgets import QApplication, QGraphicsPixmapItem, QPushButton, QGraphicsLineItem, QGraphicsTextItem, QMenu, QMessageBox
from PyQt5.QtGui import QPixmap, QColor, QImage, QPainter, QIcon, QPen, QCursor, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal, QSize, QPoint, pyqtSlot
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QPushButton, QGraphicsPathItem
from PyQt5.QtGui import QPainter, QPen, QPainterPath
from PyQt5.QtCore import Qt, QPointF
import time
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QByteArray
from base64 import b64decode
from .utility_functions import decimal_to_osm, osm_to_decimal

from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from .mapView import MapView

def resource_path(relative_path):
    """ Получает правильный путь к ресурсам """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class Tile:
    def __init__(self, mapView: "MapView", image, tile_name_position):
        self.mapView = mapView
        self.image = image
        self.tile_name_position = tile_name_position
        
        self.pixmap_item = None

        self.canvas_object = None
        self.widget_tile_width = 0
        self.widget_tile_height = 0

        canvas_pos_x, canvas_pos_y = self.get_canvas_pos()
        self.canvas_object = self.mapView.tile_group
        self.pixmap_item = QGraphicsPixmapItem(self.image)
        self.pixmap_item.setPos(canvas_pos_x, canvas_pos_y)
        self.canvas_object.addToGroup(self.pixmap_item)  

        self.draw()

    def __del__(self):
        # if Tile object gets garbage collected or deleted, delete image from canvas
        self.delete()

    def set_image_and_position(self, image, tile_name_position):
        self.image = image
        self.tile_name_position = tile_name_position
        self.setImage(image)
        
        


    def setImage(self, image):
        self.image = image
        # if not (self.image == self.mapView.tileManager.notLoadedTileImage or self.image == self.mapView.tileManager.emptyTileImage):
        self.pixmap_item.setPixmap(self.image)
        self.draw(image_update=True)

    def get_canvas_pos(self):
        self.widget_tile_width = self.mapView.lowerRightTilePos[0] - self.mapView.upperLeftTilePos[0]
        self.widget_tile_height = self.mapView.lowerRightTilePos[1] - self.mapView.upperLeftTilePos[1]
        
        canvas_pos_x = ((self.tile_name_position[0] - self.mapView.upperLeftTilePos[
            0]) / self.widget_tile_width) * self.mapView._width
        canvas_pos_y = ((self.tile_name_position[1] - self.mapView.upperLeftTilePos[
            1]) / self.widget_tile_height) * self.mapView._height
        
        return canvas_pos_x, canvas_pos_y

    def delete(self):
        try:
            if not self.pixmap_item == None:
                if self.pixmap_item in self.mapView.mapScene.items():
                    self.mapView.mapScene.removeItem(self.pixmap_item)
            self.canvas_object = None
        except Exception:
            pass

    def draw(self, image_update=False):
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos()
        self.pixmap_item.setPos(canvas_pos_x, canvas_pos_y)



class Marker(QGraphicsPixmapItem):
    def __init__(self,
                 position: tuple,
                 text: str = None,
                 textColor: str = "#652A22",
                 font: QFont = "Tahoma 11 bold",
                 markerColorCircle: str = "#000000",
                 markerColorOutside: str = "#FF0000",
                 command: Callable = None,
                 icon: QImage = None,
                 iconHeight = None,
                 iconWidth = None,
                 imageZoomVisibility: tuple = (0, float("inf"))):
        super().__init__()
        self.mapView: MapView = None
        self.position = position
        self.icon = icon
        
        self.imageZoomVisibility = imageZoomVisibility
        self.command = command
        
        self.imageVisible = False
        self.markerVisible = True
        
        self.itemText = None
        
        # Переделать создание иконки маркера
        if self.icon is None:
            # Убрать в другое место, ибо каждый новый маркер опять сохраняет изображение в память
            currentPath = os.path.dirname(os.path.abspath(__file__))
            imagePath = resource_path('../images/marker.png') 

            self.icon = QImage(imagePath)
            if self.icon.isNull():
                print("Failed to load marker image:", imagePath)
            else:
                iconWidth = self.icon.width() // 2
                iconHeight = self.icon.height() // 2
            self.icon = self.__imageFromPixmap(self.icon, iconWidth, iconHeight)
            
            colors = (QColor("#FF0000"), QColor(markerColorOutside), QColor("#000000"), QColor(markerColorCircle))
            if markerColorCircle  != "#000000" or markerColorOutside != "#FF0000":
                self.changeLolorMarker(colors)
        else:
            self.icon = self.__imageFromPixmap(self.icon, iconWidth, iconHeight)
        
        # пофиксить курсор над текстом
        self.setAcceptHoverEvents(True)
        
        self.setOffset(-self.icon.rect().width()/2, -self.icon.rect().height())
        self.setPixmap(self.icon)
        

        self.setZValue(3)
        
        #пофиксить исчезание текста при смене карты и смене видимости
        self.text = text
        if text is not None:
            self.setText(text, textColor, font)
        
    def __imageFromPixmap(self, image: QImage, width: int = None, height: int = None) -> QPixmap:
        if width is None:
            width = image.width()
        if height is None:
            height = image.height()
        image = image.scaled(width, height)
        image = QPixmap.fromImage(image)
        return image
    
    def changeLolorMarker(self, colors: list = [QColor]):        
    # colors: the first element is the old color, the second is the new color, etc.  
    # the colors of the initial marker: markerColorOutside = #FF0000", markerColorCircle = #000000 
        image = self.icon.toImage()        
        for x in range(image.width()):            
            for y in range(image.height()):                
                pixelColor = image.pixelColor(x, y)                
                if pixelColor.alpha() > 0:  # если пиксель не прозрачный                    
                    for idx, newPixelColor in enumerate(colors):                        
                        if newPixelColor == pixelColor and idx % 2 == 0:                        
                            # Изменяем цвет на новый
                            new_color = colors[idx + 1]  # Получаем следующий (новый) цвет
                            # Устанавливаем новый цвет
                            pixelColor.setRgb(new_color.red(), new_color.green(), new_color.blue())
                            break
                    image.setPixelColor(x, y, pixelColor)        
        self.icon = self.__imageFromPixmap(image)

    def delete(self):
        if self.mapView:
            self.mapView.elementsList.remove(self)
            self.mapView.mapScene.removeItem(self)

    def setPosition(self, deg_x, deg_y):
        self.position = (deg_x, deg_y)
        self.draw()

    def __textOffset(self):
        textOffsetY = self.icon.rect().height() + 20 if self.icon is not None else 70
        textOffsetX = self.itemText.boundingRect().width() / 2
        return textOffsetX, textOffsetY
    
    def setText(self, text, textColor: str = "#652A22", font: QFont = "Tahoma 11 bold"):
        self.text = text
        if self.itemText is None:
            self.itemText = QGraphicsTextItem(text, self)
        else:
            self.itemText.setPlainText(text)
        self.itemText.setFont(QFont(font, 12)) 
        self.itemText.setDefaultTextColor(QColor(textColor)) 
        textOffsetX, textOffsetY = self.__textOffset()
        self.itemText.setPos(-textOffsetX, -textOffsetY)
        self.draw()

    # debug
    def setIcon(self, new_icon: QImage, width: int = None, height: int = None):
        self.icon = self.__imageFromPixmap(new_icon, width, height)
        self.setPixmap(self.icon)
        self.setOffset(-self.icon.rect().width()/2, -self.icon.rect().height())
        textOffsetX, textOffsetY = self.__textOffset()
        self.itemText.setPos(-textOffsetX, -textOffsetY)
        self.draw()

    def setVisibleImage(self, visible: bool):
        self.imageVisible = visible
        self.draw()

    def setVisibleMarker(self, visible: bool):
        self.markerVisible = visible
        self.draw()

    def hoverEnterEvent(self, event):
        if self.command != None and self.markerVisible == True:
            QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.command != None and self.markerVisible == True:
            QApplication.restoreOverrideCursor()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if self.command is not None:
            self.command(self)
        super().mousePressEvent(event)
    
    def __getCanvasPos(self, position):
        tilePosition = decimal_to_osm(*position, round(self.mapView.zoom))

        widgetTileWidth = self.mapView.lowerRightTilePos[0] - self.mapView.upperLeftTilePos[0]
        widgetTileHeight = self.mapView.lowerRightTilePos[1] - self.mapView.upperLeftTilePos[1]

        canvasPosX = ((tilePosition[0] - self.mapView.upperLeftTilePos[0]) / widgetTileWidth) * self.mapView._width
        canvasPosY = ((tilePosition[1] - self.mapView.upperLeftTilePos[1]) / widgetTileHeight) * self.mapView._height

        return canvasPosX, canvasPosY
    
    def draw(self):
        if self.mapView:
            canvasPosX, canvasPosY = self.__getCanvasPos(self.position)

            if 0 - 50 < canvasPosX < self.mapView._width + 50 and 0 < canvasPosY < self.mapView._height + 70:
                # draw icon image for marker
                self.setPos(canvasPosX, canvasPosY)
                self.setVisible(self.markerVisible)
            else:
                self.setVisible(False)



class Buttons:
    def __init__(self,
                 zoomIn: bool = True,
                 zoomOut: bool = True,
                 layers: bool = True,
                 home: bool = True):
        self.mapView: MapView = None
        
        self.zoomInFlag = zoomIn
        self.zoomOutFlag = zoomOut
        self.layersFlag = layers
        self.homeFlag = home
         
        # buttons
        self.buttonZoomIn = None
        self.buttonZoomOut = None
        self.buttonLayers = None
        self.buttonHome = None
    
    def addButtons(self):
        if self.zoomInFlag is True:
            self.buttonZoomIn = QPushButton("+", self.mapView)
            self.buttonZoomIn.setGeometry(20, 20, 29, 29)
            self.buttonZoomIn.clicked.connect(self.zoomIn)
            
        if self.zoomOutFlag is True:    
            self.buttonZoomOut = QPushButton("-", self.mapView)
            self.buttonZoomOut.setGeometry(20, 60, 29, 29)
            self.buttonZoomOut.clicked.connect(self.zoomOut)
            
        if self.layersFlag is True:
            currentPath = os.path.dirname(os.path.abspath(__file__))
            imagePath = resource_path('../images/icon-layers.png')
            # print(imagePath )
            self.icon = QImage(imagePath)
            buttonLayers_icon = QPixmap.fromImage(self.icon)
            self.buttonLayers = QPushButton("", self.mapView)

            self.buttonLayers.setGeometry(self.mapView.size().width() - 55, 20, 35, 35)
            self.buttonLayers.setIcon(QIcon(buttonLayers_icon))
            self.buttonLayers.setIconSize(QSize(30, 30))
            self.buttonLayers.clicked.connect(self.change_layers)
            
        if self.homeFlag is True:
            currentPath = os.path.dirname(os.path.abspath(__file__))
            imagePath = resource_path('../images/icon-home.png')
            buttonImage_icon = QImage(imagePath)
            buttonImage_pixmap = QPixmap.fromImage(buttonImage_icon)
            self.buttonHome = QPushButton("", self.mapView)

            buttonWidth, buttonHeight = 35, 35
            self.buttonHome.setGeometry(self.mapView.size().width() - buttonWidth - 10, 
                                         self.mapView.size().height() - buttonHeight - 10,
                                         buttonWidth, buttonHeight)
            self.buttonHome.setIcon(QIcon(buttonImage_pixmap))
            self.buttonHome.setIconSize(QSize(30, 30))
            self.buttonHome.clicked.connect(self.mapView.setPosition)
    
    def zoomIn(self):
        self.mapView.setZoom(self.mapView.zoom + 1)
    
    def zoomOut(self):
        self.mapView.setZoom(self.mapView.zoom - 1)
    
    def change_layers(self):
        # Создаем меню для выбора слоев
        menu = QMenu(self.mapView)
        for name in self.mapView.mapLayers:
            menu.addAction(name.get('nameMap'), self.select_layer)
        
        global_pos = self.buttonLayers.mapToGlobal(self.buttonLayers.rect().bottomRight())
        menu.exec_(QPoint(global_pos.x() - menu.sizeHint().width(), global_pos.y()))

    def select_layer(self):
        for name in self.mapView.mapLayers:
            if name.get('nameMap') == self.mapView.sender().text():
                self.mapView.setTileServer(name.get('nameMap')) 
                
            

class Path(QGraphicsLineItem):
    def __init__(self,
                 startPosition: tuple,
                 positionList: list[tuple],
                 color: str = "#fefe22",
                 command: Callable = None,
                 namePath: str = None,
                 widthLine: int = 9):
        super().__init__()
        self.mapView: MapView = None
        self.pathColor = color
        self.command = command
        self.widthLine = widthLine
        self.namePath = namePath
        
        self.pathVisible = True
        
        self.__positionList = []
        self.__positionList.append((startPosition, None))
        for item in positionList:
            if isinstance(item[0], tuple):
                self.__positionList.append((item[0], item[1]))
            else:    
                self.__positionList.append((item, self.pathColor))
        
        self.__segments = 0
        self.__canvasLinePositions = []
        self.__canvasLine: list[tuple[QGraphicsLineItem, QColor]] = []
        self.__lastUpperLeftTilePos = None
        self.__lastPositionListLength = len(self.__positionList)
        
        self.setZValue(1)


    # User methods
    def getSegments(self) -> int:
        """Returns the number of path segments."""
        return self.__segments
    
    def updateColorLine(self, segment: int, color: str):
        """Changing the color of a path segment.
 
        :param segment:
        :type segment: Segment number from 0
        :param color:
        :type color: HEX color code
        """
        if segment >= self.__segments:
            segment = self.__segments - 1
        elif segment < 0:
            segment = 0
        item = list(self.__canvasLine[segment])
        item[1] = QColor(color)
        self.__canvasLine[segment] = tuple(item)
        self.draw()
        
    def delete(self):
        """Deleting a path. """
        if self.mapView:
            self.mapView.elementsList.remove(self)
            self.mapView.mapScene.removeItem(self)

    def setPositionList(self, startPosition: tuple, positionList: list[tuple]):
        """A new list of points and  line colors for the path.
 
        :param startPosition: The starting point
        :type startPosition: ( deg x, deg y )
        :param positionList: The following points and line colors (HEX color code), color optional
        :type positionList: ((( deg x, deg y ), "#fefe22" ), ( deg x, deg y ), ... )
        """
        self.__positionList = []
        self.__positionList.append((startPosition, None))
        for item in positionList:
            if isinstance(item[0], tuple):
                self.__positionList.append((item[0], item[1]))
            else:    
                self.__positionList.append((item[0], self.pathColor))
        
        self.draw()

    def addPosition(self, position: tuple, color: str = "#fefe22", index=-1):
        """Adding a new point to the path list.
 
        :param position:
        :type position: ( deg x, deg y )
        :param color: optional, default = "#fefe22"
        :type color: HEX color code
        :param index: optional, default = -1
        :type index: The index of the point in the path
        """
        if index == -1:
            self.__positionList.append((position, color))
        else:
            self.__positionList.insert((index, (position, color)))
        self.draw()

    def removePosition(self, position: tuple):
        """Remove a point to the path list.
 
        :param position:
        :type position: ( deg x, deg y )
        """
        self.__positionList.remove(position)
        self.draw()

    def setVisiblePath(self, visible: bool):
        """Path visibility. """
        self.pathVisible = visible
        self.draw()
    
    def __getCanvasPos(self, position):
        
        tilePosition = decimal_to_osm(*position, round(self.mapView.zoom))

        widgetTileWidth = self.mapView.lowerRightTilePos[0] - self.mapView.upperLeftTilePos[0]
        widgetTileHeight = self.mapView.lowerRightTilePos[1] - self.mapView.upperLeftTilePos[1]

        canvasPosX = ((tilePosition[0] - self.mapView.upperLeftTilePos[0]) / widgetTileWidth) * self.mapView._width
        canvasPosY = ((tilePosition[1] - self.mapView.upperLeftTilePos[1]) / widgetTileHeight) * self.mapView._height

        return canvasPosX, canvasPosY

    
    def draw(self):
        if self.mapView:
            
            new_line_length = self.__lastPositionListLength != len(self.__positionList)
            self.__lastPositionListLength = len(self.__positionList)
            
            if self.pathVisible == True:
                self.setVisible(True)

                self.__canvasLinePositions = []
                for position in self.__positionList:
                    canvas_position = self.__getCanvasPos(position[0])
                    self.__canvasLinePositions.append(canvas_position[0])
                    self.__canvasLinePositions.append(canvas_position[1])

                segments = int(len(self.__canvasLinePositions) / 2 - 1)
                if self.__segments != segments:
                    index = 0
                    for i in range(0, segments - self.__segments):
                        self.__segments += 1
                        lineItem = QGraphicsLineItem(self.__canvasLinePositions[index], self.__canvasLinePositions[index + 1],
                                                     self.__canvasLinePositions[index + 2], self.__canvasLinePositions[index + 3], self)
                        index +=2
                        self.__canvasLine.append((lineItem, QColor(self.__positionList[int(index/2)][1])))
                        line_pen = QPen(self.__canvasLine[-1][1])
                        line_pen.setWidth(self.widthLine)
                        lineItem.setPen(line_pen)
                else:
                    index = 0
                    for idx, item in enumerate(self.__canvasLine):
                        item[0].setLine(self.__canvasLinePositions[index], self.__canvasLinePositions[index + 1],
                                     self.__canvasLinePositions[index + 2], self.__canvasLinePositions[index + 3])
                        line_pen = QPen(item[1])
                        line_pen.setWidth(self.widthLine)
                        item[0].setPen(line_pen)
                        index+=2

                self.__lastUpperLeftTilePos = self.mapView.upperLeftTilePos
                
            else:
                self.setVisible(False)
        
            
    # Events
    def hoverEnterEvent(self, event):
        if self.command != None and self.pathVisible == True:
            QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.command != None and self.pathVisible == True:
            QApplication.restoreOverrideCursor()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if self.command != None:
            self.command(self)
        super().mousePressEvent(event)
    
    

class SimplePath(QGraphicsPathItem):
    def __init__(self, startPoint: tuple[float, float]):
        super().__init__()
        self.mapView: MapView = None
        self.startPoint = startPoint
        self.__positionList = []
        self.__positionList.append(startPoint)
        self.flag = True
        self.lastZoom = 0

    def delete(self):
        """Deleting a path. """
        if self.mapView:
            self.__path.clear()
            self.mapView.elementsList.remove(self)
            self.mapView.mapScene.removeItem(self)

    def addPosition(self, point: tuple[float, float]):
        self.__positionList.append(point)          
        canvasPosX, canvasPosY = self.__getCanvasPos(point)
        new_pos = QPointF(canvasPosX, canvasPosY)
        self.__path.lineTo(new_pos)
        self.setPath(self.__path)
        self.draw()
        
    def __getCanvasPos(self, position):
        
        tilePosition = decimal_to_osm(*position, round(self.mapView.zoom))

        widgetTileWidth = self.mapView.lowerRightTilePos[0] - self.mapView.upperLeftTilePos[0]
        widgetTileHeight = self.mapView.lowerRightTilePos[1] - self.mapView.upperLeftTilePos[1]

        canvasPosX = ((tilePosition[0] - self.mapView.upperLeftTilePos[0]) / widgetTileWidth) * self.mapView._width
        canvasPosY = ((tilePosition[1] - self.mapView.upperLeftTilePos[1]) / widgetTileHeight) * self.mapView._height

        return canvasPosX, canvasPosY
        
    def draw(self):
        if self.flag:
            self.flag = False
            self.lastZoom = self.mapView.zoom
            # Создаем путь для ломаной линии
            self.__path = QPainterPath()

            # Устанавливаем цвет и ширину линии
            pen = QPen(Qt.red, 4)
            self.setPen(pen)

            # Устанавливаем начальный путь
            self.setPath(self.__path)
            
            # text_item = QGraphicsTextItem("Hello, Path!", self)
            # text_item.setFont(QFont("Arial", 16))
            # text_item.setDefaultTextColor(QColor(255, 0, 0))  # Красный цвет текста
        if self.lastZoom != self.mapView.zoom:
            self.__path = QPainterPath()
            for i in range(len(self.__positionList)):
                canvasPosX, canvasPosY = self.__getCanvasPos(self.__positionList[i])
                if i == 0:
                    self.__path.moveTo(canvasPosX, canvasPosY)  # Начинаем новый путь 
                else:
                    self.__path.lineTo(canvasPosX, canvasPosY)  # Добавляем линию к новому пути
            self.setPath(self.__path)
        # else:
        #     canvasPosX, canvasPosY = self.__getCanvasPos(self.__positionList[0])
        #     self.setPos(canvasPosX, canvasPosY)
        
        self.lastZoom = self.mapView.zoom
        
        # canvasPosX, canvasPosY = self.__getCanvasPos(self.startPoint)
             


        
