import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsLineItem, QLineEdit, QPushButton
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem
from PyQt6.QtGui import QPixmap, QDrag, QMouseEvent, QPen, QPolygonF, QPainterPath
from PyQt6.QtCore import Qt, QMimeData, QPointF

class DraggableLabel(QLabel):
    """ A label that can be dragged onto the canvas. """
    def __init__(self, image_path, component_name, scaling=(60, 60)):
        super().__init__()
        self.setPixmap(QPixmap(image_path).scaled(scaling[0], scaling[1], Qt.AspectRatioMode.KeepAspectRatio))
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
            drag.exec(Qt.DropAction.CopyAction)  # Use CopyAction instead of MoveAction.

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

    def get_component_center(self, component):
        """Calculate the center point of a component."""
        bounding_rect = component.boundingRect()
        center_x = component.scenePos().x() + bounding_rect.width() / 2
        center_y = component.scenePos().y() + bounding_rect.height() / 2
        return QPointF(center_x, center_y)
    
    def create_connection(self, component_1, component_2):
        """Create a right-angled connection with an arrowhead between two components."""
        start_center = component_1.scenePos() + QPointF(component_1.boundingRect().width() / 2,
                                                        component_1.boundingRect().height() / 2)
        end_center = component_2.scenePos() + QPointF(component_2.boundingRect().width() / 2,
                                                    component_2.boundingRect().height() / 2)

        # Create a path from start to end with horizontal and vertical segments
        path = QPainterPath(start_center)
        mid_point = QPointF(end_center.x(), start_center.y())
        path.lineTo(mid_point)
        path.lineTo(end_center)

        # Draw the path
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(2)
        line_item = self.scene().addPath(path, pen)

        # Add arrowhead
        self.add_arrowhead(path)

        print(f"Connection created from {component_1.data(0)} to {component_2.data(0)}")
        self.connections.append([component_1.data(0), component_2.data(0)])

    def add_arrowhead(self, path):
        import math
        end_point = path.currentPosition()  # QPointF, use methods x() and y()
        element_count = path.elementCount()
        if element_count < 2:
            return  # Not enough points to determine direction
        previous_point = path.elementAt(element_count - 2)  # QPainterPath.Element with attributes x and y

        # Correct: use end_point.y() - previous_point.y (without parentheses on previous_point.y)
        angle = math.atan2(end_point.y() - previous_point.y, end_point.x() - previous_point.x)

        arrow_size = 10
        arrow_p1 = QPointF(
            end_point.x() - arrow_size * math.cos(angle - math.pi / 6),
            end_point.y() - arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = QPointF(
            end_point.x() - arrow_size * math.cos(angle + math.pi / 6),
            end_point.y() - arrow_size * math.sin(angle + math.pi / 6)
        )

        arrow_head = QPolygonF([end_point, arrow_p1, arrow_p2])
        arrow_item = QGraphicsPolygonItem(arrow_head)
        arrow_item.setBrush(Qt.GlobalColor.black)
        self.scene().addItem(arrow_item)

        
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
        self.setGeometry(100, 100, 1000, 800)

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

        # Dictionary of components (images)
        self.components = {
            "MUX": "img/mux.png",
            "FU": "img/fu.png",
            "Register": "img/reg.png",
            "input": "img/input.png",
            "output": "img/output.png"
        }

        # Define toolbar scalings; if you want every component to appear the same, use the same value,
        # otherwise adjust manually.
        toolbar_scaling = {
            "MUX": (90, 90),
            "FU": (70, 70),
            "Register": (90, 90),
            "input": (50, 50),
            "output": (50, 50)
        }

        for name, image in self.components.items():
            # Create a widget to hold both the image and its label
            comp_widget = QWidget()
            comp_layout = QVBoxLayout(comp_widget)
            comp_layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margins if needed

            # Use the scaling for this component (or a default if not provided)
            scaling = toolbar_scaling.get(name, (60, 60))
            btn = DraggableLabel(image, name, scaling=scaling)
            comp_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

            # Create and add the label
            text_label = QLabel(name)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            comp_layout.addWidget(text_label)

            # Add the composite widget to the toolbar
            toolbar.addWidget(comp_widget)

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
