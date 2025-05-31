from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow
import sys
import os

from PyQtMapView import MapView, Marker, Path,  SimplePath

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui import MainWindow
    
class interMap():
    def __init__(self, gui: "MainWindow", lat, lon, zoom, useDataBaseOnly):
        super().__init__()
        self.gui = gui
        # Map init
        self.corner_radius: int = 0
        self.bg_color: str = None
        
        self.max_zoom = 19
        
        self.database_path = "dataBase"

        self.marker_list = {}  
        self.path_list = {}

        # self.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga")
        self.map = MapView(useDatabaseOnly = useDataBaseOnly, dataPath=self.database_path, homeCoord=(lat, lon))
        self.map.setZoom(zoom)
        

    # Выбор текущего места на карте по координатам
    def choosePlace(self, coords: tuple, zoom = None):
        if zoom is None:
            zoom = self.map.getZoom()
        self.map.setPosition(coords)  # Установка позиции на метке
        self.map.setZoom(zoom)  # Установка приближения на метку



    # Установка маркера на карте
    def setMarker(self, lat, lon, source, text='', visible=True, marker_color_outside = "#FF0000"):
        marker = Marker((lat, lon),text, markerColorOutside=marker_color_outside, textColor="#FF0000")
        self.map.addElement(marker)
        marker.setVisibleMarker(visible)
        
        # marker.change_icon(plane_image)
        self.marker_list[source] = marker  # Добавление маркера в маркер лист

    # Удаление маркера с карты
    def delMarker(self, source):
        marker = self.marker_list.get(source)
        if marker:
            self.marker_list.pop(source)
            marker.delete()
        

    # Обновление маркеров
    def updateMarkers(self, data):
        for source in data:
            if data[source]['text'] == "":
                data[source]['text'] = f"{source}"
            if self.marker_list.get(source)==None:
                if not data[source]['lat'] is None and not data[source]['lon'] is None:
                    self.setMarker(data[source]['lat'], data[source]['lon'], source, data[source]['text'],data[source]['visible'], data[source]['color'])
            else:
                if not data[source]['lat'] is None and not data[source]['lon'] is None:
                    self.marker_list[source].setVisibleMarker(data[source]['visible'])
                    self.marker_list[source].setPosition(data[source]['lat'], data[source]['lon'])
                    self.marker_list[source].setText(data[source]['text'], textColor="#FF0000")
    

    def update_trace(self, source: str, data: dict):
        if not data['traceFlag'] or not data['visible']:
            self.delPath(source)
            return
        
        path = self.path_list.get(source)
        if path is None:
            # print(data)
            coords = self.gui.logger.get_user_locations(self.gui.session_path, source)
            if coords is None:
                if data.get('lat') is None or data.get('lon') is None:
                    return
                coords = [(data['lat'], data['lon']), (data['lat'], data['lon'])]
            elif len(coords) == 1:
                if data.get('lat') is None or data.get('lon') is None:
                    return
                coords.append((data['lat'], data['lon']))
            path = Path(coords[0], coords, widthLine=2, color = data["color"])
                
            self.map.addElement(path)
            self.path_list[source] = path
        else:
            if data.get('lat') is None or data.get('lon') is None:
                    return
            coord = (data['lat'], data['lon'])
            path.addPosition(coord)       
                
    def delPath(self, source: str):
        path = self.path_list.get(source)
        if not path is None:
            self.path_list.pop(source)
            path.delete()

    def deleteAbonent(self, source: str):
        self.delPath(source)
        self.delMarker(source)
        
    def clearMap(self):
        sources = list(self.marker_list.keys())
        for source in sources:
            self.deleteAbonent(source)