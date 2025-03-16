import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsLineItem, QLineEdit, QPushButton
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem
from PyQt6.QtGui import QPixmap, QDrag, QMouseEvent, QPen, QPolygonF
from PyQt6.QtCore import Qt, QMimeData, QPointF

class DraggableLabel(QLabel):
    """ A label that can be dragged onto the canvas. """
    def __init__(self, image_path, component_name):
        super().__init__()
        self.setPixmap(QPixmap(image_path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
        self.component_name = component_name

    def mousePressEvent(self, event: QMouseEvent):
        """ Start dragging when the mouse is pressed. """
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.component_name)
            drag.setMimeData(mime_data)
            drag.setHotSpot(event.pos())  # Set drag hotspot to current position.
            drag.setPixmap(self.pixmap())  # Set the pixmap of the drag.
            result = drag.exec(Qt.DropAction.CopyAction)  # Use CopyAction instead of MoveAction.

class PEGraphicsView(QGraphicsView):
    """ Custom QGraphicsView to accept drops and handle connections. """
    def __init__(self, scene, component_images):
        super().__init__(scene)
        self.setAcceptDrops(True)
        self.component_images = component_images
        self.placed_components = {
            "inputs": [],
            "outputs": [],
            "registers": [],
            "muxes": [],
            "fus": []
        }
        self.connections = []  # Store connections
        self.selected_component_1 = None
        self.selected_component_2 = None
        self.scaling = {"input": (50, 50), "output": (50, 50), "Register": (90, 30), "MUX": (100, 25), "FU": (100, 50)}

    def dragEnterEvent(self, event):
        """ Allow drag if it's a known component. """
        mime_data = event.mimeData()
        if mime_data.hasText():  # Check if text data is present
            component_name = mime_data.text()
            if component_name in self.component_images:
                event.setDropAction(Qt.DropAction.CopyAction)  # Force the copy action
                event.acceptProposedAction()  # Accept the drag

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        """ Drop component onto the canvas without connecting it immediately. """
        component_name = event.mimeData().text()
        if component_name in self.component_images:
            scene_pos = self.mapToScene(event.position().toPoint())
            
            if component_name == "input":
                unique_name = f"in{len(self.placed_components['inputs'])}"
                self.placed_components["inputs"].append(unique_name)
            elif component_name == "output":
                unique_name = f"out{len(self.placed_components['outputs'])}"
                self.placed_components["outputs"].append(unique_name)
            elif component_name == "Register":
                unique_name = f"r{len(self.placed_components['registers'])}"
                self.placed_components["registers"].append(unique_name)
            elif component_name == "MUX":
                unique_name = f"m{len(self.placed_components['muxes'])}"
                self.placed_components["muxes"].append(unique_name)
            elif component_name == "FU":
                unique_name = f"fu{len(self.placed_components['fus'])}"
                self.placed_components["fus"].append(unique_name)

            # Create and place the component on the canvas
            x, y = self.scaling[component_name]
            item = QGraphicsPixmapItem(QPixmap(self.component_images[component_name]).scaled(x, y))
            item.setPos(scene_pos)
            item.setData(0, unique_name)  # Store the component's unique name
            self.scene().addItem(item)
            
            event.accept()  # Explicitly accept the drop event
            
            # After the component is placed, do not connect yet, reset selections
            self.selected_component_1 = None
            self.selected_component_2 = None

    def create_connection(self, component_1, component_2):
        import math
        """ Create a connection line with an arrowhead between two components. """
        start_point = component_1.scenePos() + QPointF(25, 25)  # Center of first component
        end_point = component_2.scenePos() + QPointF(10, 10)  # Center of second component

        # Draw the connection line
        line = QGraphicsLineItem(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(2)  # Make the line thicker
        line.setPen(pen)
        self.scene().addItem(line)

        # Compute arrowhead points using trigonometry
        arrow_size = 10
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        angle = math.atan2(dy, dx)  # Compute angle of the line

        # Compute arrowhead base points using rotation
        arrow_p1 = QPointF(
            end_point.x() - arrow_size * math.cos(angle - math.pi / 6),
            end_point.y() - arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = QPointF(
            end_point.x() - arrow_size * math.cos(angle + math.pi / 6),
            end_point.y() - arrow_size * math.sin(angle + math.pi / 6)
        )

        # Create arrowhead polygon
        arrow_head = QPolygonF([end_point, arrow_p1, arrow_p2])
        arrow_item = QGraphicsPolygonItem(arrow_head)
        arrow_item.setBrush(Qt.GlobalColor.black)  # Fill arrowhead
        self.scene().addItem(arrow_item)

        print(f"Connection created from {component_1.data(0)} to {component_2.data(0)}")
        self.connections.append([component_1.data(0), component_2.data(0)])
        
    def mousePressEvent(self, event):
        """ Handle mouse press for panning and selecting components for connections. """
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)  # Enable panning
            self.drag_start_position = event.pos()  # Store the starting position for panning
        elif event.button() == Qt.MouseButton.LeftButton:
            # Handle component selection for connections
            item = self.itemAt(event.pos())
            if item and item.data(0) is not None:
                if self.selected_component_1 is None:
                    self.selected_component_1 = item
                    print(f"Selected first component: {item.data(0)}")
                elif self.selected_component_2 is None and item != self.selected_component_1:
                    self.selected_component_2 = item
                    print(f"Selected second component: {item.data(0)}")
                    self.create_connection(self.selected_component_1, self.selected_component_2)
                    # Reset selection after creating the connection
                    self.selected_component_1 = None
                    self.selected_component_2 = None
        super().mousePressEvent(event)  # Ensure base class functionality is called

    def mouseReleaseEvent(self, event):
        """ Handle mouse release to stop panning or finalize connection selection. """
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)  # Disable panning after middle button release
        super().mouseReleaseEvent(event)  # Ensure base class functionality is called

    def wheelEvent(self, event):
        """ Handle zooming with the mouse wheel. """
        zoom_factor = 1.15  # Define the zoom factor

        # If the wheel is scrolled upwards (zoom in)
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        # If the wheel is scrolled downwards (zoom out)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def get_placed_components(self):
        """ Return the dictionary of placed components. """
        return self.placed_components

    def get_connections(self):
        """ Return the list of connections. """
        return self.connections


class PEEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PE Creator")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Name box and export button
        name_layout = QHBoxLayout()
        self.name_box = QLineEdit(self)
        self.name_box.setPlaceholderText("Enter name (default: circuit)")
        name_layout.addWidget(QLabel("Circuit Name:"))
        name_layout.addWidget(self.name_box)

        self.export_button = QPushButton("Export", self)
        self.export_button.clicked.connect(self.generate_json)
        name_layout.addWidget(self.export_button)

        main_layout.addLayout(name_layout)

        # Components section
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Components:"))

        # Dictionary of components
        self.components = {
            "MUX": "img/mux.png",
            "FU": "img/fu.png",
            "Register": "img/reg.png",
            "input": "img/input.png",
            "output": "img/output.png"
        }

        for name, image in self.components.items():
            btn = DraggableLabel(image, name)
            toolbar.addWidget(btn)

        main_layout.addLayout(toolbar)

        # Graphics View (Canvas)
        self.scene = QGraphicsScene()
        self.view = PEGraphicsView(self.scene, self.components)
        main_layout.addWidget(self.view)

        # Set main widget
        self.setCentralWidget(main_widget)

    def generate_json(self):
        circuit_name = self.name_box.text() or "circuit"  # Default to "circuit" if no name is provided
        print(f"Generating json for module: \"{circuit_name}\"")
        """ Generate JSON from placed components and connections. """
        components = self.view.get_placed_components()
        connections = self.view.get_connections()

        # Format connections as {"from": "component1", "to": "component2"}
        formatted_connections = [
            {"from": start_name, "to": end_name}
            for start_name, end_name in connections
        ]

        pe_json = {
            "PE": {
                "name": circuit_name,
                "inputs": components["inputs"],
                "outputs": components["outputs"],
                "registers": components["registers"],
                "muxes": components["muxes"],
                "fus": [{"name": fu_name, "ops": ["ADD", "SUB", "AND", "OR"]} for fu_name in components["fus"]],
                "connections": formatted_connections  # Add the formatted connections here
            }
        }

        # Print the generated JSON (or save it to a file as needed)
        import json
        print(json.dumps(pe_json, indent=4))

        with open(circuit_name + '.json', 'w') as json_file:
            json.dump(pe_json, json_file, indent=4)

    def closeEvent(self, event):
        print("closing window...")
        circuit_name = self.name_box.text() or "circuit"
        with open('apex.log', 'w') as log_file:
            log_file.write(circuit_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PEEditor()
    window.show()
    sys.exit(app.exec())
